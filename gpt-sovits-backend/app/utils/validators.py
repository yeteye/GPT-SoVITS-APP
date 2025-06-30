# ./gpt-sovits-backend/app/utils/validators.py (修复版)
import re
import os
from werkzeug.utils import secure_filename
from flask import current_app
from app.utils.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


def validate_email(email):
    """验证邮箱格式 - 改进版本"""
    if not email or not isinstance(email, str):
        raise ValidationError("Email must be a non-empty string", "email")

    email = email.strip().lower()

    if len(email) > 254:  # RFC 5321 限制
        raise ValidationError("Email address too long", "email")

    # 改进的邮箱正则表达式
    pattern = r"^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"

    if not re.match(pattern, email):
        raise ValidationError("Invalid email format", "email")

    # 检查常见的无效域名
    invalid_domains = ["example.com", "test.com", "localhost"]
    domain = email.split("@")[1]
    if domain in invalid_domains:
        raise ValidationError("Invalid email domain", "email")

    return email


def validate_username(username):
    """验证用户名格式 - 改进版本"""
    if not username or not isinstance(username, str):
        raise ValidationError("Username must be a non-empty string", "username")

    username = username.strip()

    if len(username) < 3 or len(username) > 50:
        raise ValidationError("Username must be 3-50 characters long", "username")

    # 改进的用户名验证：支持中文
    if not re.match(r"^[a-zA-Z0-9_\-\u4e00-\u9fff]+$", username):
        raise ValidationError(
            "Username can only contain letters, numbers, underscore, hyphen, and Chinese characters",
            "username",
        )

    # 检查保留用户名
    reserved_names = {
        "admin",
        "administrator",
        "root",
        "system",
        "api",
        "www",
        "mail",
        "ftp",
        "ssh",
        "support",
        "help",
        "service",
        "null",
        "undefined",
        "test",
        "demo",
        "guest",
        "anonymous",
        "user",
        "public",
        "private",
    }

    if username.lower() in reserved_names:
        raise ValidationError("Username is reserved", "username")

    # 检查是否全为数字（通常不是好的用户名）
    if username.isdigit():
        raise ValidationError("Username cannot be all numbers", "username")

    return username


def validate_password(password):
    """验证密码强度 - 改进版本"""
    if not password or not isinstance(password, str):
        raise ValidationError("Password must be a non-empty string", "password")

    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long", "password")

    if len(password) > 128:
        raise ValidationError("Password cannot exceed 128 characters", "password")

    # 检查字符类型
    has_upper = bool(re.search(r"[A-Z]", password))
    has_lower = bool(re.search(r"[a-z]", password))
    has_digit = bool(re.search(r"\d", password))
    has_special = bool(re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password))

    missing_types = []
    if not has_upper:
        missing_types.append("uppercase letter")
    if not has_lower:
        missing_types.append("lowercase letter")
    if not has_digit:
        missing_types.append("number")
    if not has_special:
        missing_types.append("special character")

    if len(missing_types) > 1:
        raise ValidationError(
            f"Password must contain at least: {', '.join(missing_types)}", "password"
        )

    # 检查常见弱密码
    weak_passwords = {
        "password",
        "123456",
        "123456789",
        "qwerty",
        "abc123",
        "password123",
        "admin",
        "letmein",
        "welcome",
        "monkey",
        "dragon",
        "master",
        "hello",
        "login",
        "passw0rd",
        "password1",
        "123123",
        "welcome123",
    }

    if password.lower() in weak_passwords:
        raise ValidationError("Password is too common", "password")

    # 检查重复字符（如：aaaa, 1111）
    if re.search(r"(.)\1{3,}", password):
        raise ValidationError(
            "Password cannot contain 4 or more repeated characters", "password"
        )

    return True


