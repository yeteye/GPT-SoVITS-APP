# ./gpt-sovits-backend/app/models/model.py (修复版本 - 统一字段使用)
from datetime import datetime
from app.extensions import db
import uuid
import json
import os

# 多对多关系表：模型-标签
model_tags = db.Table(
    "model_tags",
    db.Column(
        "model_id", db.String(36), db.ForeignKey("voice_models.id"), primary_key=True
    ),
    db.Column("tag_id", db.String(36), db.ForeignKey("tags.id"), primary_key=True),
)


class VoiceModel(db.Model):
    """语音模型 - GPT-SoVITS 双模型架构 - 修复版本"""

    __tablename__ = "voice_models"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 基本信息
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text)

    # 模型类型: user_trained(用户训练), official(官方预训练)
    model_type = db.Column(
        db.String(20), default="user_trained", nullable=False, index=True
    )

    # 所有者信息
    owner_id = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)

    # GPT-SoVITS 双模型文件路径 (必须同时存在)
    gpt_model_path = db.Column(db.String(255), nullable=False)  # GPT模型文件路径 (.pth)
    sovits_model_path = db.Column(
        db.String(255), nullable=False
    )  # SoVITS模型文件路径 (.ckpt)

    # 模型特性
    supported_emotions = db.Column(db.Text)  # JSON格式存储支持的情感列表
    supported_languages = db.Column(db.Text)  # JSON格式存储支持的语言列表
    voice_characteristics = db.Column(db.Text)  # 音色特征描述

    # 质量评分
    quality_score = db.Column(db.Float, default=0.0, index=True)  # 模型质量评分 0-10
    download_count = db.Column(db.Integer, default=0)  # 下载次数
    usage_count = db.Column(db.Integer, default=0)  # 使用次数

    # 状态信息
    status = db.Column(
        db.String(20), default="active", nullable=False, index=True
    )  # active, inactive, pending_review
    is_public = db.Column(
        db.Boolean, default=False, nullable=False, index=True
    )  # 是否公开
    is_featured = db.Column(
        db.Boolean, default=False, nullable=False, index=True
    )  # 是否为精选模型

    # 审核信息
    review_status = db.Column(
        db.String(20), default="pending", index=True
    )  # pending, approved, rejected
    review_message = db.Column(db.Text)  # 审核意见
    reviewed_by = db.Column(db.String(36))  # 审核者用户ID
    reviewed_at = db.Column(db.DateTime)

    # 时间戳
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关联关系
    tags = db.relationship(
        "Tag",
        secondary=model_tags,
        lazy="subquery",
        backref=db.backref("models", lazy=True),
    )

    def __init__(self, **kwargs):
        """初始化时验证必需字段 - 修复版本"""
        super().__init__(**kwargs)

        # 确保必需字段存在
        if not getattr(self, "gpt_model_path", None):
            raise ValueError("gpt_model_path is required for all voice models")
        if not getattr(self, "sovits_model_path", None):
            raise ValueError("sovits_model_path is required for all voice models")

    def set_supported_emotions(self, emotions):
        """设置支持的情感列表"""
        if not isinstance(emotions, (list, tuple)):
            raise ValueError("Emotions must be a list or tuple")

        # 验证情感列表
        valid_emotions = {
            "neutral",
            "happy",
            "sad",
            "angry",
            "surprised",
            "disgusted",
            "fearful",
            "calm",
            "excited",
        }

        invalid_emotions = set(emotions) - valid_emotions
        if invalid_emotions:
            raise ValueError(f"Invalid emotions: {invalid_emotions}")

        self.supported_emotions = json.dumps(emotions)

    def get_supported_emotions(self):
        """获取支持的情感列表"""
        if self.supported_emotions:
            try:
                return json.loads(self.supported_emotions)
            except json.JSONDecodeError:
                return ["neutral"]
        return ["neutral"]

    def set_supported_languages(self, languages):
        """设置支持的语言列表"""
        if not isinstance(languages, (list, tuple)):
            raise ValueError("Languages must be a list or tuple")

        # 验证语言代码格式
        valid_language_pattern = r"^[a-z]{2}-[A-Z]{2}$"
        import re

        for lang in languages:
            if not re.match(valid_language_pattern, lang):
                raise ValueError(f"Invalid language code format: {lang}")

        self.supported_languages = json.dumps(languages)

    def get_supported_languages(self):
        """获取支持的语言列表"""
        if self.supported_languages:
            try:
                return json.loads(self.supported_languages)
            except json.JSONDecodeError:
                return ["zh-CN"]
        return ["zh-CN"]

    def increment_usage(self):
        """增加使用次数 - 线程安全版本"""
        try:
            # 使用数据库级别的原子操作
            db.session.execute(
                db.text(
                    "UPDATE voice_models SET usage_count = usage_count + 1 WHERE id = :id"
                ),
                {"id": self.id},
            )
            db.session.commit()

            # 更新本地对象
            self.usage_count += 1
        except Exception as e:
            db.session.rollback()
            raise e

    def increment_download(self):
        """增加下载次数 - 线程安全版本"""
        try:
            # 使用数据库级别的原子操作
            db.session.execute(
                db.text(
                    "UPDATE voice_models SET download_count = download_count + 1 WHERE id = :id"
                ),
                {"id": self.id},
            )
            db.session.commit()

            # 更新本地对象
            self.download_count += 1
        except Exception as e:
            db.session.rollback()
            raise e

    def set_review_result(self, status, message, reviewer_id):
        """设置审核结果"""
        if status not in ["approved", "rejected"]:
            raise ValueError("Status must be 'approved' or 'rejected'")

        self.review_status = status
        self.review_message = message
        self.reviewed_by = reviewer_id
        self.reviewed_at = datetime.utcnow()

        if status == "approved":
            self.status = "active"
        elif status == "rejected":
            self.status = "inactive"

        db.session.commit()

    def validate_model_files(self):
        """验证GPT和SoVITS模型文件是否都存在 - 修复版本"""
        result = {
            "all_files_exist": False,
            "gpt_model_exists": False,
            "sovits_model_exists": False,
            "missing_files": [],
            "file_sizes": {},
            "validation_errors": [],
        }

        try:
            # 检查GPT模型文件
            if self.gpt_model_path:
                if os.path.exists(self.gpt_model_path):
                    result["gpt_model_exists"] = True
                    result["file_sizes"]["gpt_model"] = os.path.getsize(
                        self.gpt_model_path
                    )

                    # 验证文件扩展名
                    if not self.gpt_model_path.lower().endswith(".pth"):
                        result["validation_errors"].append(
                            "GPT model file should have .pth extension"
                        )
                else:
                    result["missing_files"].append("gpt_model")
            else:
                result["missing_files"].append("gpt_model")
                result["validation_errors"].append("GPT model path is not set")

            # 检查SoVITS模型文件
            if self.sovits_model_path:
                if os.path.exists(self.sovits_model_path):
                    result["sovits_model_exists"] = True
                    result["file_sizes"]["sovits_model"] = os.path.getsize(
                        self.sovits_model_path
                    )

                    # 验证文件扩展名
                    if not self.sovits_model_path.lower().endswith(".ckpt"):
                        result["validation_errors"].append(
                            "SoVITS model file should have .ckpt extension"
                        )
                else:
                    result["missing_files"].append("sovits_model")
            else:
                result["missing_files"].append("sovits_model")
                result["validation_errors"].append("SoVITS model path is not set")

            # 检查文件大小是否合理
            for file_type, size in result["file_sizes"].items():
                if size < 1024 * 1024:  # 小于1MB
                    result["validation_errors"].append(
                        f"{file_type} file seems too small ({size} bytes)"
                    )
                elif size > 10 * 1024 * 1024 * 1024:  # 大于10GB
                    result["validation_errors"].append(
                        f"{file_type} file seems too large ({size} bytes)"
                    )

            result["all_files_exist"] = (
                result["gpt_model_exists"] and result["sovits_model_exists"]
            )

        except Exception as e:
            result["validation_errors"].append(f"Validation error: {str(e)}")

        return result

    def get_model_files_info(self):
        """获取所有模型文件的详细信息 - 修复版本"""
        files_info = {
            "gpt_model": {
                "path": self.gpt_model_path,
                "exists": False,
                "size": 0,
                "modified_at": None,
            },
            "sovits_model": {
                "path": self.sovits_model_path,
                "exists": False,
                "size": 0,
                "modified_at": None,
            },
        }

        for file_type, info in files_info.items():
            file_path = info["path"]
            if file_path and os.path.exists(file_path):
                try:
                    stat = os.stat(file_path)
                    info.update(
                        {
                            "exists": True,
                            "size": stat.st_size,
                            "modified_at": datetime.fromtimestamp(
                                stat.st_mtime
                            ).isoformat(),
                        }
                    )
                except OSError:
                    pass  # 保持默认值

        return files_info

    def can_be_used(self):
        """检查模型是否可以使用"""
        if self.status != "active":
            return False, "Model is not active"

        validation = self.validate_model_files()
        if not validation["all_files_exist"]:
            return (
                False,
                f"Missing model files: {', '.join(validation['missing_files'])}",
            )

        if validation["validation_errors"]:
            return (
                False,
                f"File validation errors: {'; '.join(validation['validation_errors'])}",
            )

        return True, "Model is ready to use"

    def to_dict(self, include_paths=False, include_validation=False):
        """转换为字典 - 修复版本"""
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "model_type": self.model_type,
            "owner_id": self.owner_id,
            "supported_emotions": self.get_supported_emotions(),
            "supported_languages": self.get_supported_languages(),
            "voice_characteristics": self.voice_characteristics,
            "quality_score": self.quality_score,
            "download_count": self.download_count,
            "usage_count": self.usage_count,
            "status": self.status,
            "is_public": self.is_public,
            "is_featured": self.is_featured,
            "review_status": self.review_status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": [tag.to_dict() for tag in self.tags],
        }

        # 包含文件路径信息
        if include_paths:
            data.update(
                {
                    "gpt_model_path": self.gpt_model_path,
                    "sovits_model_path": self.sovits_model_path,
                }
            )

        # 包含验证信息
        if include_validation:
            validation = self.validate_model_files()
            can_use, use_message = self.can_be_used()
            data.update(
                {
                    "file_validation": validation,
                    "can_be_used": can_use,
                    "use_status_message": use_message,
                    "files_info": self.get_model_files_info(),
                }
            )

        return data

    def __repr__(self):
        return f"<VoiceModel {self.name} ({self.model_type})>"


