# ./gpt-sovits-backend/app/services/file_service.py
import os
import hashlib
import magic
from datetime import datetime
from flask import current_app
from app.extensions import db
from app.models.audit import UserUpload
from app.utils.exceptions import ValidationError, FileUploadError
from app.utils.helpers import generate_unique_filename, generate_file_hash
from app.utils.audio_utils import validate_audio_content, get_audio_info


def process_file_upload(file, user_id, file_type="general", metadata=None):
    """处理文件上传"""
    try:
        if not file or not file.filename:
            raise ValidationError("No file provided")

        # 验证文件大小
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        max_size = current_app.config.get("MAX_CONTENT_LENGTH", 10 * 1024 * 1024)
        if file_size > max_size:
            raise ValidationError(
                f"File size exceeds {max_size // (1024*1024)}MB limit"
            )

        # 生成唯一文件名
        original_filename = file.filename
        safe_filename = generate_unique_filename(original_filename, f"user_{user_id}")

        # 确定保存目录
        upload_dir = get_upload_directory(file_type)
        os.makedirs(upload_dir, exist_ok=True)

        # 保存文件
        file_path = os.path.join(upload_dir, safe_filename)
        file.save(file_path)

        # 验证文件内容
        mime_type = get_file_mime_type(file_path)
        file_hash = generate_file_hash(file_path)

        # 检查重复文件
        existing_upload = UserUpload.query.filter_by(
            user_id=user_id, file_hash=file_hash, is_deleted=False
        ).first()

        if existing_upload:
            # 删除新上传的文件
            os.remove(file_path)
            return {
                "upload_id": existing_upload.id,
                "is_duplicate": True,
                "message": "File already exists",
            }

        # 处理特定文件类型
        file_metadata = metadata or {}
        if file_type == "audio":
            try:
                audio_info = get_audio_info(file_path)
                file_metadata.update(audio_info)

                # 验证音频内容
                validate_audio_content(file_path)

            except Exception as e:
                # 删除无效文件
                os.remove(file_path)
                raise ValidationError(f"Invalid audio file: {str(e)}")

        # 创建上传记录
        upload_record = UserUpload(
            user_id=user_id,
            filename=safe_filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            mime_type=mime_type,
            file_hash=file_hash,
        )

        upload_record.set_metadata(file_metadata)

        db.session.add(upload_record)
        db.session.commit()

        return {
            "upload_id": upload_record.id,
            "filename": safe_filename,
            "original_filename": original_filename,
            "file_size": file_size,
            "file_type": file_type,
            "mime_type": mime_type,
            "metadata": file_metadata,
            "is_duplicate": False,
        }

    except Exception as e:
        # 清理已上传的文件
        if "file_path" in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        raise e


def get_upload_directory(file_type):
    """获取上传目录"""
    base_dir = current_app.config["UPLOAD_FOLDER"]

    type_dirs = {
        "audio": "audio_samples",
        "model": "models",
        "image": "images",
        "document": "documents",
        "general": "general",
    }

    subdir = type_dirs.get(file_type, "general")
    return os.path.join(base_dir, subdir)


def get_file_mime_type(file_path):
    """获取文件MIME类型"""
    try:
        mime = magic.Magic(mime=True)
        return mime.from_file(file_path)
    except Exception:
        # 回退到基于扩展名的检测
        ext = os.path.splitext(file_path)[1].lower()
        mime_map = {
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
            ".flac": "audio/flac",
            ".m4a": "audio/mp4",
            ".pth": "application/octet-stream",
            ".json": "application/json",
            ".txt": "text/plain",
            ".pdf": "application/pdf",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
        }
        return mime_map.get(ext, "application/octet-stream")


def validate_file_type(file_path, expected_type):
    """验证文件类型"""
    try:
        mime_type = get_file_mime_type(file_path)

        type_patterns = {
            "audio": ["audio/"],
            "image": ["image/"],
            "document": ["text/", "application/pdf", "application/msword"],
            "model": ["application/octet-stream", "application/json"],
        }

        patterns = type_patterns.get(expected_type, [])

        for pattern in patterns:
            if mime_type.startswith(pattern):
                return True

        return False

    except Exception:
        return False


