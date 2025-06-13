# ./gpt-sovits-backend/app/api/voice_clone.py
from flask import Blueprint, request, jsonify, current_app
from app.extensions import db
from app.models.task import VoiceCloneTask
from app.models.model import VoiceModel
from app.models.audit import UserUpload
from app.auth.decorators import auth_required, rate_limit, log_action
from app.utils.validators import (
    validate_audio_file,
    validate_model_name,
    validate_pagination,
)
from app.utils.audio_utils import validate_audio_content, convert_to_standard_format
from app.utils.helpers import (
    save_uploaded_file,
    create_response,
    paginate_query,
    calculate_estimated_time,
    log_user_action,
)
from app.utils.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    ServiceUnavailableError,
)
from app.services.voice_clone_service import start_voice_clone_task
import os

voice_clone_bp = Blueprint("voice_clone", __name__)


@voice_clone_bp.route("/upload-sample", methods=["POST"])
@auth_required
@rate_limit(requests_per_minute=10)
@log_action("upload_audio_sample", "audio_sample")
def upload_audio_sample():
    """上传音频样本"""
    try:
        user = request.current_user

        # 检查是否有文件上传
        if "audio_file" not in request.files:
            raise ValidationError("No audio file provided", "audio_file")

        file = request.files["audio_file"]

        # 验证文件
        validate_audio_file(file)

        # 保存文件
        file_info = save_uploaded_file(file, "audio_samples", f"user_{user.id}")

        # 验证音频内容
        audio_info = validate_audio_content(file_info["file_path"])

        # 转换为标准格式
        standard_path = file_info["file_path"].replace(".", "_standard.")
        if file_info["file_path"].lower().endswith(".wav"):
            standard_path = file_info["file_path"]
        else:
            convert_to_standard_format(file_info["file_path"], standard_path)

        # 记录上传信息
        upload_record = UserUpload(
            user_id=user.id,
            filename=file_info["filename"],
            original_filename=file.filename,
            file_path=standard_path,
            file_size=file_info["size"],
            file_type="audio",
            mime_type=file.content_type,
        )
        upload_record.set_metadata(audio_info)

        db.session.add(upload_record)
        db.session.commit()

        return (
            jsonify(
                create_response(
                    success=True,
                    message="Audio sample uploaded successfully",
                    data={
                        "upload_id": upload_record.id,
                        "filename": upload_record.filename,
                        "duration": audio_info["duration"],
                        "sample_rate": audio_info["sample_rate"],
                        "file_size": file_info["size"],
                    },
                )
            ),
            201,
        )

    except ValidationError as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Upload audio sample error: {e}")
        return jsonify(create_response(False, "Upload failed")), 500


@voice_clone_bp.route("/start-training", methods=["POST"])
@auth_required
@rate_limit(requests_per_minute=3)
@log_action("start_voice_clone_training", "voice_clone_task")
def start_training():
    """启动音色克隆训练"""
    try:
        user = request.current_user
        data = request.get_json()

        if not data:
            raise ValidationError("Request body is required")

        # 验证必需字段
        model_name = data.get("model_name", "").strip()
        sample_ids = data.get("sample_ids", [])

        if not model_name:
            raise ValidationError("Model name is required", "model_name")

        if not sample_ids or len(sample_ids) < 3:
            raise ValidationError("At least 3 audio samples are required", "sample_ids")

        validate_model_name(model_name)

        # 检查模型名称是否已存在
        existing_model = VoiceModel.query.filter_by(
            name=model_name, owner_id=user.id
        ).first()

        if existing_model:
            raise ValidationError("Model name already exists", "model_name")

        # 验证样本是否属于当前用户
        samples = UserUpload.query.filter(
            UserUpload.id.in_(sample_ids),
            UserUpload.user_id == user.id,
            UserUpload.file_type == "audio",
            UserUpload.is_deleted == False,
        ).all()

        if len(samples) != len(sample_ids):
            raise ValidationError("Some audio samples not found or invalid")

        # 计算总时长
        total_duration = 0
        sample_paths = []

        for sample in samples:
            metadata = sample.get_metadata()
            total_duration += metadata.get("duration", 0)
            sample_paths.append(sample.file_path)

        # 检查时长要求
        if total_duration < 30:  # 至少30秒
            raise ValidationError("Total audio duration must be at least 30 seconds")

        if total_duration > 600:  # 最多10分钟
            raise ValidationError("Total audio duration must not exceed 10 minutes")

        # 创建训练任务
        task = VoiceCloneTask(
            user_id=user.id,
            task_name=model_name,
            sample_count=len(samples),
            total_duration=total_duration,
            model_name=model_name,
            estimated_completion=calculate_estimated_time(
                "voice_clone", sample_count=len(samples), total_duration=total_duration
            ),
        )

        task.set_audio_samples(sample_paths)
        task.set_config(
            {
                "model_name": model_name,
                "training_params": data.get("training_params", {}),
                "sample_ids": sample_ids,
            }
        )

        db.session.add(task)
        db.session.commit()

        # 启动异步训练任务
        celery_task = start_voice_clone_task.delay(task.id)
        task.celery_task_id = celery_task.id
        db.session.commit()

        return (
            jsonify(
                create_response(
                    success=True,
                    message="Voice clone training started",
                    data={
                        "task_id": task.id,
                        "status": task.status,
                        "estimated_completion": task.estimated_completion.isoformat(),
                        "sample_count": task.sample_count,
                        "total_duration": task.total_duration,
                    },
                )
            ),
            201,
        )

    except ValidationError as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Start training error: {e}")
        return jsonify(create_response(False, "Failed to start training")), 500


