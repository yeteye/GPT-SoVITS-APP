# ./gpt-sovits-backend/app/api/user.py
from flask import Blueprint, request, jsonify, current_app
from app.extensions import db
from app.models.user import User
from app.models.task import VoiceCloneTask, TTSTask
from app.models.model import VoiceModel
from app.models.audit import UserUpload
from app.auth.decorators import auth_required, rate_limit, log_action
from app.utils.validators import validate_email, validate_username, validate_pagination
from app.utils.helpers import create_response, paginate_query, log_user_action
from app.utils.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    ResourceConflictError,
)

user_bp = Blueprint("user", __name__)


@user_bp.route("/profile", methods=["GET"])
@auth_required
@rate_limit(requests_per_minute=60)
def get_profile():
    """获取用户个人资料"""
    try:
        user = request.current_user

        # 获取用户统计信息
        voice_clone_tasks = VoiceCloneTask.query.filter_by(user_id=user.id).count()
        tts_tasks = TTSTask.query.filter_by(user_id=user.id).count()
        voice_models = VoiceModel.query.filter_by(owner_id=user.id).count()
        uploads = UserUpload.query.filter_by(user_id=user.id, is_deleted=False).count()

        profile_data = user.to_dict(include_sensitive=True)
        profile_data["statistics"] = {
            "voice_clone_tasks": voice_clone_tasks,
            "tts_tasks": tts_tasks,
            "voice_models": voice_models,
            "uploads": uploads,
        }

        return jsonify(
            create_response(
                success=True,
                message="Profile retrieved successfully",
                data={"profile": profile_data},
            )
        )

    except Exception as e:
        current_app.logger.error(f"Get profile error: {e}")
        return jsonify(create_response(False, "Failed to retrieve profile")), 500


@user_bp.route("/profile", methods=["PUT"])
@auth_required
@rate_limit(requests_per_minute=10)
@log_action("update_profile", "user")
def update_profile():
    """更新用户个人资料"""
    try:
        user = request.current_user
        data = request.get_json()

        if not data:
            raise ValidationError("Request body is required")

        # 可更新的字段
        updatable_fields = ["username", "email", "avatar_url"]
        old_values = {}
        new_values = {}

        for field in updatable_fields:
            if field in data:
                new_value = data[field]

                if field == "username":
                    new_value = new_value.strip()
                    if new_value != user.username:
                        validate_username(new_value)
                        # 检查用户名是否已被使用
                        existing_user = User.query.filter_by(username=new_value).first()
                        if existing_user and existing_user.id != user.id:
                            raise ResourceConflictError("Username already exists")

                        old_values["username"] = user.username
                        user.username = new_value
                        new_values["username"] = new_value

                elif field == "email":
                    new_value = new_value.strip().lower()
                    if new_value != user.email:
                        validate_email(new_value)
                        # 检查邮箱是否已被使用
                        existing_user = User.query.filter_by(email=new_value).first()
                        if existing_user and existing_user.id != user.id:
                            raise ResourceConflictError("Email already exists")

                        old_values["email"] = user.email
                        user.email = new_value
                        user.is_verified = False  # 需要重新验证邮箱
                        new_values["email"] = new_value

                elif field == "avatar_url":
                    if new_value and len(new_value) > 255:
                        raise ValidationError("Avatar URL too long")

                    old_values["avatar_url"] = user.avatar_url
                    user.avatar_url = new_value
                    new_values["avatar_url"] = new_value

        if old_values:  # 只有在有更改时才提交
            db.session.commit()

            # 记录更改
            from app.models.audit import AuditLog

            AuditLog.log_action(
                action="update_profile",
                resource_type="user",
                user_id=user.id,
                resource_id=user.id,
                old_values=old_values,
                new_values=new_values,
                description="Updated user profile",
            )

        return jsonify(
            create_response(
                success=True,
                message="Profile updated successfully",
                data={"profile": user.to_dict(include_sensitive=True)},
            )
        )

    except (ValidationError, ResourceConflictError) as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Update profile error: {e}")
        return jsonify(create_response(False, "Failed to update profile")), 500


