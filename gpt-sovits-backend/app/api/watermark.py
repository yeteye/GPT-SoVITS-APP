# ./gpt-sovits-backend/app/api/watermark.py
from flask import (
    Blueprint,
    request,
    jsonify,
    current_app,
    send_file,
    after_this_request,
)
from werkzeug.utils import secure_filename
import tempfile
import os

from app.extensions import db
from app.models.watermark import Watermark, WatermarkVerificationLog
from app.auth.decorators import auth_required, admin_required, rate_limit, log_action
from app.utils.validators import validate_audio_file, validate_pagination
from app.utils.helpers import (
    create_response,
    paginate_query,
    get_client_ip,
    get_user_agent,
)
from app.utils.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    AudioProcessingError,
    ServiceUnavailableError,
)
from app.services.watermark_service import WatermarkService

watermark_bp = Blueprint("watermark", __name__)


@watermark_bp.route("/embed", methods=["POST"])
@auth_required
@rate_limit(requests_per_minute=10)
@log_action("embed_watermark", "watermark")
def embed_watermark():
    """手动嵌入水印API"""
    try:
        user = request.current_user

        # 检查文件上传
        if "audio_file" not in request.files:
            raise ValidationError("No audio file provided", "audio_file")

        file = request.files["audio_file"]
        validate_audio_file(file)

        # 获取可选参数
        code_length = request.form.get("code_length", 16, type=int)
        if code_length not in [8, 16, 32]:
            raise ValidationError("Code length must be 8, 16, or 32", "code_length")

        description = request.form.get("description", "").strip()
        model_id = request.form.get("model_id")

        # 保存上传的文件到临时位置
        filename = secure_filename(file.filename)
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_input_path = temp_input.name
        temp_input.close()
        file.save(temp_input_path)

        try:
            # 验证音频文件
            import wave

            with wave.open(temp_input_path, "rb") as wav:
                # 简单验证WAV文件头
                pass
        except wave.Error:
            os.unlink(temp_input_path)
            raise ValidationError("Invalid WAV file", "audio_file")

        # 初始化水印服务
        watermark_service = WatermarkService()

        # 获取或创建水印码
        watermark_code = watermark_service.get_or_create_user_watermark(
            user_id=user.id, username=user.username, model_id=model_id
        )

        # 自动清理临时文件
        @after_this_request
        def cleanup_files(response):
            try:
                if os.path.exists(temp_input_path):
                    os.unlink(temp_input_path)
            except Exception as e:
                current_app.logger.warning(f"Failed to cleanup temp file: {e}")
            return response

        # 嵌入水印
        watermarked_path = watermark_service.embed_watermark_to_audio(
            original_path=temp_input_path,
            watermark_code=watermark_code,
            user_id=user.id,
            output_dir=os.path.dirname(temp_input_path),
        )

        # 返回带水印的文件
        return send_file(
            watermarked_path,
            as_attachment=True,
            download_name=f"watermarked_{filename}",
            mimetype="audio/wav",
        )

    except (ValidationError, AudioProcessingError) as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Embed watermark error: {e}")
        return jsonify(create_response(False, "Watermark embedding failed")), 500


