# ./gpt-sovits-backend/app/api/__init__.py
from app.api.voice_clone import voice_clone_bp
from app.api.tts import tts_bp
from app.api.model_management import model_bp
from app.api.admin import admin_bp
from app.api.user import user_bp

__all__ = ["voice_clone_bp", "tts_bp", "model_bp", "admin_bp", "user_bp"]