def validate_text_length(text, min_length=1, max_length=200, field_name="text"):
    """验证文本长度 - 改进版本"""
    if text is None:
        raise ValidationError(f"{field_name} is required", field_name)

    if not isinstance(text, str):
        raise ValidationError(f"{field_name} must be a string", field_name)

    # 去除首尾空白字符后检查
    stripped_text = text.strip()

    if len(stripped_text) < min_length:
        raise ValidationError(
            f"{field_name} must be at least {min_length} characters long", field_name
        )

    if len(text) > max_length:  # 使用原始长度（包含空格）
        raise ValidationError(
            f"{field_name} must not exceed {max_length} characters", field_name
        )

    # 检查是否包含恶意内容
    if contains_malicious_content(text):
        raise ValidationError(f"{field_name} contains invalid content", field_name)

    return stripped_text


def contains_malicious_content(text):
    """检查文本是否包含恶意内容"""
    if not isinstance(text, str):
        return False

    # 检查常见的注入攻击模式
    malicious_patterns = [
        r"<script[^>]*>.*?</script>",  # XSS
        r"javascript:",  # JavaScript协议
        r"on\w+\s*=",  # 事件处理器
        r"eval\s*\(",  # eval函数
        r"(?:union|select|insert|update|delete|drop|create|alter)\s+",  # SQL关键字
        r"<!--.*?-->",  # HTML注释（可能包含恶意代码）
    ]

    text_lower = text.lower()
    for pattern in malicious_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
            return True

    return False


def validate_audio_file(file):
    """验证音频文件 - 改进版本"""
    if not file or not file.filename:
        raise ValidationError("No audio file provided", "audio_file")

    # 检查文件名安全性
    filename = secure_filename(file.filename)

    if not filename:
        raise ValidationError("Invalid filename", "audio_file")

    if "." not in filename:
        raise ValidationError("File must have an extension", "audio_file")

    ext = filename.rsplit(".", 1)[1].lower()

    allowed_extensions = current_app.config.get("ALLOWED_AUDIO_EXTENSIONS", set())

    if ext not in allowed_extensions:
        raise ValidationError(
            f'Unsupported audio format. Allowed: {", ".join(sorted(allowed_extensions))}',
            "audio_file",
        )

    # 检查文件大小
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    max_size = current_app.config.get("MAX_CONTENT_LENGTH", 100 * 1024 * 1024)  # 100MB
    if file_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise ValidationError(
            f"File size exceeds {max_size_mb:.1f}MB limit", "audio_file"
        )

    if file_size < 1024:  # 至少1KB
        raise ValidationError(
            "File is too small to be a valid audio file", "audio_file"
        )

    # 检查文件头部魔数（基础检查）
    file_header = file.read(12)
    file.seek(0)

    print(f"File header: {file_header}")

    # if not validate_audio_file_header(file_header, ext):
    #     raise ValidationError(
    #         "File content doesn't match the file extension", "audio_file"
    #     )

    return True


