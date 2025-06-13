# ./gpt-sovits-backend/app/api/tts.py
from flask import Blueprint, request, jsonify, current_app, send_file
from app.extensions import db
from app.models.task import TTSTask
from app.models.model import VoiceModel
from app.auth.decorators import auth_required, rate_limit, log_action
from app.utils.validators import (
    validate_text_length,
    validate_emotion,
    validate_speed,
    validate_pagination,
)
from app.utils.helpers import (
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
from app.services.tts_service import generate_speech_task
import os

tts_bp = Blueprint("tts", __name__)


@tts_bp.route("/generate", methods=["POST"])
@auth_required
@rate_limit(requests_per_minute=20)
@log_action("generate_speech", "tts_task")
def generate_speech():
    """生成语音"""
    try:
        user = request.current_user
        data = request.get_json()

        if not data:
            raise ValidationError("Request body is required")

        # 验证必需字段
        text = data.get("text", "").strip()
        model_id = data.get("model_id", "").strip()
        emotion = data.get("emotion", "neutral").strip()
        speed = data.get("speed", 1.0)

        if not text:
            raise ValidationError("Text is required", "text")

        if not model_id:
            raise ValidationError("Model ID is required", "model_id")

        # 验证输入
        validate_text_length(text, min_length=1, max_length=200, field_name="text")
        validate_emotion(emotion)
        validate_speed(speed)

        # 验证模型存在且可用
        model = VoiceModel.query.get(model_id)

        if not model:
            raise ResourceNotFoundError("Voice model")

        if model.status != "active":
            raise ValidationError("Model is not available for use")

        # 检查模型权限
        if not model.is_public and model.owner_id != user.id:
            raise ValidationError("You do not have permission to use this model")

        # 检查模型是否支持指定情感
        supported_emotions = model.get_supported_emotions()
        if emotion not in supported_emotions:
            raise ValidationError(
                f'Model does not support emotion: {emotion}. Supported: {", ".join(supported_emotions)}'
            )

        # 检查并发任务限制
        active_tasks = TTSTask.query.filter_by(
            user_id=user.id, status="processing"
        ).count()

        max_concurrent = current_app.config.get("MAX_CONCURRENT_TASKS", 5)
        if active_tasks >= max_concurrent:
            raise ServiceUnavailableError(
                f"Maximum concurrent tasks ({max_concurrent}) exceeded"
            )

        # 创建TTS任务
        task = TTSTask(
            user_id=user.id, text=text, model_id=model_id, emotion=emotion, speed=speed
        )

        db.session.add(task)
        db.session.commit()

        # 启动异步生成任务
        celery_task = generate_speech_task.delay(task.id)
        task.celery_task_id = celery_task.id
        db.session.commit()

        # 增加模型使用次数
        model.increment_usage()

        return (
            jsonify(
                create_response(
                    success=True,
                    message="Speech generation started",
                    data={
                        "task_id": task.id,
                        "status": task.status,
                        "text": task.text,
                        "model_id": task.model_id,
                        "emotion": task.emotion,
                        "speed": task.speed,
                    },
                )
            ),
            201,
        )

    except (ValidationError, ResourceNotFoundError, ServiceUnavailableError) as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Generate speech error: {e}")
        return jsonify(create_response(False, "Speech generation failed")), 500


@tts_bp.route("/tasks", methods=["GET"])
@auth_required
@rate_limit(requests_per_minute=30)
def get_tts_tasks():
    """获取用户的TTS任务列表"""
    try:
        user = request.current_user

        # 分页参数
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        status = request.args.get("status")

        page, per_page = validate_pagination(page, per_page)

        # 构建查询
        query = TTSTask.query.filter_by(user_id=user.id)

        if status:
            query = query.filter_by(status=status)

        # 按创建时间倒序排列
        query = query.order_by(TTSTask.created_at.desc())

        # 分页
        pagination = paginate_query(query, page, per_page)

        return jsonify(
            create_response(
                success=True,
                message="TTS tasks retrieved successfully",
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
        current_app.logger.error(f"Get TTS tasks error: {e}")
        return jsonify(create_response(False, "Failed to retrieve TTS tasks")), 500


@tts_bp.route("/tasks/<task_id>", methods=["GET"])
@auth_required
@rate_limit(requests_per_minute=60)
def get_tts_task_detail(task_id):
    """获取TTS任务详情"""
    try:
        user = request.current_user

        task = TTSTask.query.filter_by(id=task_id, user_id=user.id).first()

        if not task:
            raise ResourceNotFoundError("TTS task")

        task_data = task.to_dict()

        # 如果有关联模型，添加模型信息
        if task.model:
            task_data["model"] = task.model.to_dict()

        return jsonify(
            create_response(
                success=True,
                message="TTS task details retrieved successfully",
                data={"task": task_data},
            )
        )

    except ResourceNotFoundError as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Get TTS task detail error: {e}")
        return (
            jsonify(create_response(False, "Failed to retrieve TTS task details")),
            500,
        )


@tts_bp.route("/tasks/<task_id>/download", methods=["GET"])
@auth_required
@rate_limit(requests_per_minute=30)
def download_audio(task_id):
    """下载生成的音频"""
    try:
        user = request.current_user

        task = TTSTask.query.filter_by(id=task_id, user_id=user.id).first()

        if not task:
            raise ResourceNotFoundError("TTS task")

        if task.status != "completed":
            raise ValidationError("Task is not completed yet")

        if not task.audio_path or not os.path.exists(task.audio_path):
            raise ResourceNotFoundError("Audio file")

        # 记录下载日志
        log_user_action(
            user_id=user.id,
            action="download_generated_audio",
            resource_type="tts_task",
            resource_id=task.id,
            details=f"Downloaded audio for task {task.id}",
        )

        return send_file(
            task.audio_path,
            as_attachment=True,
            download_name=f"generated_speech_{task.id}.wav",
            mimetype="audio/wav",
        )

    except (ResourceNotFoundError, ValidationError) as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Download audio error: {e}")
        return jsonify(create_response(False, "Failed to download audio")), 500


@tts_bp.route("/models", methods=["GET"])
@auth_required
@rate_limit(requests_per_minute=30)
def get_available_models():
    """获取可用的语音模型列表"""
    try:
        user = request.current_user

        # 分页参数
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        model_type = request.args.get("type")  # official, user_trained
        featured = request.args.get("featured", type=bool)

        page, per_page = validate_pagination(page, per_page)

        # 构建查询：公开模型 + 用户自己的模型
        query = VoiceModel.query.filter(
            (VoiceModel.is_public == True) | (VoiceModel.owner_id == user.id),
            VoiceModel.status == "active",
        )

        if model_type:
            query = query.filter_by(model_type=model_type)

        if featured is not None:
            query = query.filter_by(is_featured=featured)

        # 按创建时间倒序排列
        query = query.order_by(VoiceModel.created_at.desc())

        # 分页
        pagination = paginate_query(query, page, per_page)

        return jsonify(
            create_response(
                success=True,
                message="Available models retrieved successfully",
                data={
                    "models": [model.to_dict() for model in pagination["items"]],
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
        current_app.logger.error(f"Get available models error: {e}")
        return jsonify(create_response(False, "Failed to retrieve models")), 500


@tts_bp.route("/models/<model_id>", methods=["GET"])
@auth_required
@rate_limit(requests_per_minute=60)
def get_model_detail(model_id):
    """获取模型详情"""
    try:
        user = request.current_user

        model = VoiceModel.query.get(model_id)

        if not model:
            raise ResourceNotFoundError("Voice model")

        # 检查访问权限
        if not model.is_public and model.owner_id != user.id:
            raise ValidationError("You do not have permission to view this model")

        return jsonify(
            create_response(
                success=True,
                message="Model details retrieved successfully",
                data={"model": model.to_dict()},
            )
        )

    except (ResourceNotFoundError, ValidationError) as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Get model detail error: {e}")
        return jsonify(create_response(False, "Failed to retrieve model details")), 500


@tts_bp.route("/emotions", methods=["GET"])
@rate_limit(requests_per_minute=100)
def get_supported_emotions():
    """获取支持的情感列表"""
    try:
        emotions = [
            {
                "value": "neutral",
                "label": "Neutral",
                "description": "Natural, calm voice",
            },
            {"value": "happy", "label": "Happy", "description": "Joyful, upbeat voice"},
            {
                "value": "sad",
                "label": "Sad",
                "description": "Melancholic, sorrowful voice",
            },
            {
                "value": "angry",
                "label": "Angry",
                "description": "Fierce, aggressive voice",
            },
            {
                "value": "surprised",
                "label": "Surprised",
                "description": "Amazed, shocked voice",
            },
            {
                "value": "disgusted",
                "label": "Disgusted",
                "description": "Repulsed, revolted voice",
            },
            {
                "value": "fearful",
                "label": "Fearful",
                "description": "Scared, anxious voice",
            },
            {
                "value": "calm",
                "label": "Calm",
                "description": "Peaceful, relaxed voice",
            },
            {
                "value": "excited",
                "label": "Excited",
                "description": "Energetic, enthusiastic voice",
            },
        ]

        return jsonify(
            create_response(
                success=True,
                message="Supported emotions retrieved successfully",
                data={"emotions": emotions},
            )
        )

    except Exception as e:
        current_app.logger.error(f"Get emotions error: {e}")
        return jsonify(create_response(False, "Failed to retrieve emotions")), 500
