import os
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from flask import request, current_app
from werkzeug.utils import secure_filename


def generate_unique_filename(original_filename, prefix=""):
    """生成唯一文件名"""
    # 获取文件扩展名
    _, ext = os.path.splitext(original_filename)

    # 生成唯一标识符
    unique_id = str(uuid.uuid4())

    # 组合文件名
    if prefix:
        filename = f"{prefix}_{unique_id}{ext}"
    else:
        filename = f"{unique_id}{ext}"

    return filename


def save_uploaded_file(file, upload_type="audio_samples", prefix=""):
    """保存上传的文件"""
    if not file or not file.filename:
        return None

    # 生成安全的文件名
    filename = generate_unique_filename(file.filename, prefix)

    # 创建保存路径
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


def generate_file_hash(file_path):
    """生成文件哈希值"""
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception:
        return None


def get_client_ip():
    """获取客户端IP地址"""
    if request.environ.get("HTTP_X_FORWARDED_FOR") is None:
        return request.environ["REMOTE_ADDR"]
    else:
        # 如果使用了代理，获取原始IP
        return request.environ["HTTP_X_FORWARDED_FOR"].split(",")[0].strip()


def get_user_agent():
    """获取用户代理字符串"""
    return request.headers.get("User-Agent", "")


def format_file_size(size_bytes):
    """格式化文件大小"""
    if size_bytes == 0:
        return "0B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f}{size_names[i]}"


def format_duration(seconds):
    """格式化时长"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{int(minutes)}m{int(remaining_seconds)}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{int(hours)}h{int(minutes)}m"


def paginate_query(query, page, per_page):
    """分页查询辅助函数"""
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
    """创建标准API响应"""
    response = {"success": success, "message": message}

    if data is not None:
        response["data"] = data

    # 添加额外的响应字段
    response.update(kwargs)

    return response


def safe_filename(filename):
    """生成安全的文件名"""
    filename = secure_filename(filename)

    # 如果文件名为空，生成一个随机名称
    if not filename:
        filename = f"file_{secrets.token_hex(8)}"

    return filename


def calculate_estimated_time(task_type, **kwargs):
    """计算预估完成时间"""
    base_times = {
        "voice_clone": 120,  # 2分钟基础时间
        "tts": 10,  # 10秒基础时间
    }

    base_time = base_times.get(task_type, 60)

    if task_type == "voice_clone":
        # 根据音频数量和时长调整
        sample_count = kwargs.get("sample_count", 1)
        total_duration = kwargs.get("total_duration", 30)
        base_time += sample_count * 30 + total_duration * 2

    elif task_type == "tts":
        # 根据文本长度调整
        text_length = kwargs.get("text_length", 50)
        base_time = max(5, text_length * 0.2)

    return datetime.utcnow() + timedelta(seconds=base_time)


def clean_temp_files(max_age_hours=24):
    """清理临时文件"""
    temp_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "temp")
    if not os.path.exists(temp_dir):
        return

    cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

    for filename in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, filename)
        try:
            # 获取文件修改时间
            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_mtime < cutoff_time:
                os.remove(file_path)
        except Exception:
            # 忽略删除失败的文件
            pass


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


def generate_api_key():
    """生成API密钥"""
    return f"sk-{secrets.token_urlsafe(32)}"


def mask_sensitive_data(data, sensitive_fields):
    """遮蔽敏感数据"""
    if isinstance(data, dict):
        masked_data = data.copy()
        for field in sensitive_fields:
            if field in masked_data:
                if isinstance(masked_data[field], str) and len(masked_data[field]) > 4:
                    masked_data[field] = (
                        masked_data[field][:2]
                        + "*" * (len(masked_data[field]) - 4)
                        + masked_data[field][-2:]
                    )
                else:
                    masked_data[field] = "***"
        return masked_data
    return data


def log_user_action(user_id, action, resource_type, resource_id=None, details=None):
    """记录用户操作日志"""
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