def validate_audio_file_header(header, extension):
    """验证音频文件头部魔数"""
    if len(header) < 4:
        return False

    # 定义常见音频格式的魔数
    magic_numbers = {
        "wav": [b"RIFF"],
        "mp3": [b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"],
        "flac": [b"fLaC"],
        "ogg": [b"OggS"],
        "m4a": [b"ftypM4A"],
        "aac": [b"\xff\xf1", b"\xff\xf9"],
    }

    expected_headers = magic_numbers.get(extension, [])
    if not expected_headers:
        return True  # 如果不知道格式，跳过检查

    for expected in expected_headers:
        if header.startswith(expected):
            return True

    return False


def validate_model_file(file, expected_type=None):
    """验证模型文件 - 改进版本"""
    if not file or not file.filename:
        raise ValidationError("No model file provided", "model_file")

    filename = secure_filename(file.filename)
    if not filename:
        raise ValidationError("Invalid filename", "model_file")

    if "." not in filename:
        raise ValidationError("File must have an extension", "model_file")

    ext = filename.rsplit(".", 1)[1].lower()
    allowed_extensions = current_app.config.get("ALLOWED_MODEL_EXTENSIONS", set())

    if ext not in allowed_extensions:
        raise ValidationError(
            f'Unsupported model format. Allowed: {", ".join(sorted(allowed_extensions))}',
            "model_file",
        )

    # 严格的类型检查
    if expected_type:
        if expected_type == "gpt" and ext != "pth":
            raise ValidationError(
                "GPT model file must be .pth format", "gpt_model_file"
            )
        elif expected_type == "sovits" and ext != "ckpt":
            raise ValidationError(
                "SoVITS model file must be .ckpt format", "sovits_model_file"
            )

    # 检查文件大小
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    max_size = current_app.config.get("MAX_CONTENT_LENGTH", 1024 * 1024 * 1024)
    if file_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise ValidationError(
            f"Model file size exceeds {max_size_mb:.1f}MB limit", "model_file"
        )

    min_size = 1024 * 1024  # 至少1MB
    if file_size < min_size:
        raise ValidationError("Model file seems too small to be valid", "model_file")

    return True


def validate_emotion(emotion):
    """验证情感参数 - 改进版本"""
    if not emotion or not isinstance(emotion, str):
        raise ValidationError("Emotion must be a non-empty string", "emotion")

    emotion = emotion.strip().lower()

    # 扩展的情感列表
    allowed_emotions = {
        "neutral",
        "happy",
        "sad",
        "angry",
        "surprised",
        "disgusted",
        "fearful",
        "calm",
        "excited",
        "confident",
        "gentle",
        "cheerful",
        "melancholy",
        "energetic",
        "peaceful",
        "passionate",
        "serious",
        "playful",
        "romantic",
        "mysterious",
    }

    if emotion not in allowed_emotions:
        raise ValidationError(
            f'Invalid emotion. Allowed: {", ".join(sorted(allowed_emotions))}',
            "emotion",
        )

    return emotion


def validate_speed(speed):
    """验证语速参数 - 改进版本"""
    if speed is None:
        raise ValidationError("Speed is required", "speed")

    try:
        speed = float(speed)
    except (ValueError, TypeError):
        raise ValidationError("Speed must be a number", "speed")

    if speed < 0.25 or speed > 3.0:
        raise ValidationError("Speed must be between 0.25 and 3.0", "speed")

    return speed


def validate_role(role):
    """验证用户角色 - 改进版本"""
    if role is None:
        raise ValidationError("Role is required", "role")

    try:
        role = int(role)
    except (ValueError, TypeError):
        raise ValidationError("Role must be an integer", "role")

    valid_roles = {0: "User", 1: "Auditor", 2: "Admin"}

    if role not in valid_roles:
        role_descriptions = [f"{k} ({v})" for k, v in valid_roles.items()]
        raise ValidationError(
            f"Invalid role. Must be one of: {', '.join(role_descriptions)}", "role"
        )

    return role


def validate_model_name(name):
    """验证模型名称 - 改进版本"""
    if not name or not isinstance(name, str):
        raise ValidationError("Model name is required", "model_name")

    name = name.strip()

    if len(name) < 2:
        raise ValidationError(
            "Model name must be at least 2 characters long", "model_name"
        )

    if len(name) > 100:
        raise ValidationError("Model name must not exceed 100 characters", "model_name")

    # 支持中文、英文、数字、下划线、连字符和空格
    if not re.match(r"^[a-zA-Z0-9_\-\s\u4e00-\u9fff]+$", name):
        raise ValidationError("Model name contains invalid characters", "model_name")

    # 检查保留名称
    reserved_names = {
        "system",
        "admin",
        "api",
        "null",
        "undefined",
        "default",
        "test",
        "demo",
        "sample",
        "example",
        "official",
    }

    if name.lower() in reserved_names:
        raise ValidationError("Model name is reserved", "model_name")

    # 检查恶意内容
    if contains_malicious_content(name):
        raise ValidationError("Model name contains invalid content", "model_name")

    return name


def validate_pagination(page, per_page):
    """验证分页参数 - 改进版本"""
    # 处理页码
    if page is None:
        page = 1

    try:
        page = int(page)
    except (ValueError, TypeError):
        raise ValidationError("Page number must be an integer", "page")

    if page < 1:
        raise ValidationError("Page number must be positive", "page")

    if page > 10000:  # 防止过大的页码
        raise ValidationError("Page number too large", "page")

    # 处理每页项目数
    if per_page is None:
        per_page = current_app.config.get("ITEMS_PER_PAGE", 20)

    try:
        per_page = int(per_page)
    except (ValueError, TypeError):
        raise ValidationError("Items per page must be an integer", "per_page")

    if per_page < 1:
        raise ValidationError("Items per page must be positive", "per_page")

    max_per_page = current_app.config.get("MAX_ITEMS_PER_PAGE", 100)
    if per_page > max_per_page:
        raise ValidationError(
            f"Items per page cannot exceed {max_per_page}", "per_page"
        )

    return page, per_page


def validate_model_upload_data(data, gpt_file=None, sovits_file=None):
    """验证模型上传数据 - 严格版本"""
    print(f"Validating model upload data: {data}")
    if not isinstance(data, dict):
        raise ValidationError("Invalid data format", "data")

    # 验证必需字段
    required_fields = ["name", "description"]
    for field in required_fields:
        if not data.get(field):
            raise ValidationError(f"{field} is required", field)

    # 验证模型名称
    model_name = validate_model_name(data["name"])

    # 验证描述
    description = validate_text_length(
        data["description"], min_length=10, max_length=1000, field_name="description"
    )

    # 严格要求：必须提供两个文件
    if not gpt_file:
        raise ValidationError("GPT model file (.pth) is required", "gpt_model_file")
    if not sovits_file:
        raise ValidationError(
            "SoVITS model file (.ckpt) is required", "sovits_model_file"
        )

    # 验证文件
    validate_model_file(gpt_file, expected_type="gpt")
    validate_model_file(sovits_file, expected_type="sovits")

    # 验证支持的语言
    supported_languages = data.get("supported_languages", ["zh"])
    if supported_languages:
        validate_language_support(supported_languages)

    # 验证支持的情感
    supported_emotions = data.get("supported_emotions", ["neutral"])
    if supported_emotions:
        for emotion in supported_emotions:
            validate_emotion(emotion)

    # 验证标签
    tags = data.get("tags", [])
    if tags:
        validate_tags(tags)

    return {
        "name": model_name,
        "description": description,
        "supported_languages": supported_languages,
        "supported_emotions": supported_emotions,
        "tags": tags,
    }


def validate_language_support(languages):
    """验证支持的语言列表 - 改进版本"""
    print(f"Validating supported languages: {languages}")
    if not languages:
        raise ValidationError(
            "At least one language must be supported", "supported_languages"
        )

    if not isinstance(languages, (list, tuple)):
        raise ValidationError(
            "Languages must be provided as a list", "supported_languages"
        )

    if len(languages) > 10:  # 限制最大语言数
        raise ValidationError(
            "Too many languages specified (max 10)", "supported_languages"
        )

    # 获取支持的语言列表
    supported_languages = current_app.config.get("SUPPORTED_LANGUAGES", {})
    print(f"Supported languages from config: {supported_languages}")
    valid_language_codes = set(supported_languages.keys())

    # 如果配置为空，使用默认支持的语言
    if not valid_language_codes:
        valid_language_codes = {
            "zh",
            "en",
            "ja",
            "ko",
            "es",
            "fr",
            "de",
        }

    invalid_languages = []
    for lang in languages:
        if not isinstance(lang, str):
            raise ValidationError(
                "Language codes must be strings", "supported_languages"
            )

        # 验证语言代码格式 (如: zh, en)
        if not re.match(r"^[a-z]{2}$", lang):
            print(f"Invalid language code format: {lang}")
            raise ValidationError(
                f"Invalid language code format: {lang}", "supported_languages"
            )

        if lang not in valid_language_codes:
            invalid_languages.append(lang)

    if invalid_languages:
        raise ValidationError(
            f'Unsupported languages: {", ".join(invalid_languages)}. '
            f'Supported: {", ".join(sorted(valid_language_codes))}',
            "supported_languages",
        )

    return list(set(languages))  # 去重


def validate_tags(tags):
    """验证标签列表"""
    if not isinstance(tags, (list, tuple)):
        raise ValidationError("Tags must be provided as a list", "tags")

    if len(tags) > 20:  # 限制标签数量
        raise ValidationError("Too many tags (max 20)", "tags")

    validated_tags = []
    for tag in tags:
        if not isinstance(tag, str):
            raise ValidationError("Tag names must be strings", "tags")

        tag = tag.strip()
        if not tag:
            continue  # 跳过空标签

        if len(tag) > 50:
            raise ValidationError("Tag name too long (max 50 characters)", "tags")

        # 检查标签名称格式
        if not re.match(r"^[a-zA-Z0-9_\-\s\u4e00-\u9fff]+$", tag):
            raise ValidationError(f"Invalid tag name: {tag}", "tags")

        if contains_malicious_content(tag):
            raise ValidationError(f"Tag contains invalid content: {tag}", "tags")

        validated_tags.append(tag)

    return list(set(validated_tags))  # 去重


def validate_file_pair(gpt_file, sovits_file, model_name):
    """验证文件对 - 严格版本"""
    if not gpt_file:
        raise ValidationError("GPT model file (.pth) is required", "gpt_model_file")

    if not sovits_file:
        raise ValidationError(
            "SoVITS model file (.ckpt) is required", "sovits_model_file"
        )

    # 验证文件名安全性
    gpt_filename = secure_filename(gpt_file.filename)
    sovits_filename = secure_filename(sovits_file.filename)

    if not gpt_filename or not sovits_filename:
        raise ValidationError("Invalid file names", "model_files")

    # 检查文件扩展名
    if not gpt_filename.lower().endswith(".pth"):
        raise ValidationError(
            "GPT model file must have .pth extension", "gpt_model_file"
        )

    if not sovits_filename.lower().endswith(".ckpt"):
        raise ValidationError(
            "SoVITS model file must have .ckpt extension", "sovits_model_file"
        )

    # 检查文件大小比例（GPT文件通常比SoVITS文件小）
    gpt_file.seek(0, os.SEEK_END)
    gpt_size = gpt_file.tell()
    gpt_file.seek(0)

    sovits_file.seek(0, os.SEEK_END)
    sovits_size = sovits_file.tell()
    sovits_file.seek(0)

    # 基本合理性检查
    if gpt_size > sovits_size * 10:  # GPT文件不应该比SoVITS文件大太多
        logger.warning(
            f"Unusual file size ratio: GPT({gpt_size}) vs SoVITS({sovits_size})"
        )

    # 可选：检查文件名是否匹配模型名称
    if model_name:
        safe_model_name = re.sub(r"[^\w\-_.]", "_", model_name.lower())

        # 建议的文件名模式
        suggested_gpt = f"{safe_model_name}_gpt.pth"
        suggested_sovits = f"{safe_model_name}_sovits.ckpt"

        if gpt_filename.lower() != suggested_gpt:
            logger.info(
                f"GPT file name suggestion: {suggested_gpt} (actual: {gpt_filename})"
            )

        if sovits_filename.lower() != suggested_sovits:
            logger.info(
                f"SoVITS file name suggestion: {suggested_sovits} (actual: {sovits_filename})"
            )

    return True


def validate_watermark_code_length(code_length):
    """验证水印码长度 - 改进版本"""
    if code_length is None:
        raise ValidationError("Code length is required", "code_length")

    try:
        code_length = int(code_length)
    except (ValueError, TypeError):
        raise ValidationError("Code length must be a valid integer", "code_length")

    valid_lengths = [8, 16, 32]
    if code_length not in valid_lengths:
        raise ValidationError(
            f"Code length must be one of: {', '.join(map(str, valid_lengths))}",
            "code_length",
        )

    return code_length


def validate_watermark_description(description):
    """验证水印描述"""
    if description is None:
        return ""

    if not isinstance(description, str):
        raise ValidationError("Description must be a string", "description")

    description = description.strip()

    if len(description) > 500:
        raise ValidationError(
            "Description must be less than 500 characters", "description"
        )

    if contains_malicious_content(description):
        raise ValidationError("Description contains invalid content", "description")

    return description


def sanitize_filename(filename):
    """清理文件名 - 改进版本"""
    if not filename or not isinstance(filename, str):
        return "unnamed_file"

    # 使用werkzeug的secure_filename作为基础
    filename = secure_filename(filename)

    if not filename:
        return "unnamed_file"

    # 进一步清理
    # 移除可能有害的字符
    filename = re.sub(r"[^\w\s.\-_()]", "", filename)

    # 限制连续的特殊字符
    filename = re.sub(r"[-_.]{2,}", "_", filename)

    # 确保不以点开头（隐藏文件）
    if filename.startswith("."):
        filename = "file_" + filename[1:]

    # 限制长度
    max_length = current_app.config.get("MAX_FILENAME_LENGTH", 255)
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        available_length = max_length - len(ext) - 1
        filename = name[:available_length] + ext

    # 确保有扩展名（如果原本有的话）
    if "." not in filename and "." in secure_filename(filename):
        filename += ".unknown"

    return filename


def validate_json_structure(data, required_structure):
    """验证JSON数据结构"""
    if not isinstance(data, dict):
        raise ValidationError("Data must be a JSON object")

    def check_structure(obj, structure, path=""):
        for key, expected_type in structure.items():
            current_path = f"{path}.{key}" if path else key

            if key not in obj:
                raise ValidationError(f"Missing required field: {current_path}")

            value = obj[key]

            if isinstance(expected_type, dict):
                if not isinstance(value, dict):
                    raise ValidationError(f"Field {current_path} must be an object")
                check_structure(value, expected_type, current_path)
            elif isinstance(expected_type, list):
                if not isinstance(value, list):
                    raise ValidationError(f"Field {current_path} must be an array")
                if expected_type and len(expected_type) > 0:
                    item_type = expected_type[0]
                    for i, item in enumerate(value):
                        if not isinstance(item, item_type):
                            raise ValidationError(
                                f"Field {current_path}[{i}] must be {item_type.__name__}"
                            )
            else:
                if not isinstance(value, expected_type):
                    raise ValidationError(
                        f"Field {current_path} must be {expected_type.__name__}"
                    )

    check_structure(data, required_structure)
    return True


def validate_batch_operation(items, max_items=100):
    """验证批量操作"""
    if not isinstance(items, (list, tuple)):
        raise ValidationError("Items must be provided as a list")

    if len(items) == 0:
        raise ValidationError("At least one item is required")

    if len(items) > max_items:
        raise ValidationError(f"Too many items (max {max_items})")

    # 检查重复项
    if len(set(items)) != len(items):
        raise ValidationError("Duplicate items detected")

    return list(items)


def validate_id_list(ids, field_name="ids"):
    """验证ID列表"""
    if not isinstance(ids, (list, tuple)):
        raise ValidationError(f"{field_name} must be a list", field_name)

    if not ids:
        raise ValidationError(f"{field_name} cannot be empty", field_name)

    validated_ids = []
    for i, id_value in enumerate(ids):
        if not isinstance(id_value, str):
            raise ValidationError(f"{field_name}[{i}] must be a string", field_name)

        id_value = id_value.strip()
        if not id_value:
            raise ValidationError(f"{field_name}[{i}] cannot be empty", field_name)

        # 验证UUID格式（如果使用UUID）
        try:
            import uuid

            uuid.UUID(id_value)
            validated_ids.append(id_value)
        except ValueError:
            raise ValidationError(
                f"{field_name}[{i}] is not a valid ID format", field_name
            )

    # 去重
    return list(set(validated_ids))


# 装饰器：自动验证请求数据
def validate_request_data(schema):
    """请求数据验证装饰器"""

    def decorator(func):
        from functools import wraps

        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import request

            # 获取请求数据
            if request.content_type and "application/json" in request.content_type:
                data = request.get_json()
                if data is None:
                    raise ValidationError("Invalid JSON data")
            else:
                data = request.form.to_dict()

            # 验证数据结构
            validate_json_structure(data, schema)

            # 将验证后的数据传递给原函数
            return func(data, *args, **kwargs)

        return wrapper

    return decorator
