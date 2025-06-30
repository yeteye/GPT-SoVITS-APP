# ./gpt-sovits-backend/app/api/emotion_management.py

from flask import Blueprint, request, jsonify, current_app
from app.extensions import db
from app.models.model import VoiceModel
from app.models.emotion import Emotion  # 假设已在 models/emotion.py 定义了对应 ORM
from app.auth.decorators import auth_required, rate_limit, verify_ownership
from app.utils.helpers import create_response
from app.utils.exceptions import ResourceNotFoundError, ValidationError

emotion_bp = Blueprint("emotions", __name__, url_prefix="/models")

# 1. 获取某模型支持的所有情感类型
@emotion_bp.route("/<model_id>/emotions", methods=["GET"])
@auth_required
@rate_limit(requests_per_minute=60)
def list_emotions(model_id):
    """
    GET /models/<model_id>/emotions
    返回格式:
    {
      "success": true,
      "message": "Emotions retrieved successfully",
      "data": {
        "emotions": ["neutral","happy", ...]
      }
    }
    """
    # 验证模型存在
    model = VoiceModel.query.get(model_id)
    if not model:
        raise ResourceNotFoundError("Voice model")
    try:
        rows = Emotion.query.with_entities(Emotion.type).filter_by(model_id=model_id).all()
        types = [r.type for r in rows]
        return jsonify(create_response(
            success=True,
            message="Emotions retrieved successfully",
            data={"emotions": types}
        ))
    except Exception as e:
        current_app.logger.error(f"List emotions error: {e}")
        return jsonify(create_response(False, "Failed to retrieve emotions")), 500


# 2. 根据模型 ID 和情感类型获取参考音频参数
@emotion_bp.route("/<model_id>/emotions/<emotion_type>", methods=["GET"])
@auth_required
@rate_limit(requests_per_minute=60)
def get_emotion_detail(model_id, emotion_type):
    """
    GET /models/<model_id>/emotions/<emotion_type>
    返回格式:
    {
      "success": true,
      "message": "Emotion detail retrieved successfully",
      "data": {
        "model_id": "...",
        "type": "happy",
        "ref_path": "...",
        "ref_lang": "zh",
        "ref_text": "...",
        "description": "..."
      }
    }
    """
    # 验证模型存在
    model = VoiceModel.query.get(model_id)
    if not model:
        raise ResourceNotFoundError("Voice model")
    # 验证 emotion_type 是否有效枚举
    if emotion_type not in Emotion.__table__.columns['type'].type.enums:
        raise ValidationError(f"Emotion type '{emotion_type}' is not supported")
    try:
        emo = Emotion.query.filter_by(model_id=model_id, type=emotion_type).first()
        if not emo:
            raise ResourceNotFoundError(f"Emotion '{emotion_type}' for model '{model_id}'")
        detail = {
            "model_id": emo.model_id,
            "type": emo.type,
            "ref_path": emo.ref_path,
            "ref_lang": emo.ref_lang,
            "ref_text": emo.ref_text,
            "description": emo.description,
        }
        return jsonify(create_response(
            success=True,
            message="Emotion detail retrieved successfully",
            data=detail
        ))
    except (ResourceNotFoundError, ValidationError) as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Get emotion detail error: {e}")
        return jsonify(create_response(False, "Failed to retrieve emotion detail")), 500
