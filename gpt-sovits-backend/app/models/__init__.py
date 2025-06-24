# ./gpt-sovits-backend/app/models/__init__.py (更新版本)
from app.models.user import User, AuthToken
from app.models.task import VoiceCloneTask, TTSTask
from app.models.model import VoiceModel, Tag
from app.models.audit import AuditLog, UserUpload
from app.models.watermark import Watermark, WatermarkVerificationLog  # 新增水印模型

__all__ = [
    "User",
    "AuthToken",
    "VoiceCloneTask",
    "TTSTask",
    "VoiceModel",
    "Tag",
    "AuditLog",
    "UserUpload",
    "Watermark",  # 新增
    "WatermarkVerificationLog",  # 新增
]
