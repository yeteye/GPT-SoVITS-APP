from flask import Blueprint, request, jsonify, current_app
from app.extensions import db
from app.models.user import User
from app.models.model import VoiceModel, Tag
from app.models.task import VoiceCloneTask, TTSTask
from app.models.audit import AuditLog, UserUpload
from app.auth.decorators import admin_required, auditor_required, rate_limit, log_action
from app.utils.validators import validate_model_file, validate_pagination, validate_role
from app.utils.helpers import (
    save_uploaded_file,
    create_response,
    paginate_query,
    log_user_action,
)
from app.utils.exceptions import ValidationError, ResourceNotFoundError
import os
import datetime
import timedelta

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/upload-official-model", methods=["POST"])
@admin_required
@rate_limit(requests_per_minute=5)
@log_action("upload_official_model", "voice_model")
def upload_official_model():
    """上传官方预训练模型"""
    try:
        user = request.current_user

        # 检查文件上传
        if "model_file" not in request.files:
            raise ValidationError("No model file provided", "model_file")

        model_file = request.files["model_file"]
        validate_model_file(model_file)

        # 获取模型信息
        model_name = request.form.get("model_name", "").strip()
        description = request.form.get("description", "").strip()
        supported_emotions = request.form.getlist("supported_emotions")
        supported_languages = request.form.getlist("supported_languages")
        tags = request.form.getlist("tags")

        if not model_name:
            raise ValidationError("Model name is required", "model_name")

        # 检查模型名称是否已存在
        existing_model = VoiceModel.query.filter_by(name=model_name).first()
        if existing_model:
            raise ValidationError("Model name already exists", "model_name")

        # 保存模型文件
        file_info = save_uploaded_file(model_file, "models/official", "official")

        # 创建模型记录
        voice_model = VoiceModel(
            name=model_name,
            description=description,
            model_type="official",
            model_path=file_info["file_path"],
            status="active",
            is_public=True,
            is_featured=True,
            quality_score=9.0,  # 官方模型默认高质量
            review_status="approved",
            reviewed_by=user.id,
            reviewed_at=db.func.now(),
        )

        # 设置支持的情感和语言
        if supported_emotions:
            voice_model.set_supported_emotions(supported_emotions)
        else:
            voice_model.set_supported_emotions(["neutral", "happy", "sad", "calm"])

        if supported_languages:
            voice_model.set_supported_languages(supported_languages)
        else:
            voice_model.set_supported_languages(["zh-CN"])

        # 添加标签
        for tag_name in tags:
            tag = Tag.get_or_create(tag_name.strip())
            voice_model.tags.append(tag)

        db.session.add(voice_model)
        db.session.commit()

        return (
            jsonify(
                create_response(
                    success=True,
                    message="Official model uploaded successfully",
                    data={"model": voice_model.to_dict(include_paths=True)},
                )
            ),
            201,
        )

    except ValidationError as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Upload official model error: {e}")
        return jsonify(create_response(False, "Failed to upload model")), 500