@user_bp.route("/tasks/history", methods=["GET"])
@auth_required
@rate_limit(requests_per_minute=30)
def get_task_history():
    """获取用户任务历史"""
    try:
        user = request.current_user

        # 分页参数
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        task_type = request.args.get("type")  # voice_clone, tts
        status = request.args.get("status")

        page, per_page = validate_pagination(page, per_page)

        tasks = []

        if not task_type or task_type == "voice_clone":
            # 获取语音克隆任务
            vc_query = VoiceCloneTask.query.filter_by(user_id=user.id)
            if status:
                vc_query = vc_query.filter_by(status=status)

            vc_tasks = vc_query.order_by(VoiceCloneTask.created_at.desc()).all()
            for task in vc_tasks:
                task_data = task.to_dict()
                task_data["task_type"] = "voice_clone"
                tasks.append(task_data)

        if not task_type or task_type == "tts":
            # 获取TTS任务
            tts_query = TTSTask.query.filter_by(user_id=user.id)
            if status:
                tts_query = tts_query.filter_by(status=status)

            tts_tasks = tts_query.order_by(TTSTask.created_at.desc()).all()
            for task in tts_tasks:
                task_data = task.to_dict()
                task_data["task_type"] = "tts"
                tasks.append(task_data)

        # 按创建时间排序
        tasks.sort(key=lambda x: x["created_at"], reverse=True)

        # 手动分页
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_tasks = tasks[start_idx:end_idx]

        total = len(tasks)
        pages = (total + per_page - 1) // per_page

        return jsonify(
            create_response(
                success=True,
                message="Task history retrieved successfully",
                data={
                    "tasks": paginated_tasks,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": total,
                        "pages": pages,
                        "has_prev": page > 1,
                        "has_next": page < pages,
                    },
                },
            )
        )

    except ValidationError as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Get task history error: {e}")
        return jsonify(create_response(False, "Failed to retrieve task history")), 500


