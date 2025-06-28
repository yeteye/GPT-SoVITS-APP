# ./gpt-sovits-backend/app/auth/utils.py
import jwt
import secrets
from datetime import datetime, timedelta
from flask import current_app
from flask_mail import Message
from app.extensions import mail
from app.models.user import User, AuthToken
from app.utils.exceptions import AuthenticationError


def generate_verification_token(
    user_id, token_type="email_verification", expires_in_hours=24
):
    """生成验证令牌"""
    payload = {
        "user_id": user_id,
        "token_type": token_type,
        "exp": datetime.utcnow() + timedelta(hours=expires_in_hours),
        "iat": datetime.utcnow(),
    }

    token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

    return token


def verify_token(token, token_type="email_verification"):
    """验证令牌"""
    try:
        payload = jwt.decode(
            token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
        )

        if payload.get("token_type") != token_type:
            return None

        user_id = payload.get("user_id")
        user = User.query.get(user_id)

        return user

    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def send_verification_email(user, verification_url):
    """发送邮箱验证邮件"""
    subject = "Verify Your Email Address"

    html_body = f"""
    <h2>Welcome to GPT-SoVITS Platform!</h2>
    <p>Hi {user.username},</p>
    <p>Thank you for registering with our voice cloning platform. Please click the link below to verify your email address:</p>
    <p><a href="{verification_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
    <p>{verification_url}</p>
    <p>This link will expire in 24 hours.</p>
    <p>If you didn't create an account, please ignore this email.</p>
    <p>Best regards,<br>GPT-SoVITS Team</p>
    """

    text_body = f"""
    Welcome to GPT-SoVITS Platform!
    
    Hi {user.username},
    
    Thank you for registering with our voice cloning platform. Please visit the following link to verify your email address:
    
    {verification_url}
    
    This link will expire in 24 hours.
    
    If you didn't create an account, please ignore this email.
    
    Best regards,
    GPT-SoVITS Team
    """

    msg = Message(
        subject=subject, recipients=[user.email], html=html_body, body=text_body
    )

    try:
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send verification email: {e}")
        return False


def send_password_reset_email(user, reset_url):
    """发送密码重置邮件"""
    subject = "Reset Your Password"

    html_body = f"""
    <h2>Password Reset Request</h2>
    <p>Hi {user.username},</p>
    <p>We received a request to reset your password. Click the link below to create a new password:</p>
    <p><a href="{reset_url}" style="background-color: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
    <p>{reset_url}</p>
    <p>This link will expire in 24 hours.</p>
    <p>If you didn't request a password reset, please ignore this email or contact support if you have concerns.</p>
    <p>Best regards,<br>GPT-SoVITS Team</p>
    """

    text_body = f"""
    Password Reset Request
    
    Hi {user.username},
    
    We received a request to reset your password. Please visit the following link to create a new password:
    
    {reset_url}
    
    This link will expire in 24 hours.
    
    If you didn't request a password reset, please ignore this email or contact support if you have concerns.
    
    Best regards,
    GPT-SoVITS Team
    """

    msg = Message(
        subject=subject, recipients=[user.email], html=html_body, body=text_body
    )

    try:
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send password reset email: {e}")
        return False


def check_login_attempts(identifier, max_attempts=5, window_minutes=15):
    """检查登录尝试次数"""
    from app.extensions import redis_client

    key = f"login_attempts:{identifier}"

    try:
        attempts = redis_client.get(key)
        if attempts is None:
            return True

        attempts = int(attempts)
        if attempts >= max_attempts:
            return False

        return True

    except Exception:
        # Redis错误时允许登录
        return True


def record_login_attempt(identifier, success=False, max_attempts=5, window_minutes=15):
    """记录登录尝试"""
    from app.extensions import redis_client

    key = f"login_attempts:{identifier}"

    try:
        if success:
            # 登录成功，清除尝试记录
            redis_client.delete(key)
        else:
            # 登录失败，增加尝试次数
            current_attempts = redis_client.get(key)
            if current_attempts is None:
                redis_client.setex(key, window_minutes * 60, 1)
            else:
                redis_client.incr(key)

    except Exception as e:
        current_app.logger.warning(f"Failed to record login attempt: {e}")


def generate_session_token():
    """生成会话令牌"""
    return secrets.token_urlsafe(32)


def validate_password_strength(password):
    """验证密码强度"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"

    # 检查常见弱密码
    common_passwords = [
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
    ]

    if password.lower() in common_passwords:
        return False, "Password is too common"

    return True, "Password is strong"


def get_user_permissions(user):
    """获取用户权限列表"""
    permissions = ["user:read", "user:update_own"]

    if user.role >= 1:  # 审核员
        permissions.extend(["content:review", "model:review", "user:read_all"])

    if user.role >= 2:  # 管理员
        permissions.extend(
            [
                "user:create",
                "user:update_any",
                "user:delete",
                "model:create_official",
                "model:update_any",
                "model:delete_any",
                "system:manage",
            ]
        )

    return permissions


def check_permission(user, permission):
    """检查用户是否具有特定权限"""
    user_permissions = get_user_permissions(user)
    return permission in user_permissions


def create_audit_log_entry(
    user_id, action, resource_type, resource_id=None, details=None
):
    """创建审计日志条目"""
    from app.models.audit import AuditLog
    from app.utils.helpers import get_client_ip, get_user_agent

    return AuditLog.log_action(
        action=action,
        resource_type=resource_type,
        user_id=user_id,
        resource_id=resource_id,
        description=details,
        ip_address=get_client_ip(),
        user_agent=get_user_agent(),
    )


def clean_expired_tokens():
    """清理过期的令牌"""
    from app.extensions import db

    try:
        # 删除过期的认证令牌
        expired_tokens = AuthToken.query.filter(
            AuthToken.expires_at < datetime.utcnow(), AuthToken.is_revoked == False
        ).all()

        for token in expired_tokens:
            token.revoke()

        db.session.commit()
        return len(expired_tokens)

    except Exception as e:
        current_app.logger.error(f"Failed to clean expired tokens: {e}")
        db.session.rollback()
        return 0


def send_welcome_email(user):
    """发送欢迎邮件"""
    subject = "Welcome to GPT-SoVITS Platform!"

    html_body = f"""
    <h2>Welcome to GPT-SoVITS Platform!</h2>
    <p>Hi {user.username},</p>
    <p>Your account has been successfully created! You can now start using our voice cloning and text-to-speech services.</p>
    <p><strong>Getting Started:</strong></p>
    <ul>
        <li>Upload audio samples to create your voice models</li>
        <li>Use our text-to-speech service with various emotions</li>
        <li>Explore pre-trained voice models</li>
        <li>Manage your voice library</li>
    </ul>
    <p>If you have any questions, feel free to contact our support team.</p>
    <p>Happy voice cloning!</p>
    <p>Best regards,<br>GPT-SoVITS Team</p>
    """

    text_body = f"""
    Welcome to GPT-SoVITS Platform!
    
    Hi {user.username},
    
    Your account has been successfully created! You can now start using our voice cloning and text-to-speech services.
    
    Getting Started:
    - Upload audio samples to create your voice models
    - Use our text-to-speech service with various emotions
    - Explore pre-trained voice models
    - Manage your voice library
    
    If you have any questions, feel free to contact our support team.
    
    Happy voice cloning!
    
    Best regards,
    GPT-SoVITS Team
    """

    msg = Message(
        subject=subject, recipients=[user.email], html=html_body, body=text_body
    )

    try:
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send welcome email: {e}")
        return False