@watermark_bp.route("/verify", methods=["POST"])
@rate_limit(requests_per_minute=30)
def verify_watermark():
    """验证水印API"""
    try:
        # 检查文件上传
        if "audio_file" not in request.files:
            raise ValidationError("No audio file provided", "audio_file")

        file = request.files["audio_file"]
        validate_audio_file(file)

        # 获取客户端信息
        ip_address = get_client_ip()
        user_agent = get_user_agent()

        # 保存上传文件到临时位置
        filename = secure_filename(file.filename)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_path = temp_file.name
        temp_file.close()
        file.save(temp_path)

        try:
            # 验证音频文件
            import wave

            with wave.open(temp_path, "rb") as wav:
                pass
        except wave.Error:
            os.unlink(temp_path)
            raise ValidationError("Invalid WAV file", "audio_file")

        # 自动清理临时文件
        @after_this_request
        def cleanup_verify(response):
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception as e:
                current_app.logger.warning(f"Failed to cleanup temp file: {e}")
            return response

        # 初始化水印服务
        watermark_service = WatermarkService()

        # 提取并验证水印
        result = watermark_service.extract_and_verify_watermark(
            audio_path=temp_path,
            filename=filename,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if result["success"]:
            return jsonify(
                create_response(
                    success=True,
                    message=result.get("message", "Watermark verification completed"),
                    data=result,
                )
            )
        else:
            return (
                jsonify(
                    create_response(
                        success=False,
                        message=result.get("message", "No watermark detected"),
                        data=result,
                    )
                ),
                200,
            )  # 返回200，但success=False

    except (ValidationError, AudioProcessingError) as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Verify watermark error: {e}")
        return jsonify(create_response(False, "Watermark verification failed")), 500


@watermark_bp.route("/my-watermarks", methods=["GET"])
@auth_required
@rate_limit(requests_per_minute=30)
def get_my_watermarks():
    """获取我的水印列表"""
    try:
        user = request.current_user

        # 分页参数
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        model_id = request.args.get("model_id")

        page, per_page = validate_pagination(page, per_page)

        # 构建查询
        query = Watermark.query.filter_by(user_id=user.id, is_active=True)

        if model_id:
            query = query.filter_by(model_id=model_id)

        # 按创建时间倒序
        query = query.order_by(Watermark.created_at.desc())

        # 分页
        pagination = paginate_query(query, page, per_page)

        return jsonify(
            create_response(
                success=True,
                message="Watermarks retrieved successfully",
                data={
                    "watermarks": [
                        watermark.to_dict() for watermark in pagination["items"]
                    ],
                    "pagination": {
                        "page": pagination["page"],
                        "per_page": pagination["per_page"],
                        "total": pagination["total"],
                        "pages": pagination["pages"],
                        "has_prev": pagination["has_prev"],
                        "has_next": pagination["has_next"],
                    },
                },
            )
        )

    except ValidationError as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Get my watermarks error: {e}")
        return jsonify(create_response(False, "Failed to retrieve watermarks")), 500


@watermark_bp.route("/my-watermarks/<watermark_id>", methods=["GET"])
@auth_required
@rate_limit(requests_per_minute=60)
def get_watermark_detail(watermark_id):
    """获取水印详情"""
    try:
        user = request.current_user

        watermark = Watermark.query.filter_by(
            id=watermark_id, user_id=user.id, is_active=True
        ).first()

        if not watermark:
            raise ResourceNotFoundError("Watermark")

        # 获取验证日志
        verification_logs = (
            WatermarkVerificationLog.query.filter_by(
                watermark_code=watermark.watermark_code
            )
            .order_by(WatermarkVerificationLog.verified_at.desc())
            .limit(10)
            .all()
        )

        return jsonify(
            create_response(
                success=True,
                message="Watermark details retrieved successfully",
                data={
                    "watermark": watermark.to_dict(),
                    "recent_verifications": [
                        log.to_dict() for log in verification_logs
                    ],
                },
            )
        )

    except ResourceNotFoundError as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Get watermark detail error: {e}")
        return (
            jsonify(create_response(False, "Failed to retrieve watermark details")),
            500,
        )


@watermark_bp.route("/my-watermarks/<watermark_id>", methods=["PUT"])
@auth_required
@rate_limit(requests_per_minute=10)
@log_action("update_watermark", "watermark")
def update_watermark(watermark_id):
    """更新水印信息"""
    try:
        user = request.current_user
        data = request.get_json()

        if not data:
            raise ValidationError("Request body is required")

        watermark = Watermark.query.filter_by(
            id=watermark_id, user_id=user.id, is_active=True
        ).first()

        if not watermark:
            raise ResourceNotFoundError("Watermark")

        # 可更新的字段
        if "description" in data:
            watermark.description = data["description"].strip()

        db.session.commit()

        return jsonify(
            create_response(
                success=True,
                message="Watermark updated successfully",
                data={"watermark": watermark.to_dict()},
            )
        )

    except (ValidationError, ResourceNotFoundError) as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Update watermark error: {e}")
        return jsonify(create_response(False, "Failed to update watermark")), 500


@watermark_bp.route("/my-watermarks/<watermark_id>", methods=["DELETE"])
@auth_required
@rate_limit(requests_per_minute=5)
@log_action("deactivate_watermark", "watermark")
def deactivate_watermark(watermark_id):
    """停用水印（软删除）"""
    try:
        user = request.current_user

        watermark = Watermark.query.filter_by(
            id=watermark_id, user_id=user.id, is_active=True
        ).first()

        if not watermark:
            raise ResourceNotFoundError("Watermark")

        # 软删除
        watermark.is_active = False
        db.session.commit()

        return jsonify(
            create_response(success=True, message="Watermark deactivated successfully")
        )

    except ResourceNotFoundError as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Deactivate watermark error: {e}")
        return jsonify(create_response(False, "Failed to deactivate watermark")), 500


@watermark_bp.route("/statistics", methods=["GET"])
@auth_required
@rate_limit(requests_per_minute=30)
def get_watermark_statistics():
    """获取用户水印统计"""
    try:
        user = request.current_user

        watermark_service = WatermarkService()
        stats = watermark_service.get_watermark_statistics(user_id=user.id)

        return jsonify(
            create_response(
                success=True,
                message="Watermark statistics retrieved successfully",
                data=stats,
            )
        )

    except Exception as e:
        current_app.logger.error(f"Get watermark statistics error: {e}")
        return jsonify(create_response(False, "Failed to retrieve statistics")), 500


@watermark_bp.route("/verification-logs", methods=["GET"])
@auth_required
@rate_limit(requests_per_minute=30)
def get_verification_logs():
    """获取用户的水印验证日志"""
    try:
        user = request.current_user

        # 分页参数
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)

        page, per_page = validate_pagination(page, per_page)

        # 获取用户的所有水印码
        watermark_codes = [
            w.watermark_code
            for w in Watermark.query.filter_by(user_id=user.id, is_active=True).all()
        ]

        if not watermark_codes:
            return jsonify(
                create_response(
                    success=True,
                    message="No verification logs found",
                    data={
                        "logs": [],
                        "pagination": {
                            "page": 1,
                            "per_page": per_page,
                            "total": 0,
                            "pages": 0,
                            "has_prev": False,
                            "has_next": False,
                        },
                    },
                )
            )

        # 构建查询
        query = WatermarkVerificationLog.query.filter(
            WatermarkVerificationLog.watermark_code.in_(watermark_codes)
        ).order_by(WatermarkVerificationLog.verified_at.desc())

        # 分页
        pagination = paginate_query(query, page, per_page)

        return jsonify(
            create_response(
                success=True,
                message="Verification logs retrieved successfully",
                data={
                    "logs": [log.to_dict() for log in pagination["items"]],
                    "pagination": {
                        "page": pagination["page"],
                        "per_page": pagination["per_page"],
                        "total": pagination["total"],
                        "pages": pagination["pages"],
                        "has_prev": pagination["has_prev"],
                        "has_next": pagination["has_next"],
                    },
                },
            )
        )

    except ValidationError as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Get verification logs error: {e}")
        return (
            jsonify(create_response(False, "Failed to retrieve verification logs")),
            500,
        )


