# ./gpt-sovits-backend/app/models/user.py
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token
from app.extensions import db
import uuid
import secrets


class User(db.Model):
    """用户模型"""

    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # 用户信息
    avatar_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)

    # 权限级别: 0-普通用户, 1-审核员, 2-管理员
    role = db.Column(db.Integer, default=0, nullable=False)

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_login_at = db.Column(db.DateTime)

    # 关联关系
    voice_clone_tasks = db.relationship(
        "VoiceCloneTask", backref="user", lazy="dynamic"
    )
    tts_tasks = db.relationship("TTSTask", backref="user", lazy="dynamic")
    voice_models = db.relationship("VoiceModel", backref="owner", lazy="dynamic")
    uploads = db.relationship("UserUpload", backref="user", lazy="dynamic")
    auth_tokens = db.relationship("AuthToken", backref="user", lazy="dynamic")

    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def generate_tokens(self):
        """生成JWT令牌"""
        access_token = create_access_token(
            identity=self.id,
            additional_claims={"role": self.role, "username": self.username},
        )
        refresh_token = create_refresh_token(identity=self.id)
        return access_token, refresh_token

    def is_admin(self):
        """检查是否为管理员"""
        return self.role >= 2

    def is_auditor(self):
        """检查是否为审核员"""
        return self.role >= 1

    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login_at = datetime.utcnow()
        db.session.commit()

    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email if include_sensitive else None,
            "avatar_url": self.avatar_url,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "role": self.role,
            "created_at": self.created_at.isoformat(),
            "last_login_at": (
                self.last_login_at.isoformat() if self.last_login_at else None
            ),
        }
        return data

    def __repr__(self):
        return f"<User {self.username}>"


class AuthToken(db.Model):
    """认证令牌模型"""

    __tablename__ = "auth_tokens"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    token_type = db.Column(
        db.String(20), nullable=False
    )  # access, refresh, reset_password
    expires_at = db.Column(db.DateTime, nullable=False)
    is_revoked = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @classmethod
    def create_reset_token(cls, user_id, expires_in_hours=24):
        """创建密码重置令牌"""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)

        auth_token = cls(
            user_id=user_id,
            token=token,
            token_type="reset_password",
            expires_at=expires_at,
        )
        db.session.add(auth_token)
        db.session.commit()
        return token

    @classmethod
    def verify_reset_token(cls, token):
        """验证密码重置令牌"""
        auth_token = cls.query.filter_by(
            token=token, token_type="reset_password", is_revoked=False
        ).first()

        if auth_token and auth_token.expires_at > datetime.utcnow():
            return auth_token.user
        return None

    def revoke(self):
        """撤销令牌"""
        self.is_revoked = True
        db.session.commit()

    def __repr__(self):
        return f"<AuthToken {self.token_type} for user {self.user_id}>"