class Tag(db.Model):
    """标签模型"""

    __tablename__ = "tags"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(200))
    color = db.Column(db.String(7), default="#007bff")  # 十六进制颜色代码
    usage_count = db.Column(db.Integer, default=0, index=True)  # 使用次数
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # 是否活跃

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __init__(self, **kwargs):
        """初始化时验证标签名称"""
        super().__init__(**kwargs)

        if self.name:
            self.name = self.name.strip()
            if not self.name:
                raise ValueError("Tag name cannot be empty")
            if len(self.name) > 50:
                raise ValueError("Tag name cannot exceed 50 characters")

    @classmethod
    def get_or_create(cls, name, description=None, color=None):
        """获取或创建标签 - 线程安全版本"""
        if not name or not name.strip():
            raise ValueError("Tag name cannot be empty")

        name = name.strip()

        # 尝试获取现有标签
        tag = cls.query.filter_by(name=name).first()

        if not tag:
            try:
                # 创建新标签
                tag = cls(name=name, description=description, color=color or "#007bff")
                db.session.add(tag)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                # 可能是并发创建，再次尝试获取
                tag = cls.query.filter_by(name=name).first()
                if not tag:
                    raise e

        return tag

    def increment_usage(self):
        """增加使用次数 - 线程安全版本"""
        try:
            db.session.execute(
                db.text("UPDATE tags SET usage_count = usage_count + 1 WHERE id = :id"),
                {"id": self.id},
            )
            db.session.commit()
            self.usage_count += 1
        except Exception as e:
            db.session.rollback()
            raise e

    def decrement_usage(self):
        """减少使用次数 - 当模型被删除时调用"""
        try:
            db.session.execute(
                db.text(
                    "UPDATE tags SET usage_count = GREATEST(0, usage_count - 1) WHERE id = :id"
                ),
                {"id": self.id},
            )
            db.session.commit()
            self.usage_count = max(0, self.usage_count - 1)
        except Exception as e:
            db.session.rollback()
            raise e

    def can_be_deleted(self):
        """检查标签是否可以被删除"""
        if self.usage_count > 0:
            return False, f"Tag is used by {self.usage_count} models"
        return True, "Tag can be deleted"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "usage_count": self.usage_count,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Tag {self.name} (used {self.usage_count} times)>"