@admin_bp.route("/models", methods=["GET"])
@auditor_required
@rate_limit(requests_per_minute=30)
def get_all_models():
    """获取所有模型列表（管理员视图）"""
    try:
        # 分页参数
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        model_type = request.args.get("type")
        status = request.args.get("status")
        review_status = request.args.get("review_status")

        page, per_page = validate_pagination(page, per_page)

        # 构建查询
        query = VoiceModel.query

        if model_type:
            query = query.filter_by(model_type=model_type)

        if status:
            query = query.filter_by(status=status)

        if review_status:
            query = query.filter_by(review_status=review_status)

        # 按创建时间倒序排列
        query = query.order_by(VoiceModel.created_at.desc())

        # 分页
        pagination = paginate_query(query, page, per_page)

        return jsonify(
            create_response(
                success=True,
                message="Models retrieved successfully",
                data={
                    "models": [
                        model.to_dict(include_paths=True)
                        for model in pagination["items"]
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
        current_app.logger.error(f"Get all models error: {e}")
        return jsonify(create_response(False, "Failed to retrieve models")), 500


@admin_bp.route("/models/<model_id>/review", methods=["POST"])
@auditor_required
@rate_limit(requests_per_minute=20)
@log_action("review_model", "voice_model")
def review_model(model_id):
    """审核模型"""
    try:
        user = request.current_user
        data = request.get_json()

        if not data:
            raise ValidationError("Request body is required")

        model = VoiceModel.query.get(model_id)
        if not model:
            raise ResourceNotFoundError("Voice model")

        review_status = data.get("status")  # approved, rejected
        review_message = data.get("message", "").strip()

        if review_status not in ["approved", "rejected"]:
            raise ValidationError(
                'Invalid review status. Must be "approved" or "rejected"'
            )

        # 设置审核结果
        model.set_review_result(review_status, review_message, user.id)

        return jsonify(
            create_response(
                success=True,
                message=f"Model {review_status} successfully",
                data={"model": model.to_dict(include_paths=True)},
            )
        )

    except (ValidationError, ResourceNotFoundError) as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Review model error: {e}")
        return jsonify(create_response(False, "Failed to review model")), 500


@admin_bp.route("/users", methods=["GET"])
@admin_required
@rate_limit(requests_per_minute=30)
def get_all_users():
    """获取所有用户列表"""
    try:
        # 分页参数
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        role = request.args.get("role", type=int)
        is_active = request.args.get("is_active", type=bool)

        page, per_page = validate_pagination(page, per_page)

        # 构建查询
        query = User.query

        if role is not None:
            query = query.filter_by(role=role)

        if is_active is not None:
            query = query.filter_by(is_active=is_active)

        # 按创建时间倒序排列
        query = query.order_by(User.created_at.desc())

        # 分页
        pagination = paginate_query(query, page, per_page)

        return jsonify(
            create_response(
                success=True,
                message="Users retrieved successfully",
                data={
                    "users": [
                        user.to_dict(include_sensitive=True)
                        for user in pagination["items"]
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
        current_app.logger.error(f"Get all users error: {e}")
        return jsonify(create_response(False, "Failed to retrieve users")), 500


@admin_bp.route("/users/<user_id>/role", methods=["PUT"])
@admin_required
@rate_limit(requests_per_minute=10)
@log_action("update_user_role", "user")
def update_user_role(user_id):
    """更新用户角色"""
    try:
        admin_user = request.current_user
        data = request.get_json()

        if not data:
            raise ValidationError("Request body is required")

        target_user = User.query.get(user_id)
        if not target_user:
            raise ResourceNotFoundError("User")

        new_role = data.get("role")
        if new_role is None:
            raise ValidationError("Role is required", "role")

        validate_role(new_role)

        # 防止管理员降级自己
        if target_user.id == admin_user.id and new_role < admin_user.role:
            raise ValidationError("Cannot downgrade your own role")

        old_role = target_user.role
        target_user.role = new_role
        db.session.commit()

        # 记录角色变更
        role_names = {0: "User", 1: "Auditor", 2: "Admin"}
        log_user_action(
            user_id=admin_user.id,
            action="update_user_role",
            resource_type="user",
            resource_id=target_user.id,
            details=f"Changed user {target_user.username} role from {role_names.get(old_role)} to {role_names.get(new_role)}",
        )

        return jsonify(
            create_response(
                success=True,
                message="User role updated successfully",
                data={"user": target_user.to_dict(include_sensitive=True)},
            )
        )

    except (ValidationError, ResourceNotFoundError) as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Update user role error: {e}")
        return jsonify(create_response(False, "Failed to update user role")), 500


@admin_bp.route("/users/<user_id>/status", methods=["PUT"])
@admin_required
@rate_limit(requests_per_minute=10)
@log_action("update_user_status", "user")
def update_user_status(user_id):
    """更新用户状态（激活/禁用）"""
    try:
        admin_user = request.current_user
        data = request.get_json()

        if not data:
            raise ValidationError("Request body is required")

        target_user = User.query.get(user_id)
        if not target_user:
            raise ResourceNotFoundError("User")

        is_active = data.get("is_active")
        if is_active is None:
            raise ValidationError("is_active is required")

        # 防止管理员禁用自己
        if target_user.id == admin_user.id and not is_active:
            raise ValidationError("Cannot deactivate your own account")

        old_status = target_user.is_active
        target_user.is_active = is_active
        db.session.commit()

        action = "activated" if is_active else "deactivated"

        log_user_action(
            user_id=admin_user.id,
            action="update_user_status",
            resource_type="user",
            resource_id=target_user.id,
            details=f"User {target_user.username} {action}",
        )

        return jsonify(
            create_response(
                success=True,
                message=f"User {action} successfully",
                data={"user": target_user.to_dict(include_sensitive=True)},
            )
        )

    except (ValidationError, ResourceNotFoundError) as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Update user status error: {e}")
        return jsonify(create_response(False, "Failed to update user status")), 500


@admin_bp.route("/audit-logs", methods=["GET"])
@admin_required
@rate_limit(requests_per_minute=30)
def get_audit_logs():
    """获取审计日志"""
    try:
        # 分页参数
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        action = request.args.get("action")
        resource_type = request.args.get("resource_type")
        user_id = request.args.get("user_id")

        page, per_page = validate_pagination(page, per_page)

        # 构建查询
        query = AuditLog.query

        if action:
            query = query.filter_by(action=action)

        if resource_type:
            query = query.filter_by(resource_type=resource_type)

        if user_id:
            query = query.filter_by(user_id=user_id)

        # 按创建时间倒序排列
        query = query.order_by(AuditLog.created_at.desc())

        # 分页
        pagination = paginate_query(query, page, per_page)

        return jsonify(
            create_response(
                success=True,
                message="Audit logs retrieved successfully",
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
        current_app.logger.error(f"Get audit logs error: {e}")
        return jsonify(create_response(False, "Failed to retrieve audit logs")), 500


@admin_bp.route("/statistics", methods=["GET"])
@admin_required
@rate_limit(requests_per_minute=30)
def get_system_statistics():
    """获取系统统计信息"""
    try:
        from datetime import datetime, timedelta

        # 用户统计
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        new_users_today = User.query.filter(
            User.created_at >= datetime.utcnow().date()
        ).count()

        # 模型统计
        total_models = VoiceModel.query.count()
        official_models = VoiceModel.query.filter_by(model_type="official").count()
        user_models = VoiceModel.query.filter_by(model_type="user_trained").count()
        pending_review = VoiceModel.query.filter_by(review_status="pending").count()

        # 任务统计
        total_voice_clone_tasks = VoiceCloneTask.query.count()
        total_tts_tasks = TTSTask.query.count()

        # 今日任务
        today_voice_clone = VoiceCloneTask.query.filter(
            VoiceCloneTask.created_at >= datetime.utcnow().date()
        ).count()
        today_tts = TTSTask.query.filter(
            TTSTask.created_at >= datetime.utcnow().date()
        ).count()

        # 存储统计
        total_uploads = UserUpload.query.count()
        total_storage = (
            db.session.query(db.func.sum(UserUpload.file_size)).scalar() or 0
        )

        return jsonify(
            create_response(
                success=True,
                message="System statistics retrieved successfully",
                data={
                    "users": {
                        "total": total_users,
                        "active": active_users,
                        "new_today": new_users_today,
                    },
                    "models": {
                        "total": total_models,
                        "official": official_models,
                        "user_trained": user_models,
                        "pending_review": pending_review,
                    },
                    "tasks": {
                        "voice_clone_total": total_voice_clone_tasks,
                        "tts_total": total_tts_tasks,
                        "voice_clone_today": today_voice_clone,
                        "tts_today": today_tts,
                    },
                    "storage": {
                        "total_uploads": total_uploads,
                        "total_size_bytes": int(total_storage),
                        "total_size_mb": round(total_storage / (1024 * 1024), 2),
                    },
                },
            )
        )

    except Exception as e:
        current_app.logger.error(f"Get system statistics error: {e}")
        return (
            jsonify(create_response(False, "Failed to retrieve system statistics")),
            500,
        )


@admin_bp.route("/cleanup", methods=["POST"])
@admin_required
@rate_limit(requests_per_minute=5)
@log_action("system_cleanup", "system")
def system_cleanup():
    """系统清理"""
    try:
        data = request.get_json() or {}
        cleanup_types = data.get("types", ["temp_files", "expired_tokens"])

        results = {}

        if "temp_files" in cleanup_types:
            from app.utils.helpers import clean_temp_files

            clean_temp_files()
            results["temp_files"] = "Cleaned"

        if "expired_tokens" in cleanup_types:
            from app.auth.utils import clean_expired_tokens

            count = clean_expired_tokens()
            results["expired_tokens"] = f"Cleaned {count} tokens"

        if "inactive_models" in cleanup_types:
            # 清理长期未使用的非活跃模型
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            inactive_models = VoiceModel.query.filter(
                VoiceModel.status == "inactive", VoiceModel.updated_at < cutoff_date
            ).all()

            for model in inactive_models:
                # 删除物理文件
                files_to_delete = [
                    model.model_path,
                    model.config_path,
                    model.index_path,
                ]
                for file_path in files_to_delete:
                    if file_path and os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except Exception:
                            pass

                # 删除数据库记录
                db.session.delete(model)

            db.session.commit()
            results["inactive_models"] = f"Cleaned {len(inactive_models)} models"

        return jsonify(
            create_response(
                success=True,
                message="System cleanup completed",
                data={"results": results},
            )
        )

    except Exception as e:
        current_app.logger.error(f"System cleanup error: {e}")
        return jsonify(create_response(False, "System cleanup failed")), 500


@admin_bp.route("/tags", methods=["POST"])
@admin_required
@rate_limit(requests_per_minute=20)
@log_action("create_tag", "tag")
def create_tag():
    """创建新标签"""
    try:
        data = request.get_json()

        if not data:
            raise ValidationError("Request body is required")

        name = data.get("name", "").strip()
        description = data.get("description", "").strip()
        color = data.get("color", "#007bff").strip()

        if not name:
            raise ValidationError("Tag name is required", "name")

        # 检查标签是否已存在
        existing_tag = Tag.query.filter_by(name=name).first()
        if existing_tag:
            raise ValidationError("Tag already exists", "name")

        # 创建标签
        tag = Tag(name=name, description=description, color=color)

        db.session.add(tag)
        db.session.commit()

        return (
            jsonify(
                create_response(
                    success=True,
                    message="Tag created successfully",
                    data={"tag": tag.to_dict()},
                )
            ),
            201,
        )

    except ValidationError as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Create tag error: {e}")
        return jsonify(create_response(False, "Failed to create tag")), 500


@admin_bp.route("/tags/<tag_id>", methods=["DELETE"])
@admin_required
@rate_limit(requests_per_minute=10)
@log_action("delete_tag", "tag")
def delete_tag(tag_id):
    """删除标签"""
    try:
        tag = Tag.query.get(tag_id)
        if not tag:
            raise ResourceNotFoundError("Tag")

        # 检查标签是否正在使用
        models_count = (
            VoiceModel.query.join(VoiceModel.tags).filter(Tag.id == tag.id).count()
        )

        if models_count > 0:
            raise ValidationError(
                f"Cannot delete tag. It is used by {models_count} models"
            )

        db.session.delete(tag)
        db.session.commit()

        return jsonify(
            create_response(success=True, message="Tag deleted successfully")
        )

    except (ValidationError, ResourceNotFoundError) as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Delete tag error: {e}")
        return jsonify(create_response(False, "Failed to delete tag")), 500
