# ./gpt-sovits-backend/app/utils/helpers.py
import os
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from flask import request, current_app
from werkzeug.utils import secure_filename
from flask import has_app_context


def generate_unique_filename(original_filename, prefix=""):
    """生成唯一文件名 - 使用配置的文件名格式"""
    # 获取文件扩展名
    _, ext = os.path.splitext(original_filename)

    # 生成唯一标识符
    unique_id = str(uuid.uuid4())

    # 组合文件名 - 使用配置的格式
    if prefix:
        filename = f"{prefix}_{unique_id}{ext}"
    else:
        filename = f"{unique_id}{ext}"

    return filename


def save_uploaded_file(file, upload_type="audio_samples", prefix=""):
    """保存上传的文件 - 使用配置的路径"""
    if not file or not file.filename:
        return None

    # 生成安全的文件名
    filename = generate_unique_filename(file.filename, prefix)

    # 创建保存路径 - 使用配置的上传目录
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], upload_type)
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, filename)

    # 保存文件
    file.save(file_path)

    return {
        "filename": filename,
        "file_path": file_path,
        "relative_path": os.path.join(upload_type, filename),
        "size": os.path.getsize(file_path),
    }


def generate_file_hash(file_path, algorithm="sha256"):
    """生成文件哈希值 - 支持配置哈希算法"""
    try:
        # 使用配置的哈希算法
        hash_algorithm = current_app.config.get("FILE_HASH_ALGORITHM", algorithm)

        if hash_algorithm == "md5":
            hash_obj = hashlib.md5()
        elif hash_algorithm == "sha1":
            hash_obj = hashlib.sha1()
        elif hash_algorithm == "sha512":
            hash_obj = hashlib.sha512()
        else:  # 默认 sha256
            hash_obj = hashlib.sha256()

        # 使用配置的读取块大小
        chunk_size = current_app.config.get("FILE_HASH_CHUNK_SIZE", 4096)

        with open(file_path, "rb") as f:
            for chunk in iter(f.read(chunk_size), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception:
        return None


def get_client_ip():
    """获取客户端IP地址 - 安全版本，支持配置的代理头"""
    try:
        from flask import request

        # 使用配置的代理头列表
        proxy_headers = current_app.config.get(
            "PROXY_HEADERS",
            ["HTTP_X_FORWARDED_FOR", "HTTP_X_REAL_IP", "HTTP_CF_CONNECTING_IP"],
        )

        # 按优先级检查代理头
        for header in proxy_headers:
            if request.environ.get(header):
                # 获取第一个IP（如果有多个代理）
                ip = request.environ[header].split(",")[0].strip()
                if ip and _is_valid_ip(ip):
                    return ip

        # 回退到直接连接IP
        return request.environ.get("REMOTE_ADDR", "127.0.0.1")
    except RuntimeError:
        # 不在请求上下文中
        return "127.0.0.1"
    except Exception:
        # 其他错误
        return "127.0.0.1"


def _is_valid_ip(ip):
    """验证IP地址格式"""
    try:
        import ipaddress

        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def get_user_agent():
    """获取用户代理字符串 - 安全版本"""
    try:
        from flask import request

        user_agent = request.headers.get("User-Agent", "")

        # 使用配置的最大长度限制
        max_length = current_app.config.get("USER_AGENT_MAX_LENGTH", 500)
        if len(user_agent) > max_length:
            user_agent = user_agent[:max_length] + "..."

        return user_agent
    except RuntimeError:
        # 不在请求上下文中
        return "TestClient/1.0"
    except Exception:
        # 其他错误
        return "Unknown"


def format_file_size(size_bytes):
    """格式化文件大小 - 支持配置的单位"""
    if size_bytes == 0:
        return "0B"

    # 使用配置的单位制（二进制或十进制）
    use_binary = current_app.config.get("FILE_SIZE_BINARY", True)
    base = 1024 if use_binary else 1000

    if use_binary:
        size_names = ["B", "KiB", "MiB", "GiB", "TiB"]
    else:
        size_names = ["B", "KB", "MB", "GB", "TB"]

    i = 0
    while size_bytes >= base and i < len(size_names) - 1:
        size_bytes /= base
        i += 1

    return f"{size_bytes:.1f}{size_names[i]}"


def format_duration(seconds):
    """格式化时长 - 支持配置的格式"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60

        # 使用配置决定是否显示秒数
        show_seconds = current_app.config.get("DURATION_SHOW_SECONDS", True)
        if show_seconds and remaining_seconds > 0:
            return f"{int(minutes)}m{int(remaining_seconds)}s"
        else:
            return f"{int(minutes)}m"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{int(hours)}h{int(minutes)}m"


def paginate_query(query, page, per_page):
    """分页查询辅助函数 - 使用配置的限制"""
    # 使用配置的最大每页项目数
    max_per_page = current_app.config.get("MAX_ITEMS_PER_PAGE", 100)
    per_page = min(per_page, max_per_page)

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
        "has_prev": page > 1,
        "has_next": page * per_page < total,
        "prev_num": page - 1 if page > 1 else None,
        "next_num": page + 1 if page * per_page < total else None,
    }


def create_response(success=True, message="", data=None, **kwargs):
    """创建标准API响应 - 支持配置的响应格式"""
    response = {"success": success, "message": message}

    if data is not None:
        response["data"] = data

    # 添加时间戳（如果配置启用）
    if current_app.config.get("RESPONSE_INCLUDE_TIMESTAMP", False):
        response["timestamp"] = datetime.now().isoformat()

    # 添加版本信息（如果配置启用）
    if current_app.config.get("RESPONSE_INCLUDE_VERSION", False):
        response["version"] = current_app.config.get("API_VERSION", "1.0")

    # 添加额外的响应字段
    response.update(kwargs)

    return response


def safe_filename(filename):
    """生成安全的文件名 - 使用配置的安全规则"""
    filename = secure_filename(filename)

    # 如果文件名为空，生成一个随机名称
    if not filename:
        random_name = current_app.config.get("DEFAULT_FILENAME_PREFIX", "file")
        filename = f"{random_name}_{secrets.token_hex(8)}"

    # 使用配置的最大文件名长度
    max_length = current_app.config.get("MAX_FILENAME_LENGTH", 255)
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[: max_length - len(ext)] + ext

    return filename


def calculate_estimated_time(task_type, **kwargs):
    """计算预估完成时间 - 使用配置的基础时间"""
    # 使用配置的基础时间
    base_times = {
        "voice_clone": current_app.config.get("VOICE_CLONE_BASE_TIME", 120),
        "tts": current_app.config.get("TTS_BASE_TIME", 10),
    }

    base_time = base_times.get(task_type, 60)

    if task_type == "voice_clone":
        # 根据音频数量和时长调整 - 使用配置的系数
        sample_count = kwargs.get("sample_count", 1)
        total_duration = kwargs.get("total_duration", 30)

        sample_factor = current_app.config.get("VOICE_CLONE_SAMPLE_FACTOR", 30)
        duration_factor = current_app.config.get("VOICE_CLONE_DURATION_FACTOR", 2)

        base_time += sample_count * sample_factor + total_duration * duration_factor

    elif task_type == "tts":
        # 根据文本长度调整 - 使用配置的系数
        text_length = kwargs.get("text_length", 50)
        length_factor = current_app.config.get("TTS_LENGTH_FACTOR", 0.2)
        min_time = current_app.config.get("TTS_MIN_TIME", 5)

        base_time = max(min_time, text_length * length_factor)

    return datetime.now() + timedelta(seconds=base_time)


def clean_temp_files(max_age_hours=None):
    """清理临时文件 - 使用配置的清理策略"""
    if max_age_hours is None:
        max_age_hours = current_app.config.get("TEMP_FILE_MAX_AGE_HOURS", 24)

    temp_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "temp")
    if not os.path.exists(temp_dir):
        return 0

    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    cleaned_count = 0

    # 使用配置的清理模式
    cleanup_mode = current_app.config.get("TEMP_CLEANUP_MODE", "recursive")

    if cleanup_mode == "recursive":
        # 递归清理所有子目录
        for root, dirs, files in os.walk(temp_dir, topdown=False):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    if _should_clean_file(file_path, cutoff_time):
                        os.remove(file_path)
                        cleaned_count += 1
                except Exception:
                    pass

            # 尝试删除空目录
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                except Exception:
                    pass
    else:
        # 仅清理顶级文件
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            if os.path.isfile(file_path):
                try:
                    if _should_clean_file(file_path, cutoff_time):
                        os.remove(file_path)
                        cleaned_count += 1
                except Exception:
                    pass

    return cleaned_count


def _should_clean_file(file_path, cutoff_time):
    """判断文件是否应该被清理"""
    try:
        # 跳过系统文件和隐藏文件
        filename = os.path.basename(file_path)
        if filename.startswith(".") or filename.startswith("~"):
            return False

        # 检查文件修改时间
        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        return file_mtime < cutoff_time
    except Exception:
        return False


def validate_json_data(data, required_fields):
    """验证JSON数据包含必需字段"""
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)

    if missing_fields:
        from app.utils.exceptions import ValidationError

        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

    return True


def generate_api_key(length=None, prefix=None):
    """生成API密钥 - 使用配置的格式"""
    if length is None:
        length = current_app.config.get("API_KEY_LENGTH", 32)
    if prefix is None:
        prefix = current_app.config.get("API_KEY_PREFIX", "sk")

    return f"{prefix}-{secrets.token_urlsafe(length)}"


def mask_sensitive_data(data, sensitive_fields=None):
    """遮蔽敏感数据 - 使用配置的敏感字段列表"""
    if sensitive_fields is None:
        sensitive_fields = current_app.config.get(
            "SENSITIVE_FIELDS", ["password", "token", "key", "secret", "email"]
        )

    if isinstance(data, dict):
        masked_data = data.copy()
        for field in sensitive_fields:
            if field in masked_data:
                if isinstance(masked_data[field], str) and len(masked_data[field]) > 4:
                    # 使用配置的遮蔽字符
                    mask_char = current_app.config.get("MASK_CHARACTER", "*")
                    masked_data[field] = (
                        masked_data[field][:2]
                        + mask_char * (len(masked_data[field]) - 4)
                        + masked_data[field][-2:]
                    )
                else:
                    masked_data[field] = "***"
        return masked_data
    return data


def log_user_action(user_id, action, resource_type, resource_id=None, details=None):
    """记录用户操作日志 - 安全版本，支持配置的日志级别"""
    try:
        if not has_app_context():
            raise RuntimeError("No Flask application context")

        if not current_app.config.get("ENABLE_ACTION_LOGGING", True):
            return

        log_level = current_app.config.get("ACTION_LOG_LEVEL", "INFO")
        if log_level == "ERROR" and not action.endswith("_failed"):
            return

        from app.models.audit import AuditLog

        AuditLog.log_action(
            action=action,
            resource_type=resource_type,
            user_id=user_id,
            resource_id=resource_id,
            description=details,
            ip_address=get_client_ip(),
            user_agent=get_user_agent(),
        )
    except Exception as e:
        # 如果日志记录失败，不影响主要功能
        print(f"Warning: Failed to log user action: {e}")


def get_upload_path(upload_type, filename=None):
    """获取上传路径 - 使用配置的目录结构"""
    base_path = current_app.config["UPLOAD_FOLDER"]

    # 使用配置的目录映射
    directory_mapping = current_app.config.get(
        "UPLOAD_DIRECTORY_MAPPING",
        {
            "audio_samples": "audio_samples",
            "models": "models",
            "generated": "generated",
            "temp": "temp",
            "watermarked": "watermarked",
            "images": "images",
            "documents": "documents",
        },
    )

    subdir = directory_mapping.get(upload_type, upload_type)
    full_path = os.path.join(base_path, subdir)

    if filename:
        return os.path.join(full_path, filename)
    return full_path


def ensure_directory_exists(path):
    """确保目录存在 - 使用配置的权限"""
    try:
        os.makedirs(path, exist_ok=True)

        # 设置目录权限（如果配置了）
        dir_mode = current_app.config.get("UPLOAD_DIR_MODE")
        if dir_mode and hasattr(os, "chmod"):
            try:
                os.chmod(path, dir_mode)
            except Exception:
                pass  # 权限设置失败不影响功能

        return True
    except Exception as e:
        current_app.logger.error(f"Failed to create directory {path}: {e}")
        return False


def get_file_url(file_path, file_type="general"):
    """生成文件访问URL - 使用配置的URL前缀"""
    try:
        # 获取相对于上传目录的路径
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        relative_path = os.path.relpath(file_path, upload_folder)

        # 使用配置的URL前缀
        base_url = current_app.config.get("FILE_BASE_URL", "/uploads")
        if not base_url.startswith("/"):
            base_url = "/" + base_url

        # 标准化路径分隔符（Windows兼容）
        relative_path = relative_path.replace("\\", "/")

        return f"{base_url}/{relative_path}"
    except Exception:
        return None


def check_disk_space(path=None, min_free_mb=None):
    """检查磁盘空间 - 使用配置的最小空间要求"""
    try:
        if path is None:
            path = current_app.config["UPLOAD_FOLDER"]
        if min_free_mb is None:
            min_free_mb = current_app.config.get("MIN_DISK_SPACE_MB", 1024)  # 默认1GB

        import shutil

        total, used, free = shutil.disk_usage(path)
        free_mb = free // (1024 * 1024)

        return {
            "has_space": free_mb >= min_free_mb,
            "free_mb": free_mb,
            "required_mb": min_free_mb,
            "total_mb": total // (1024 * 1024),
            "used_mb": used // (1024 * 1024),
        }
    except Exception as e:
        current_app.logger.error(f"Disk space check failed: {e}")
        return {
            "has_space": True,  # 检查失败时假设有足够空间
            "free_mb": 0,
            "required_mb": min_free_mb or 0,
            "total_mb": 0,
            "used_mb": 0,
        }


def sanitize_user_input(text, max_length=None, validation_mode=None):
    """清理用户输入 - 使用配置的安全规则"""
    if not text:
        return ""

    # 使用配置的最大长度
    if max_length is None:
        max_length = current_app.config.get("MAX_USER_INPUT_LENGTH", 1000)

    # 截断过长的输入
    if len(text) > max_length:
        text = text[:max_length]

    # 使用配置的验证模式
    if validation_mode is None:
        validation_mode = current_app.config.get("INPUT_VALIDATION_MODE", "strict")

    # 根据验证模式定义允许的字符模式
    if validation_mode == "strict":
        # 只允许字母、数字、空格和基本标点
        import re

        text = re.sub(r"[^a-zA-Z0-9\s\-_.,!?@#$%^&*()+=]", "", text)
    elif validation_mode == "moderate":
        # 允许更多字符，但过滤危险字符
        import re

        text = re.sub(r'[<>"\';\\]', "", text)
    elif validation_mode == "lenient":
        # 只过滤明显的危险字符
        import re

        text = re.sub(r'[<>"\']', "", text)
    # lenient 模式基本不过滤

    # 清理多余的空白字符
    text = " ".join(text.split())

    return text.strip()


def get_system_info():
    """获取系统信息 - 支持配置的信息级别"""
    info_level = current_app.config.get("SYSTEM_INFO_LEVEL", "basic")

    basic_info = {
        "upload_folder": current_app.config["UPLOAD_FOLDER"],
        "max_file_size": current_app.config.get("MAX_CONTENT_LENGTH", 0),
        "allowed_audio_formats": list(
            current_app.config.get("ALLOWED_AUDIO_EXTENSIONS", [])
        ),
    }

    if info_level == "detailed":
        try:
            import psutil

            basic_info.update(
                {
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage("/").percent,
                }
            )
        except ImportError:
            basic_info["system_monitoring"] = "psutil not available"

    if info_level == "full":
        basic_info.update(
            {
                "config_keys": list(current_app.config.keys()),
                "environment": current_app.config.get("FLASK_ENV", "unknown"),
            }
        )

    return basic_info