# 管理员API
@watermark_bp.route("/admin/all-watermarks", methods=["GET"])
@admin_required
@rate_limit(requests_per_minute=30)
def admin_get_all_watermarks():
    """管理员获取所有水印"""
    try:
        # 分页参数
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        username = request.args.get("username")
        is_active = request.args.get("is_active", type=bool)

        page, per_page = validate_pagination(page, per_page)

        # 构建查询
        query = Watermark.query

        if username:
            query = query.filter(Watermark.username.contains(username))

        if is_active is not None:
            query = query.filter_by(is_active=is_active)

        # 按创建时间倒序
        query = query.order_by(Watermark.created_at.desc())

        # 分页
        pagination = paginate_query(query, page, per_page)

        return jsonify(
            create_response(
                success=True,
                message="All watermarks retrieved successfully",
                data={
                    "watermarks": [
                        watermark.to_dict() for watermark in pagination["items"]
                    ],
                    "pagination": {
                        "page": pagination["page"],
                        "per_page": pagination["per_page"],
                        "total": pagination["total"],
                        "pages": pagination["pages"],
                        "has_prev": pagination["has_prev"],
                        "has_next": pagination["has_next"],
                    },
                },
            )
        )

    except ValidationError as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Admin get all watermarks error: {e}")
        return jsonify(create_response(False, "Failed to retrieve watermarks")), 500


