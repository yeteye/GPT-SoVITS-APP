# ./gpt-sovits-backend/app/models/audit.py
from datetime import datetime
from app.extensions import db
import uuid
import json


class AuditLog(db.Model):
    """审计日志模型"""

    __tablename__ = "audit_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 操作信息
    action = db.Column(db.String(50), nullable=False)  # 操作类型
    resource_type = db.Column(db.String(50), nullable=False)  # 资源类型
    resource_id = db.Column(db.String(36))  # 资源ID

    # 用户信息
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"))
    ip_address = db.Column(db.String(45))  # 支持IPv6
    user_agent = db.Column(db.String(500))

    # 操作详情
    old_values = db.Column(db.Text)  # JSON格式存储修改前的值
    new_values = db.Column(db.Text)  # JSON格式存储修改后的值
    description = db.Column(db.Text)  # 操作描述

    # 结果信息
    status = db.Column(db.String(20), default="success")  # success, failed, error
    error_message = db.Column(db.Text)

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # 关联关系
    user = db.relationship("User", backref="audit_logs")

    @classmethod
    def log_action(
        cls,
        action,
        resource_type,
        user_id=None,
        resource_id=None,
        old_values=None,
        new_values=None,
        description=None,
        ip_address=None,
        user_agent=None,
        status="success",
        error_message=None,
    ):
        """记录操作日志"""
        log = cls(
            action=action,
            resource_type=resource_type,
            user_id=user_id,
            resource_id=resource_id,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message,
        )
        db.session.add(log)
        db.session.commit()
        return log

    def get_old_values(self):
        """获取修改前的值"""
        if self.old_values:
            return json.loads(self.old_values)
        return {}

    def get_new_values(self):
        """获取修改后的值"""
        if self.new_values:
            return json.loads(self.new_values)
        return {}

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "old_values": self.get_old_values(),
            "new_values": self.get_new_values(),
            "description": self.description,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<AuditLog {self.action} on {self.resource_type}>"


class UserUpload(db.Model):
    """用户上传文件记录"""

    __tablename__ = "user_uploads"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)

    # 文件信息
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False)  # 文件大小(字节)
    file_type = db.Column(db.String(50), nullable=False)  # audio, model, image等
    mime_type = db.Column(db.String(100))
    file_hash = db.Column(db.String(64))  # SHA256哈希值，用于去重

    # 文件状态
    status = db.Column(
        db.String(20), default="uploaded"
    )  # uploaded, processing, processed, failed
    is_deleted = db.Column(db.Boolean, default=False)

    # 关联信息
    related_task_id = db.Column(db.String(36))  # 关联的任务ID
    related_model_id = db.Column(db.String(36))  # 关联的模型ID

    # 元数据
    file_metadata = db.Column(db.Text)  # JSON格式存储文件元数据

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def set_metadata(self, metadata):
        """设置元数据"""
        self.file_metadata = json.dumps(metadata)

    def get_metadata(self):
        """获取元数据"""
        if self.file_metadata:
            return json.loads(self.file_metadata)
        return {}

    def mark_deleted(self):
        """标记为已删除"""
        self.is_deleted = True
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "mime_type": self.mime_type,
            "status": self.status,
            "related_task_id": self.related_task_id,
            "related_model_id": self.related_model_id,
            "file_metadata": self.get_metadata(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<UserUpload {self.filename}>"
