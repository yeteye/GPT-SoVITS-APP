# ./gpt-sovits-backend/app/api/admin.py
from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import RequestEntityTooLarge
from app.extensions import db
from app.models.user import User
from app.models.model import VoiceModel, Tag
from app.models.task import VoiceCloneTask, TTSTask
from app.models.audit import AuditLog, UserUpload
from app.auth.decorators import admin_required, auditor_required, rate_limit, log_action
from app.utils.validators import (
    validate_model_upload_data,
    validate_model_file,
    validate_pagination,
    validate_role,
    validate_file_pair,
)
from app.utils.helpers import (
    save_uploaded_file,
    create_response,
    paginate_query,
    log_user_action,
)
from app.utils.exceptions import ValidationError, ResourceNotFoundError
import os
from datetime import datetime, timedelta

admin_bp = Blueprint("admin", __name__)


@admin_bp.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    """处理文件过大错误"""
    max_size_mb = current_app.config["MAX_CONTENT_LENGTH"] / (1024 * 1024)
    return (
        jsonify(
            create_response(
                success=False,
                message=f"文件太大，最大允许 {max_size_mb:.0f}MB。请压缩文件或分批上传。",
                code="FILE_TOO_LARGE",
            )
        ),
        413,
    )


# app/api/admin.py - upload_official_model函数部分修改
@admin_bp.route("/upload-official-model", methods=["POST"])
@admin_required
@rate_limit(requests_per_minute=5)
@log_action("upload_official_model", "voice_model")
def upload_official_model():
    """上传官方预训练模型 - 修复：要求必须上传两个文件"""
    try:
        user = request.current_user

        # 提前检查请求大小
        content_length = request.content_length
        max_length = current_app.config["MAX_CONTENT_LENGTH"]

        if content_length and content_length > max_length:
            max_size_mb = max_length / (1024 * 1024)
            raise ValidationError(
                f"请求大小 {content_length/(1024*1024):.1f}MB 超过限制 {max_size_mb:.0f}MB"
            )

        # 检查文件上传 - 修复：要求必须提供两个文件
        gpt_file = request.files.get("gpt_model_file")
        sovits_file = request.files.get("sovits_model_file")

        if not gpt_file:
            raise ValidationError("GPT模型文件(.pth)是必需的", "gpt_model_file")

        if not sovits_file:
            raise ValidationError("SoVITS模型文件(.ckpt)是必需的", "sovits_model_file")

        # 获取并验证文件大小
        def check_file_size(file, file_type):
            if file:
                file.seek(0, 2)  # 移动到文件末尾
                size = file.tell()
                file.seek(0)  # 重置到开头

                max_individual_size = max_length  # 单个文件也不能超过总限制
                if size > max_individual_size:
                    size_mb = size / (1024 * 1024)
                    max_mb = max_individual_size / (1024 * 1024)
                    raise ValidationError(
                        f"{file_type}文件 {size_mb:.1f}MB 超过单文件限制 {max_mb:.0f}MB"
                    )

                current_app.logger.info(
                    f"{file_type}文件大小: {size/(1024*1024):.1f}MB"
                )
                return size

        gpt_size = check_file_size(gpt_file, "GPT")
        sovits_size = check_file_size(sovits_file, "SoVITS")
        total_size = gpt_size + sovits_size

        # 检查总大小
        if total_size > max_length:
            total_mb = total_size / (1024 * 1024)
            max_mb = max_length / (1024 * 1024)
            raise ValidationError(
                f"文件总大小 {total_mb:.1f}MB 超过限制 {max_mb:.0f}MB"
            )

        # 获取模型信息
        model_name = request.form.get("model_name", "").strip()
        description = request.form.get("description", "").strip()
        supported_emotions = request.form.getlist("supported_emotions")
        supported_languages = request.form.getlist("supported_languages")
        tags = request.form.getlist("tags")

        # 验证上传数据
        form_data = {
            "name": model_name,
            "description": description,
            "supported_emotions": supported_emotions,
            "supported_languages": supported_languages,
        }
        validate_model_upload_data(form_data, gpt_file, sovits_file)

        # 检查模型名称是否已存在
        existing_model = VoiceModel.query.filter_by(name=model_name).first()
        if existing_model:
            raise ValidationError("模型名称已存在", "model_name")

        # 验证文件对
        validate_file_pair(gpt_file, sovits_file, model_name)

        current_app.logger.info(f"开始保存模型文件: {model_name}")

        # 保存模型文件
        try:
            current_app.logger.info("保存GPT模型文件...")
            validate_model_file(gpt_file, expected_type="gpt")
            gpt_file_info = save_uploaded_file(gpt_file, "models/official", "gpt")
            current_app.logger.info(f"GPT文件已保存: {gpt_file_info['file_path']}")

            current_app.logger.info("保存SoVITS模型文件...")
            validate_model_file(sovits_file, expected_type="sovits")
            sovits_file_info = save_uploaded_file(
                sovits_file, "models/official", "sovits"
            )
            current_app.logger.info(
                f"SoVITS文件已保存: {sovits_file_info['file_path']}"
            )

        except Exception as save_error:
            # 清理已保存的文件
            if (
                "gpt_file_info" in locals()
                and gpt_file_info
                and os.path.exists(gpt_file_info["file_path"])
            ):
                os.remove(gpt_file_info["file_path"])
            if (
                "sovits_file_info" in locals()
                and sovits_file_info
                and os.path.exists(sovits_file_info["file_path"])
            ):
                os.remove(sovits_file_info["file_path"])
            raise ValidationError(f"文件保存失败: {str(save_error)}")

        # 创建模型记录
        voice_model = VoiceModel(
            name=model_name,
            description=description,
            model_type="official",
            gpt_model_path=gpt_file_info["file_path"],
            sovits_model_path=sovits_file_info["file_path"],
            status="active",
            is_public=True,
            is_featured=True,
            quality_score=9.0,
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

        current_app.logger.info(
            f"官方模型创建成功: {model_name} (ID: {voice_model.id})"
        )

        return (
            jsonify(
                create_response(
                    success=True,
                    message="官方模型上传成功",
                    data={"model": voice_model.to_dict(include_paths=True)},
                )
            ),
            201,
        )

    except RequestEntityTooLarge:
        # 处理Flask自动抛出的413错误
        max_size_mb = current_app.config["MAX_CONTENT_LENGTH"] / (1024 * 1024)
        return (
            jsonify(
                create_response(
                    success=False,
                    message=f"文件太大，最大允许 {max_size_mb:.0f}MB",
                    code="FILE_TOO_LARGE",
                )
            ),
            413,
        )

    except ValidationError as e:
        current_app.logger.error(f"验证错误: {str(e)}")
        return jsonify(create_response(False, str(e))), 422

    except Exception as e:
        current_app.logger.error(f"上传官方模型错误: {str(e)}", exc_info=True)
        return jsonify(create_response(False, f"上传失败: {str(e)}")), 500


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

        # 模型统计 - 修改：区分GPT和SoVITS模型完整性
        total_models = VoiceModel.query.count()
        official_models = VoiceModel.query.filter_by(model_type="official").count()
        user_models = VoiceModel.query.filter_by(model_type="user_trained").count()
        pending_review = VoiceModel.query.filter_by(review_status="pending").count()

        # 新增：模型文件完整性统计
        models_with_both_files = 0
        models_with_gpt_only = 0
        models_with_sovits_only = 0
        models_with_no_files = 0

        for model in VoiceModel.query.all():
            validation = model.validate_model_files()
            if validation["all_files_exist"]:
                models_with_both_files += 1
            elif validation["gpt_model_exists"]:
                models_with_gpt_only += 1
            elif validation["sovits_model_exists"]:
                models_with_sovits_only += 1
            else:
                models_with_no_files += 1

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
                        "file_integrity": {
                            "complete_models": models_with_both_files,
                            "gpt_only": models_with_gpt_only,
                            "sovits_only": models_with_sovits_only,
                            "no_files": models_with_no_files,
                        },
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
    """系统清理 - 修复：使用正确的模型字段名"""
    try:
        data = request.get_json() or {}
        cleanup_types = data.get("types", ["temp_files", "expired_tokens"])

        results = {}

        if "temp_files" in cleanup_types:
            from app.utils.helpers import clean_temp_files

            cleaned_count = clean_temp_files()
            results["temp_files"] = f"Cleaned {cleaned_count} temporary files"

        if "expired_tokens" in cleanup_types:
            from app.auth.utils import clean_expired_tokens

            count = clean_expired_tokens()
            results["expired_tokens"] = f"Cleaned {count} expired tokens"

        if "inactive_models" in cleanup_types:
            # 🔧 修复：清理长期未使用的非活跃模型，使用正确字段名
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            inactive_models = VoiceModel.query.filter(
                VoiceModel.status == "inactive",
                VoiceModel.updated_at < cutoff_date,
                VoiceModel.model_type
                == "user_trained",  # 只清理用户训练的模型，保护官方模型
            ).all()

            cleaned_models = 0
            for model in inactive_models:
                try:
                    # 🔧 修复：删除正确的模型文件
                    files_to_delete = [
                        model.gpt_model_path,  # 新字段：GPT模型文件
                        model.sovits_model_path,  # 新字段：SoVITS模型文件
                    ]

                    # 删除物理文件
                    for file_path in files_to_delete:
                        if file_path and os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                                current_app.logger.info(f"Deleted file: {file_path}")
                            except Exception as file_error:
                                current_app.logger.warning(
                                    f"Failed to delete file {file_path}: {file_error}"
                                )

                    # 尝试删除空的模型目录
                    model_dirs = set()
                    for file_path in files_to_delete:
                        if file_path:
                            model_dirs.add(os.path.dirname(file_path))

                    for model_dir in model_dirs:
                        try:
                            if os.path.exists(model_dir) and not os.listdir(model_dir):
                                os.rmdir(model_dir)
                                current_app.logger.info(
                                    f"Deleted empty directory: {model_dir}"
                                )
                        except Exception as dir_error:
                            current_app.logger.warning(
                                f"Failed to delete directory {model_dir}: {dir_error}"
                            )

                    # 删除数据库记录
                    db.session.delete(model)
                    cleaned_models += 1

                except Exception as model_error:
                    current_app.logger.error(
                        f"Failed to cleanup model {model.id}: {model_error}"
                    )
                    continue

            db.session.commit()
            results["inactive_models"] = f"Cleaned {cleaned_models} inactive models"

        if "orphaned_files" in cleanup_types:
            # 🔧 新增：清理孤立文件
            from app.services.file_service import cleanup_orphaned_files

            try:
                orphaned_count = cleanup_orphaned_files()
                results["orphaned_files"] = f"Cleaned {orphaned_count} orphaned files"
            except Exception as e:
                current_app.logger.error(f"Orphaned files cleanup failed: {e}")
                results["orphaned_files"] = f"Failed: {str(e)}"

        if "old_tasks" in cleanup_types:
            # 🔧 新增：清理旧任务
            from app.services.task_service import TaskService

            try:
                cleanup_result = TaskService.cleanup_old_tasks(
                    days_threshold=30, keep_completed=True
                )
                total_cleaned = cleanup_result["total_deleted"]
                results["old_tasks"] = f"Cleaned {total_cleaned} old tasks"
            except Exception as e:
                current_app.logger.error(f"Old tasks cleanup failed: {e}")
                results["old_tasks"] = f"Failed: {str(e)}"

        return jsonify(
            create_response(
                success=True,
                message="System cleanup completed",
                data={
                    "results": results,
                    "cleanup_types": cleanup_types,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
        )

    except Exception as e:
        current_app.logger.error(f"System cleanup error: {e}")
        return jsonify(create_response(False, f"System cleanup failed: {str(e)}")), 500


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


@admin_bp.route("/models/<model_id>/validate-files", methods=["POST"])
@admin_required
@rate_limit(requests_per_minute=20)
@log_action("validate_model_files", "voice_model")
def validate_model_files(model_id):
    """验证模型文件完整性 - 新增API"""
    try:
        model = VoiceModel.query.get(model_id)
        if not model:
            raise ResourceNotFoundError("Voice model")

        # 验证文件存在性
        validation_result = model.validate_model_files()
        print(f"Validation result: {validation_result}")

        # 检查文件大小和格式
        file_details = {}

        if model.gpt_model_path and os.path.exists(model.gpt_model_path):
            file_details["gpt_model"] = {
                "path": model.gpt_model_path,
                "size": os.path.getsize(model.gpt_model_path),
                "exists": True,
            }
        else:
            file_details["gpt_model"] = {
                "path": model.gpt_model_path,
                "exists": False,
                "error": "File not found",
            }

        if model.sovits_model_path and os.path.exists(model.sovits_model_path):
            file_details["sovits_model"] = {
                "path": model.sovits_model_path,
                "size": os.path.getsize(model.sovits_model_path),
                "exists": True,
            }
        else:
            file_details["sovits_model"] = {
                "path": model.sovits_model_path,
                "exists": False,
                "error": "File not found",
            }

        return jsonify(
            create_response(
                success=True,
                message="Model file validation completed",
                data={
                    "validation_result": validation_result,
                    "file_details": file_details,
                },
            )
        )

    except ResourceNotFoundError as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Validate model files error: {e}")
        return jsonify(create_response(False, "Failed to validate model files")), 500
