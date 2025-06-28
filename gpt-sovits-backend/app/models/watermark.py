# app/models/watermark.py
from datetime import datetime
from app.extensions import db
import uuid
import json
import secrets
import string


class Watermark(db.Model):
    """音频水印模型 - 修复外键关系"""

    __tablename__ = "watermarks"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    watermark_code = db.Column(db.String(64), unique=True, nullable=False, index=True)

    # 用户关联 - 修复：移除冗余的username字段
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)

    # 模型关联
    model_id = db.Column(db.String(36), db.ForeignKey("voice_models.id"))

    # 水印属性
    code_length = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    file_info = db.Column(db.Text)

    # 使用统计
    usage_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_used = db.Column(db.DateTime)

    # 状态
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # 关联关系 - 修复：简化关系定义
    user = db.relationship("User", backref=db.backref("watermarks", lazy=True))
    model = db.relationship("VoiceModel", backref=db.backref("watermarks", lazy=True))

    @classmethod
    def generate_watermark_code(cls, length: int = 16) -> str:
        """生成水印识别码"""
        if length == 8:
            return "".join(secrets.choice(string.digits) for _ in range(8))
        elif length == 16:
            chars = string.ascii_lowercase + string.digits
            return "".join(secrets.choice(chars) for _ in range(16))
        elif length == 32:
            return secrets.token_hex(16)
        else:
            chars = string.ascii_lowercase + string.digits
            return "".join(secrets.choice(chars) for _ in range(length))

    @classmethod
    def create_for_user(
        cls,
        user_id: str,
        model_id: str = None,
        code_length: int = 16,
        description: str = "",
    ):
        """为用户创建水印 - 修复：移除username存储"""
        max_attempts = 10
        for _ in range(max_attempts):
            watermark_code = cls.generate_watermark_code(code_length)

            # 检查是否已存在
            existing = cls.query.filter_by(watermark_code=watermark_code).first()
            if not existing:
                watermark = cls(
                    watermark_code=watermark_code,
                    user_id=user_id,
                    model_id=model_id,
                    code_length=code_length,
                    description=description,
                )
                db.session.add(watermark)
                db.session.commit()
                return watermark

        raise Exception("无法生成唯一的水印码")

    def increment_usage(self):
        """增加使用次数"""
        self.usage_count += 1
        self.last_used = datetime.utcnow()
        db.session.commit()

    def set_file_info(self, file_info: dict):
        """设置文件信息"""
        self.file_info = json.dumps(file_info)

    def get_file_info(self):
        """获取文件信息"""
        if self.file_info:
            return json.loads(self.file_info)
        return {}

    def to_dict(self):
        """转换为字典 - 修复：动态获取用户名"""
        return {
            "id": self.id,
            "watermark_code": self.watermark_code,
            "username": self.username,  # 动态获取
            "user_id": self.user_id,
            "model_id": self.model_id,
            "code_length": self.code_length,
            "description": self.description,
            "file_info": self.get_file_info(),
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "is_active": self.is_active,
        }

    def __repr__(self):
        return f"<Watermark {self.watermark_code}>"


class WatermarkVerificationLog(db.Model):
    """水印验证日志"""

    __tablename__ = "watermark_verification_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 水印信息
    watermark_code = db.Column(db.String(64), nullable=False, index=True)
    original_filename = db.Column(db.String(255))

    # 提取结果
    extraction_accuracy = db.Column(db.Float)
    extracted_code = db.Column(db.String(64))
    success = db.Column(db.Boolean, nullable=False)

    # 客户端信息
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))

    # 时间戳
    verified_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # 附加信息
    verification_details = db.Column(db.Text)  # JSON格式存储详细信息

    def set_verification_details(self, details: dict):
        """设置验证详细信息"""
        self.verification_details = json.dumps(details)

    def get_verification_details(self):
        """获取验证详细信息"""
        if self.verification_details:
            return json.loads(self.verification_details)
        return {}

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "watermark_code": self.watermark_code,
            "original_filename": self.original_filename,
            "extraction_accuracy": self.extraction_accuracy,
            "extracted_code": self.extracted_code,
            "success": self.success,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "verified_at": self.verified_at.isoformat(),
            "verification_details": self.get_verification_details(),
        }

    def __repr__(self):
        return f"<WatermarkVerificationLog {self.watermark_code}>"
