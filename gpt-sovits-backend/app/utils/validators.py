# ./gpt-sovits-backend/app/utils/validators.py (修改后的版本)
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
        raise ValidationError("File size exceeds maximum limit", "audio_file")

    if file_size < 1024:  # 至少1KB
        raise ValidationError("File is too small", "audio_file")

    return True


def validate_model_file(file, expected_type=None):
    """验证模型文件 - 修改：支持GPT(.pth)和SoVITS(.ckpt)文件"""
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

    # 如果指定了期望的文件类型，进行验证
    if expected_type:
        if expected_type == "gpt" and ext != "pth":
            raise ValidationError(
                "GPT model file must be .pth format", "gpt_model_file"
            )
        elif expected_type == "sovits" and ext != "ckpt":
            raise ValidationError(
                "SoVITS model file must be .ckpt format", "sovits_model_file"
            )

    # 检查文件大小（模型文件通常较大）
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > current_app.config["MAX_CONTENT_LENGTH"]:
        raise ValidationError("Model file size exceeds maximum limit", "model_file")

    if file_size < 1024 * 1024:  # 至少1MB（模型文件应该比较大）
        raise ValidationError("Model file seems too small", "model_file")

    return True


def validate_language_support(languages):
    """验证支持的语言列表 - 新增：验证语言支持"""
    if not languages:
        raise ValidationError(
            "At least one language must be supported", "supported_languages"
        )

    if not isinstance(languages, (list, tuple)):
        raise ValidationError(
            "Languages must be provided as a list", "supported_languages"
        )

    # 获取支持的语言列表
    supported_languages = current_app.config.get("SUPPORTED_LANGUAGES", {})
    valid_language_codes = list(supported_languages.keys())

    for lang in languages:
        if lang not in valid_language_codes:
            raise ValidationError(
                f'Unsupported language: {lang}. Supported languages: {", ".join(valid_language_codes)}',
                "supported_languages",
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


def validate_model_upload_data(data, gpt_file=None, sovits_file=None):
    """验证模型上传数据 - 修复：统一要求必须上传两个文件"""
    # 验证必需字段
    required_fields = ["name", "description"]
    for field in required_fields:
        if not data.get(field):
            raise ValidationError(f"{field} is required", field)

    # 验证模型名称
    validate_model_name(data["name"])

    # 修复：始终要求两个文件都存在
    if not gpt_file:
        raise ValidationError("GPT模型文件(.pth)是必需的", "gpt_model_file")
    if not sovits_file:
        raise ValidationError("SoVITS模型文件(.ckpt)是必需的", "sovits_model_file")

    # 验证文件
    validate_model_file(gpt_file, expected_type="gpt")
    validate_model_file(sovits_file, expected_type="sovits")

    # 验证支持的语言
    supported_languages = data.get("supported_languages", ["zh-CN"])
    validate_language_support(supported_languages)

    # 验证支持的情感（可选）
    supported_emotions = data.get("supported_emotions", ["neutral"])
    if supported_emotions:
        for emotion in supported_emotions:
            validate_emotion(emotion)

    return True


def sanitize_filename(filename):
    """清理文件名"""
    # 移除不安全字符
    filename = re.sub(r"[^\w\s.-]", "", filename.strip())
    # 限制长度
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[: 255 - len(ext)] + ext
    return filename


def validate_watermark_code_length(code_length):
    """验证水印码长度"""
    if not isinstance(code_length, int):
        try:
            code_length = int(code_length)
        except (ValueError, TypeError):
            raise ValidationError("Code length must be a valid integer")

    if code_length not in [8, 16, 32]:
        raise ValidationError("Code length must be 8, 16, or 32")

    return code_length


def validate_watermark_description(description):
    """验证水印描述"""
    if description is not None:
        description = str(description).strip()
        if len(description) > 500:
            raise ValidationError("Description must be less than 500 characters")
    return description


def validate_file_pair(gpt_file, sovits_file, model_name):
    """验证文件对 - 修复：确保两个文件都存在"""
    if not gpt_file:
        raise ValidationError("GPT模型文件(.pth)是必需的", "gpt_model_file")

    if not sovits_file:
        raise ValidationError("SoVITS模型文件(.ckpt)是必需的", "sovits_model_file")

    # 验证文件名匹配（可选，确保文件是配对的）
    if gpt_file and sovits_file and model_name:
        expected_gpt = f"{model_name}.pth"
        expected_sovits = f"{model_name}.ckpt"

        if gpt_file.filename != expected_gpt:
            current_app.logger.warning(
                f"GPT file name mismatch: expected {expected_gpt}, got {gpt_file.filename}"
            )

        if sovits_file.filename != expected_sovits:
            current_app.logger.warning(
                f"SoVITS file name mismatch: expected {expected_sovits}, got {sovits_file.filename}"
            )

    return True