@voice_clone_bp.route("/tasks", methods=["GET"])
@auth_required
@rate_limit(requests_per_minute=30)
def get_user_tasks():
    """获取用户的音色克隆任务列表"""
    try:
        user = request.current_user

        # 分页参数
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        status = request.args.get("status")

        page, per_page = validate_pagination(page, per_page)

        # 构建查询
        query = VoiceCloneTask.query.filter_by(user_id=user.id)

        if status:
            query = query.filter_by(status=status)

        # 按创建时间倒序排列
        query = query.order_by(VoiceCloneTask.created_at.desc())

        # 分页
        pagination = paginate_query(query, page, per_page)

        return jsonify(
            create_response(
                success=True,
                message="Tasks retrieved successfully",
                data={
                    "tasks": [task.to_dict() for task in pagination["items"]],
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
        current_app.logger.error(f"Get tasks error: {e}")
        return jsonify(create_response(False, "Failed to retrieve tasks")), 500


@voice_clone_bp.route("/tasks/<task_id>", methods=["GET"])
@auth_required
@rate_limit(requests_per_minute=60)
def get_task_detail(task_id):
    """获取任务详情"""
    try:
        user = request.current_user

        task = VoiceCloneTask.query.filter_by(id=task_id, user_id=user.id).first()

        if not task:
            raise ResourceNotFoundError("Task")

        return jsonify(
            create_response(
                success=True,
                message="Task details retrieved successfully",
                data={"task": task.to_dict()},
            )
        )

    except ResourceNotFoundError as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Get task detail error: {e}")
        return jsonify(create_response(False, "Failed to retrieve task details")), 500


@voice_clone_bp.route("/tasks/<task_id>/cancel", methods=["POST"])
@auth_required
@rate_limit(requests_per_minute=10)
@log_action("cancel_voice_clone_task", "voice_clone_task")
def cancel_task(task_id):
    """取消训练任务"""
    try:
        user = request.current_user

        task = VoiceCloneTask.query.filter_by(id=task_id, user_id=user.id).first()

        if not task:
            raise ResourceNotFoundError("Task")

        if task.status not in ["pending", "processing"]:
            raise ValidationError("Task cannot be cancelled in current status")

        # 取消Celery任务
        if task.celery_task_id:
            from app.extensions import celery

            celery.control.revoke(task.celery_task_id, terminate=True)

        # 更新任务状态
        task.update_status("failed", error_message="Cancelled by user")

        return jsonify(
            create_response(success=True, message="Task cancelled successfully")
        )

    except (ResourceNotFoundError, ValidationError) as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Cancel task error: {e}")
        return jsonify(create_response(False, "Failed to cancel task")), 500


@voice_clone_bp.route("/tasks/<task_id>/result", methods=["GET"])
@auth_required
@rate_limit(requests_per_minute=30)
def get_task_result(task_id):
    """获取训练结果"""
    try:
        user = request.current_user

        task = VoiceCloneTask.query.filter_by(id=task_id, user_id=user.id).first()

        if not task:
            raise ResourceNotFoundError("Task")

        if task.status != "completed":
            return (
                jsonify(
                    create_response(
                        success=False,
                        message=f"Task is not completed. Current status: {task.status}",
                    )
                ),
                400,
            )

        if not task.result_model_id:
            raise ValidationError("No model generated for this task")

        # 获取生成的模型
        model = VoiceModel.query.get(task.result_model_id)

        if not model:
            raise ResourceNotFoundError("Generated model")

        return jsonify(
            create_response(
                success=True,
                message="Training result retrieved successfully",
                data={"task": task.to_dict(), "model": model.to_dict()},
            )
        )

    except (ResourceNotFoundError, ValidationError) as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Get task result error: {e}")
        return jsonify(create_response(False, "Failed to retrieve task result")), 500


@voice_clone_bp.route("/samples", methods=["GET"])
@auth_required
@rate_limit(requests_per_minute=30)
def get_user_samples():
    """获取用户的音频样本列表"""
    try:
        user = request.current_user

        # 分页参数
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)

        page, per_page = validate_pagination(page, per_page)

        # 查询用户的音频样本
        query = UserUpload.query.filter_by(
            user_id=user.id, file_type="audio", is_deleted=False
        ).order_by(UserUpload.created_at.desc())

        # 分页
        pagination = paginate_query(query, page, per_page)

        return jsonify(
            create_response(
                success=True,
                message="Audio samples retrieved successfully",
                data={
                    "samples": [sample.to_dict() for sample in pagination["items"]],
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
        current_app.logger.error(f"Get samples error: {e}")
        return jsonify(create_response(False, "Failed to retrieve samples")), 500


@voice_clone_bp.route("/samples/<sample_id>", methods=["DELETE"])
@auth_required
@rate_limit(requests_per_minute=20)
@log_action("delete_audio_sample", "audio_sample")
def delete_sample(sample_id):
    """删除音频样本"""
    try:
        user = request.current_user

        sample = UserUpload.query.filter_by(
            id=sample_id, user_id=user.id, file_type="audio"
        ).first()

        if not sample:
            raise ResourceNotFoundError("Audio sample")

        # 检查样本是否正在被使用
        active_task = VoiceCloneTask.query.filter(
            VoiceCloneTask.user_id == user.id,
            VoiceCloneTask.status.in_(["pending", "processing"]),
        ).first()

        if active_task:
            # 检查样本是否在任务中
            sample_paths = active_task.get_audio_samples()
            if sample.file_path in sample_paths:
                raise ValidationError(
                    "Cannot delete sample while it is being used in training"
                )

        # 标记为已删除（软删除）
        sample.mark_deleted()

        # 可选：删除物理文件
        try:
            if os.path.exists(sample.file_path):
                os.remove(sample.file_path)
        except Exception as e:
            current_app.logger.warning(f"Failed to delete physical file: {e}")

        return jsonify(
            create_response(success=True, message="Audio sample deleted successfully")
        )

    except (ResourceNotFoundError, ValidationError) as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Delete sample error: {e}")
        return jsonify(create_response(False, "Failed to delete sample")), 500


@voice_clone_bp.route("/tasks/<task_id>/retry", methods=["POST"])
@auth_required
@rate_limit(requests_per_minute=5)
@log_action("retry_voice_clone_task", "voice_clone_task")
def retry_task(task_id):
    """重试失败的任务"""
    try:
        user = request.current_user

        task = VoiceCloneTask.query.filter_by(id=task_id, user_id=user.id).first()

        if not task:
            raise ResourceNotFoundError("Task")

        if not task.can_be_retried():
            raise ValidationError("Task cannot be retried")

        # 重置任务状态
        task.status = "pending"
        task.progress = 0
        task.error_message = None
        task.started_at = None
        task.completed_at = None
        task.celery_task_id = None

        db.session.commit()

        # 重新启动任务
        celery_task = start_voice_clone_task.delay(task.id)
        task.celery_task_id = celery_task.id
        db.session.commit()

        return jsonify(
            create_response(
                success=True,
                message="Task restarted successfully",
                data={"task": task.to_dict()},
            )
        )

    except (ResourceNotFoundError, ValidationError) as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Retry task error: {e}")
        return jsonify(create_response(False, "Failed to retry task")), 500