def delete_file(upload_id, user_id, force_delete=False):
    """删除文件"""
    try:
        upload = UserUpload.query.filter_by(id=upload_id, user_id=user_id).first()

        if not upload:
            raise ValidationError("File not found")

        if upload.is_deleted and not force_delete:
            raise ValidationError("File already deleted")

        # 检查文件是否正在使用
        if not force_delete and is_file_in_use(upload):
            raise ValidationError("File is currently in use and cannot be deleted")

        # 标记为已删除
        upload.mark_deleted()

        # 删除物理文件
        if os.path.exists(upload.file_path):
            try:
                os.remove(upload.file_path)
            except Exception as e:
                current_app.logger.warning(f"Failed to delete physical file: {e}")

        return True

    except Exception as e:
        raise e


def is_file_in_use(upload):
    """检查文件是否正在使用"""
    try:
        if upload.file_type == "audio":
            # 检查是否在进行中的语音克隆任务中
            from app.models.task import VoiceCloneTask

            active_tasks = VoiceCloneTask.query.filter(
                VoiceCloneTask.user_id == upload.user_id,
                VoiceCloneTask.status.in_(["pending", "processing"]),
            ).all()

            for task in active_tasks:
                sample_paths = task.get_audio_samples()
                if upload.file_path in sample_paths:
                    return True

        elif upload.file_type == "model":
            # 检查是否有关联的语音模型
            from app.models.model import VoiceModel

            model = VoiceModel.query.filter(
                (VoiceModel.model_path == upload.file_path)
                | (VoiceModel.config_path == upload.file_path)
                | (VoiceModel.index_path == upload.file_path)
            ).first()

            if model and model.status == "active":
                return True

        return False

    except Exception:
        return False  # 如果检查失败，假设没有在使用


def get_file_statistics(user_id=None):
    """获取文件统计信息"""
    try:
        query = UserUpload.query.filter_by(is_deleted=False)

        if user_id:
            query = query.filter_by(user_id=user_id)

        # 总体统计
        total_files = query.count()
        total_size = (
            query.with_entities(db.func.sum(UserUpload.file_size)).scalar() or 0
        )

        # 按类型统计
        type_stats = {}
        file_types = ["audio", "model", "image", "document", "general"]

        for file_type in file_types:
            type_query = query.filter_by(file_type=file_type)
            count = type_query.count()
            size = (
                type_query.with_entities(db.func.sum(UserUpload.file_size)).scalar()
                or 0
            )

            type_stats[file_type] = {
                "count": count,
                "size_bytes": int(size),
                "size_mb": round(size / (1024 * 1024), 2),
            }

        return {
            "total_files": total_files,
            "total_size_bytes": int(total_size),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "by_type": type_stats,
        }

    except Exception as e:
        raise e


def cleanup_orphaned_files():
    """清理孤立文件"""
    try:
        cleaned_count = 0

        # 查找数据库中的文件记录
        uploads = UserUpload.query.all()
        db_file_paths = {upload.file_path for upload in uploads}

        # 扫描上传目录
        base_dir = current_app.config["UPLOAD_FOLDER"]

        for root, dirs, files in os.walk(base_dir):
            for file in files:
                file_path = os.path.join(root, file)

                # 跳过系统文件
                if file.startswith("."):
                    continue

                # 如果文件不在数据库中，删除它
                if file_path not in db_file_paths:
                    try:
                        os.remove(file_path)
                        cleaned_count += 1
                    except Exception as e:
                        current_app.logger.warning(
                            f"Failed to delete orphaned file {file_path}: {e}"
                        )

        # 清理空目录
        for root, dirs, files in os.walk(base_dir, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                except Exception:
                    pass

        return cleaned_count

    except Exception as e:
        current_app.logger.error(f"Cleanup orphaned files failed: {e}")
        raise e


def batch_delete_files(upload_ids, user_id):
    """批量删除文件"""
    try:
        uploads = UserUpload.query.filter(
            UserUpload.id.in_(upload_ids),
            UserUpload.user_id == user_id,
            UserUpload.is_deleted == False,
        ).all()

        deleted_count = 0
        errors = []

        for upload in uploads:
            try:
                # 检查是否正在使用
                if is_file_in_use(upload):
                    errors.append(f"File {upload.original_filename} is in use")
                    continue

                # 删除文件
                upload.mark_deleted()

                if os.path.exists(upload.file_path):
                    os.remove(upload.file_path)

                deleted_count += 1

            except Exception as e:
                errors.append(f"Failed to delete {upload.original_filename}: {str(e)}")

        db.session.commit()

        return {"deleted_count": deleted_count, "errors": errors}

    except Exception as e:
        raise e
