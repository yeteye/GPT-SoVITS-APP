# ./gpt-sovits-backend/app/models/model.py
from datetime import datetime
from app.extensions import db
import uuid
import json

# 多对多关系表：模型-标签
model_tags = db.Table(
    "model_tags",
    db.Column(
        "model_id", db.String(36), db.ForeignKey("voice_models.id"), primary_key=True
    ),
    db.Column("tag_id", db.String(36), db.ForeignKey("tags.id"), primary_key=True),
)


class VoiceModel(db.Model):
    """语音模型"""

    __tablename__ = "voice_models"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 基本信息
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    # 模型类型: user_trained(用户训练), official(官方预训练)
    model_type = db.Column(db.String(20), default="user_trained", nullable=False)

    # 所有者信息
    owner_id = db.Column(db.String(36), db.ForeignKey("users.id"))

    # 模型文件路径
    model_path = db.Column(db.String(255), nullable=False)  # 主模型文件路径
    config_path = db.Column(db.String(255))  # 配置文件路径
    index_path = db.Column(db.String(255))  # 索引文件路径

    # 模型特性
    supported_emotions = db.Column(db.Text)  # JSON格式存储支持的情感列表
    supported_languages = db.Column(db.Text)  # JSON格式存储支持的语言列表
    voice_characteristics = db.Column(db.Text)  # 音色特征描述

    # 质量评分
    quality_score = db.Column(db.Float, default=0.0)  # 模型质量评分 0-10
    download_count = db.Column(db.Integer, default=0)  # 下载次数
    usage_count = db.Column(db.Integer, default=0)  # 使用次数

    # 状态信息
    status = db.Column(
        db.String(20), default="active", nullable=False
    )  # active, inactive, pending_review
    is_public = db.Column(db.Boolean, default=False, nullable=False)  # 是否公开
    is_featured = db.Column(db.Boolean, default=False, nullable=False)  # 是否为精选模型

    # 审核信息
    review_status = db.Column(
        db.String(20), default="pending"
    )  # pending, approved, rejected
    review_message = db.Column(db.Text)  # 审核意见
    reviewed_by = db.Column(db.String(36), db.ForeignKey("users.id"))
    reviewed_at = db.Column(db.DateTime)

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
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
    reviewer = db.relationship("User", foreign_keys=[reviewed_by])

    def set_supported_emotions(self, emotions):
        """设置支持的情感列表"""
        self.supported_emotions = json.dumps(emotions)

    def get_supported_emotions(self):
        """获取支持的情感列表"""
        if self.supported_emotions:
            return json.loads(self.supported_emotions)
        return ["neutral"]

    def set_supported_languages(self, languages):
        """设置支持的语言列表"""
        self.supported_languages = json.dumps(languages)

    def get_supported_languages(self):
        """获取支持的语言列表"""
        if self.supported_languages:
            return json.loads(self.supported_languages)
        return ["zh-CN"]

    def increment_usage(self):
        """增加使用次数"""
        self.usage_count += 1
        db.session.commit()

    def increment_download(self):
        """增加下载次数"""
        self.download_count += 1
        db.session.commit()

    def set_review_result(self, status, message, reviewer_id):
        """设置审核结果"""
        self.review_status = status
        self.review_message = message
        self.reviewed_by = reviewer_id
        self.reviewed_at = datetime.utcnow()

        if status == "approved":
            self.status = "active"
        elif status == "rejected":
            self.status = "inactive"

        db.session.commit()

    def to_dict(self, include_paths=False):
        """转换为字典"""
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

        if include_paths:
            data.update(
                {
                    "model_path": self.model_path,
                    "config_path": self.config_path,
                    "index_path": self.index_path,
                }
            )

        return data

    def __repr__(self):
        return f"<VoiceModel {self.name}>"


class Tag(db.Model):
    """标签模型"""

    __tablename__ = "tags"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    color = db.Column(db.String(7), default="#007bff")  # 十六进制颜色代码
    usage_count = db.Column(db.Integer, default=0)  # 使用次数

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @classmethod
    def get_or_create(cls, name, description=None):
        """获取或创建标签"""
        tag = cls.query.filter_by(name=name).first()
        if not tag:
            tag = cls(name=name, description=description)
            db.session.add(tag)
            db.session.commit()
        return tag

    def increment_usage(self):
        """增加使用次数"""
        self.usage_count += 1
        db.session.commit()

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "usage_count": self.usage_count,
        }

    def __repr__(self):
        return f"<Tag {self.name}>"