@watermark_bp.route("/admin/statistics", methods=["GET"])
@admin_required
@rate_limit(requests_per_minute=30)
def admin_get_statistics():
    """管理员获取系统水印统计"""
    try:
        watermark_service = WatermarkService()
        stats = watermark_service.get_watermark_statistics()

        # 添加额外的管理员统计信息
        from datetime import datetime, timedelta

        # 最近30天的活动
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_watermarks = Watermark.query.filter(
            Watermark.created_at >= thirty_days_ago
        ).count()

        recent_verifications = WatermarkVerificationLog.query.filter(
            WatermarkVerificationLog.verified_at >= thirty_days_ago
        ).count()

        # 活跃用户统计
        active_users = (
            db.session.query(Watermark.user_id)
            .filter(Watermark.is_active == True, Watermark.last_used >= thirty_days_ago)
            .distinct()
            .count()
        )

        stats.update(
            {
                "recent_30_days": {
                    "new_watermarks": recent_watermarks,
                    "verifications": recent_verifications,
                    "active_users": active_users,
                }
            }
        )

        return jsonify(
            create_response(
                success=True,
                message="System watermark statistics retrieved successfully",
                data=stats,
            )
        )

    except Exception as e:
        current_app.logger.error(f"Admin get statistics error: {e}")
        return jsonify(create_response(False, "Failed to retrieve statistics")), 500


@watermark_bp.route("/admin/verification-logs", methods=["GET"])
@admin_required
@rate_limit(requests_per_minute=30)
def admin_get_verification_logs():
    """管理员获取所有验证日志"""
    try:
        # 分页参数
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        success = request.args.get("success", type=bool)
        watermark_code = request.args.get("watermark_code")

        page, per_page = validate_pagination(page, per_page)

        # 构建查询
        query = WatermarkVerificationLog.query

        if success is not None:
            query = query.filter_by(success=success)

        if watermark_code:
            query = query.filter(
                WatermarkVerificationLog.watermark_code.contains(watermark_code)
            )

        # 按验证时间倒序
        query = query.order_by(WatermarkVerificationLog.verified_at.desc())

        # 分页
        pagination = paginate_query(query, page, per_page)

        return jsonify(
            create_response(
                success=True,
                message="All verification logs retrieved successfully",
                data={
                    "logs": [log.to_dict() for log in pagination["items"]],
                    "pagination": {
                        "page": pagination["page"],
                        "per_page": pagination["per_page"],
                        "total": pagination["total"],
                        "pages": pagination["pages"],
                        "has_prev": pagination["has_prev"],
                        "has_next": pagination["has_next"],
                    },
                },
            )
        )

    except ValidationError as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Admin get verification logs error: {e}")
        return (
            jsonify(create_response(False, "Failed to retrieve verification logs")),
            500,
        )


@watermark_bp.route("/info/<watermark_code>", methods=["GET"])
@rate_limit(requests_per_minute=100)
def get_watermark_info(watermark_code):
    """根据水印码获取公开信息（无需认证）"""
    try:
        watermark = Watermark.query.filter_by(
            watermark_code=watermark_code, is_active=True
        ).first()

        if not watermark:
            return (
                jsonify(create_response(success=False, message="Watermark not found")),
                404,
            )

        # 只返回公开信息
        public_info = {
            "watermark_code": watermark.watermark_code,
            "username": watermark.username,
            "created_at": watermark.created_at.isoformat(),
            "description": watermark.description,
            "usage_count": watermark.usage_count,
        }

        return jsonify(
            create_response(
                success=True,
                message="Watermark information retrieved successfully",
                data=public_info,
            )
        )

    except Exception as e:
        current_app.logger.error(f"Get watermark info error: {e}")
        return (
            jsonify(create_response(False, "Failed to retrieve watermark information")),
            500,
        )
