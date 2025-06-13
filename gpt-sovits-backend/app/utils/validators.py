# ./gpt-sovits-backend/app/utils/validators.py
import re
import os
from werkzeug.utils import secure_filename
from flask import current_app
from app.utils.exceptions import ValidationError


def validate_email(email):
    """验证邮箱格式"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        raise ValidationError("Invalid email format", "email")
    return True


def validate_username(username):
    """验证用户名格式"""
    if not username or len(username) < 3 or len(username) > 50:
        raise ValidationError("Username must be 3-50 characters long", "username")

    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        raise ValidationError(
            "Username can only contain letters, numbers, underscore and hyphen",
            "username",
        )

    return True


def validate_password(password):
    """验证密码强度"""
    if not password or len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long", "password")

    if not re.search(r"[A-Z]", password):
        raise ValidationError(
            "Password must contain at least one uppercase letter", "password"
        )

    if not re.search(r"[a-z]", password):
        raise ValidationError(
            "Password must contain at least one lowercase letter", "password"
        )

    if not re.search(r"\d", password):
        raise ValidationError("Password must contain at least one number", "password")

    return True


def validate_text_length(text, min_length=1, max_length=200, field_name="text"):
    """验证文本长度"""
    if not text or len(text.strip()) < min_length:
        raise ValidationError(
            f"{field_name} must be at least {min_length} characters long", field_name
        )

    if len(text) > max_length:
        raise ValidationError(
            f"{field_name} must not exceed {max_length} characters", field_name
        )

    return True


def validate_audio_file(file):
    """验证音频文件"""
    if not file or not file.filename:
        raise ValidationError("No audio file provided", "audio_file")

    # 检查文件扩展名
    filename = secure_filename(file.filename)
    if "." not in filename:
        raise ValidationError("File must have an extension", "audio_file")

    ext = filename.rsplit(".", 1)[1].lower()
    if ext not in current_app.config["ALLOWED_AUDIO_EXTENSIONS"]:
        raise ValidationError(
            f'Unsupported audio format. Allowed: {", ".join(current_app.config["ALLOWED_AUDIO_EXTENSIONS"])}',
            "audio_file",
        )

    # 检查文件大小
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > current_app.config["MAX_CONTENT_LENGTH"]:
        raise ValidationError("File size exceeds 10MB limit", "audio_file")

    if file_size < 1024:  # 至少1KB
        raise ValidationError("File is too small", "audio_file")

    return True


def validate_model_file(file):
    """验证模型文件"""
    if not file or not file.filename:
        raise ValidationError("No model file provided", "model_file")

    filename = secure_filename(file.filename)
    if "." not in filename:
        raise ValidationError("File must have an extension", "model_file")

    ext = filename.rsplit(".", 1)[1].lower()
    if ext not in current_app.config["ALLOWED_MODEL_EXTENSIONS"]:
        raise ValidationError(
            f'Unsupported model format. Allowed: {", ".join(current_app.config["ALLOWED_MODEL_EXTENSIONS"])}',
            "model_file",
        )

    return True


def validate_emotion(emotion):
    """验证情感参数"""
    allowed_emotions = [
        "neutral",
        "happy",
        "sad",
        "angry",
        "surprised",
        "disgusted",
        "fearful",
        "calm",
        "excited",
    ]
    if emotion not in allowed_emotions:
        raise ValidationError(
            f'Invalid emotion. Allowed: {", ".join(allowed_emotions)}', "emotion"
        )
    return True


def validate_speed(speed):
    """验证语速参数"""
    if not isinstance(speed, (int, float)):
        raise ValidationError("Speed must be a number", "speed")

    if speed < 0.5 or speed > 2.0:
        raise ValidationError("Speed must be between 0.5 and 2.0", "speed")

    return True


def validate_role(role):
    """验证用户角色"""
    if role not in [0, 1, 2]:
        raise ValidationError(
            "Invalid role. Must be 0 (user), 1 (auditor), or 2 (admin)", "role"
        )
    return True


def validate_model_name(name):
    """验证模型名称"""
    if not name or len(name.strip()) < 1:
        raise ValidationError("Model name is required", "model_name")

    if len(name) > 100:
        raise ValidationError("Model name must not exceed 100 characters", "model_name")

    # 只允许字母、数字、下划线、连字符和空格
    if not re.match(r"^[a-zA-Z0-9_\-\s\u4e00-\u9fff]+$", name):
        raise ValidationError("Model name contains invalid characters", "model_name")

    return True


def validate_pagination(page, per_page):
    """验证分页参数"""
    try:
        page = int(page) if page else 1
        per_page = (
            int(per_page) if per_page else current_app.config.get("ITEMS_PER_PAGE", 20)
        )
    except (ValueError, TypeError):
        raise ValidationError("Invalid pagination parameters", "pagination")

    if page < 1:
        raise ValidationError("Page number must be positive", "page")

    if per_page < 1 or per_page > 100:
        raise ValidationError("Items per page must be between 1 and 100", "per_page")

    return page, per_page


def sanitize_filename(filename):
    """清理文件名"""
    # 移除不安全字符
    filename = re.sub(r"[^\w\s.-]", "", filename.strip())
    # 限制长度
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[: 255 - len(ext)] + ext
    return filename