@user_bp.route("/uploads", methods=["GET"])
@auth_required
@rate_limit(requests_per_minute=30)
def get_user_uploads():
    """获取用户上传文件列表"""
    try:
        user = request.current_user

        # 分页参数
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        file_type = request.args.get("type")  # audio, model, image

        page, per_page = validate_pagination(page, per_page)

        # 构建查询
        query = UserUpload.query.filter_by(user_id=user.id, is_deleted=False)

        if file_type:
            query = query.filter_by(file_type=file_type)

        # 按创建时间倒序排列
        query = query.order_by(UserUpload.created_at.desc())

        # 分页
        pagination = paginate_query(query, page, per_page)

        return jsonify(
            create_response(
                success=True,
                message="User uploads retrieved successfully",
                data={
                    "uploads": [upload.to_dict() for upload in pagination["items"]],
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
        current_app.logger.error(f"Get user uploads error: {e}")
        return jsonify(create_response(False, "Failed to retrieve uploads")), 500


@user_bp.route("/uploads/<upload_id>", methods=["DELETE"])
@auth_required
@rate_limit(requests_per_minute=20)
@log_action("delete_upload", "user_upload")
def delete_upload(upload_id):
    """删除上传文件"""
    try:
        user = request.current_user

        upload = UserUpload.query.filter_by(id=upload_id, user_id=user.id).first()

        if not upload:
            raise ResourceNotFoundError("Upload")

        # 检查文件是否正在使用
        if upload.file_type == "audio":
            # 检查是否在进行中的语音克隆任务中
            active_tasks = VoiceCloneTask.query.filter(
                VoiceCloneTask.user_id == user.id,
                VoiceCloneTask.status.in_(["pending", "processing"]),
            ).all()

            for task in active_tasks:
                sample_paths = task.get_audio_samples()
                if upload.file_path in sample_paths:
                    raise ValidationError(
                        "Cannot delete file while it is being used in training"
                    )

        # 标记为已删除
        upload.mark_deleted()

        # 删除物理文件
        import os

        try:
            if os.path.exists(upload.file_path):
                os.remove(upload.file_path)
        except Exception as e:
            current_app.logger.warning(f"Failed to delete physical file: {e}")

        return jsonify(
            create_response(success=True, message="Upload deleted successfully")
        )

    except (ResourceNotFoundError, ValidationError) as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Delete upload error: {e}")
        return jsonify(create_response(False, "Failed to delete upload")), 500


@user_bp.route("/statistics", methods=["GET"])
@auth_required
@rate_limit(requests_per_minute=30)
def get_user_statistics():
    """获取用户统计信息"""
    try:
        user = request.current_user
        from datetime import datetime, timedelta

        # 任务统计
        total_voice_clone = VoiceCloneTask.query.filter_by(user_id=user.id).count()
        completed_voice_clone = VoiceCloneTask.query.filter_by(
            user_id=user.id, status="completed"
        ).count()

        total_tts = TTSTask.query.filter_by(user_id=user.id).count()
        completed_tts = TTSTask.query.filter_by(
            user_id=user.id, status="completed"
        ).count()

        # 模型统计
        total_models = VoiceModel.query.filter_by(owner_id=user.id).count()
        public_models = VoiceModel.query.filter_by(
            owner_id=user.id, is_public=True, status="active"
        ).count()

        # 使用统计
        total_model_usage = (
            db.session.query(db.func.sum(VoiceModel.usage_count))
            .filter_by(owner_id=user.id)
            .scalar()
            or 0
        )

        total_downloads = (
            db.session.query(db.func.sum(VoiceModel.download_count))
            .filter_by(owner_id=user.id)
            .scalar()
            or 0
        )

        # 存储统计
        total_uploads = UserUpload.query.filter_by(
            user_id=user.id, is_deleted=False
        ).count()

        total_storage = (
            db.session.query(db.func.sum(UserUpload.file_size))
            .filter_by(user_id=user.id, is_deleted=False)
            .scalar()
            or 0
        )

        # 本月活动
        month_start = datetime.utcnow().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        month_voice_clone = VoiceCloneTask.query.filter(
            VoiceCloneTask.user_id == user.id, VoiceCloneTask.created_at >= month_start
        ).count()

        month_tts = TTSTask.query.filter(
            TTSTask.user_id == user.id, TTSTask.created_at >= month_start
        ).count()

        return jsonify(
            create_response(
                success=True,
                message="User statistics retrieved successfully",
                data={
                    "tasks": {
                        "voice_clone": {
                            "total": total_voice_clone,
                            "completed": completed_voice_clone,
                            "success_rate": (
                                round(
                                    completed_voice_clone / total_voice_clone * 100, 1
                                )
                                if total_voice_clone > 0
                                else 0
                            ),
                        },
                        "tts": {
                            "total": total_tts,
                            "completed": completed_tts,
                            "success_rate": (
                                round(completed_tts / total_tts * 100, 1)
                                if total_tts > 0
                                else 0
                            ),
                        },
                    },
                    "models": {
                        "total": total_models,
                        "public": public_models,
                        "total_usage": int(total_model_usage),
                        "total_downloads": int(total_downloads),
                    },
                    "storage": {
                        "total_uploads": total_uploads,
                        "total_size_bytes": int(total_storage),
                        "total_size_mb": round(total_storage / (1024 * 1024), 2),
                    },
                    "monthly_activity": {
                        "voice_clone_tasks": month_voice_clone,
                        "tts_tasks": month_tts,
                    },
                },
            )
        )

    except Exception as e:
        current_app.logger.error(f"Get user statistics error: {e}")
        return (
            jsonify(create_response(False, "Failed to retrieve user statistics")),
            500,
        )


@user_bp.route("/delete-account", methods=["DELETE"])
@auth_required
@rate_limit(requests_per_minute=1)
@log_action("delete_account", "user")
def delete_account():
    """删除用户账户"""
    try:
        user = request.current_user
        data = request.get_json() or {}

        # 确认密码
        password = data.get("password")
        if not password or not user.check_password(password):
            raise ValidationError("Password confirmation required")

        # 检查是否有正在进行的任务
        active_vc_tasks = VoiceCloneTask.query.filter_by(
            user_id=user.id, status="processing"
        ).count()

        active_tts_tasks = TTSTask.query.filter_by(
            user_id=user.id, status="processing"
        ).count()

        if active_vc_tasks > 0 or active_tts_tasks > 0:
            raise ValidationError("Cannot delete account while tasks are processing")

        # 删除用户数据
        # 1. 标记上传文件为已删除
        uploads = UserUpload.query.filter_by(user_id=user.id).all()
        for upload in uploads:
            upload.mark_deleted()

        # 2. 将用户模型设为非活跃
        models = VoiceModel.query.filter_by(owner_id=user.id).all()
        for model in models:
            model.status = "inactive"
            model.is_public = False

        # 3. 停用用户账户（软删除）
        user.is_active = False
        user.username = f"deleted_user_{user.id}"
        user.email = f"deleted_{user.id}@deleted.local"

        db.session.commit()

        return jsonify(
            create_response(success=True, message="Account deleted successfully")
        )

    except ValidationError as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Delete account error: {e}")
        return jsonify(create_response(False, "Failed to delete account")), 500
