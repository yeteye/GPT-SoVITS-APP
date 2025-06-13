from flask import Blueprint, request, jsonify, current_app, url_for
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
from app.extensions import db
from app.models.user import User, AuthToken
from app.auth.utils import (
    generate_verification_token,
    verify_token,
    send_verification_email,
    send_password_reset_email,
    check_login_attempts,
    record_login_attempt,
    validate_password_strength,
    send_welcome_email,
)
from app.auth.decorators import rate_limit
from app.utils.validators import validate_email, validate_username, validate_password
from app.utils.exceptions import (
    ValidationError,
    AuthenticationError,
    ResourceConflictError,
)
from app.utils.helpers import create_response, get_client_ip, log_user_action

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
@rate_limit(requests_per_minute=5)
def register():
    """用户注册"""
    try:
        data = request.get_json()

        if not data:
            raise ValidationError("Request body is required")

        # 验证必需字段
        username = data.get("username", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not username or not email or not password:
            raise ValidationError("Username, email and password are required")

        # 验证输入格式
        validate_username(username)
        validate_email(email)
        validate_password(password)

        # 检查用户名和邮箱是否已存在
        if User.query.filter_by(username=username).first():
            raise ResourceConflictError("Username already exists")

        if User.query.filter_by(email=email).first():
            raise ResourceConflictError("Email already registered")

        # 创建新用户
        user = User(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        # 记录注册日志
        log_user_action(
            user_id=user.id,
            action="user_register",
            resource_type="user",
            resource_id=user.id,
            details="User registered successfully",
        )

        # 生成验证令牌并发送邮件
        verification_token = generate_verification_token(user.id)
        verification_url = url_for(
            "auth.verify_email", token=verification_token, _external=True
        )

        if send_verification_email(user, verification_url):
            message = "Registration successful. Please check your email to verify your account."
        else:
            message = "Registration successful, but failed to send verification email."

        # 生成访问令牌（可选：注册后自动登录）
        access_token, refresh_token = user.generate_tokens()

        return (
            jsonify(
                create_response(
                    success=True,
                    message=message,
                    data={
                        "user": user.to_dict(),
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                    },
                )
            ),
            201,
        )

    except (ValidationError, ResourceConflictError) as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Registration error: {e}")
        return jsonify(create_response(False, "Registration failed")), 500


@auth_bp.route("/login", methods=["POST"])
@rate_limit(requests_per_minute=10)
def login():
    """用户登录"""
    try:
        data = request.get_json()

        if not data:
            raise ValidationError("Request body is required")

        # 获取登录凭据
        identifier = data.get("identifier", "").strip().lower()  # 用户名或邮箱
        password = data.get("password", "")

        if not identifier or not password:
            raise ValidationError("Username/email and password are required")

        # 检查登录尝试次数
        client_ip = get_client_ip()
        if not check_login_attempts(client_ip):
            raise AuthenticationError(
                "Too many failed login attempts. Please try again later."
            )

        # 查找用户
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

        if not user or not user.check_password(password):
            # 记录失败的登录尝试
            record_login_attempt(client_ip, success=False)
            raise AuthenticationError("Invalid username/email or password")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        # 登录成功
        record_login_attempt(client_ip, success=True)
        user.update_last_login()

        # 生成令牌
        access_token, refresh_token = user.generate_tokens()

        # 记录登录日志
        log_user_action(
            user_id=user.id,
            action="user_login",
            resource_type="user",
            resource_id=user.id,
            details="User logged in successfully",
        )

        return jsonify(
            create_response(
                success=True,
                message="Login successful",
                data={
                    "user": user.to_dict(include_sensitive=True),
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                },
            )
        )

    except (ValidationError, AuthenticationError) as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Login error: {e}")
        return jsonify(create_response(False, "Login failed")), 500


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """用户登出"""
    try:
        user_id = get_jwt_identity()

        # 记录登出日志
        log_user_action(
            user_id=user_id,
            action="user_logout",
            resource_type="user",
            resource_id=user_id,
            details="User logged out",
        )

        # 这里可以添加令牌黑名单逻辑
        # 简化处理：客户端删除令牌即可

        return jsonify(create_response(success=True, message="Logout successful"))

    except Exception as e:
        current_app.logger.error(f"Logout error: {e}")
        return jsonify(create_response(False, "Logout failed")), 500


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """刷新访问令牌"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        # 生成新的访问令牌
        access_token = create_access_token(
            identity=user.id,
            additional_claims={"role": user.role, "username": user.username},
        )

        return jsonify(
            create_response(
                success=True,
                message="Token refreshed",
                data={"access_token": access_token},
            )
        )

    except AuthenticationError as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {e}")
        return jsonify(create_response(False, "Token refresh failed")), 500


@auth_bp.route("/verify-email/<token>")
def verify_email(token):
    """验证邮箱"""
    try:
        user = verify_token(token, "email_verification")

        if not user:
            return (
                jsonify(
                    create_response(False, "Invalid or expired verification token")
                ),
                400,
            )

        if user.is_verified:
            return jsonify(create_response(True, "Email already verified"))

        # 标记邮箱为已验证
        user.is_verified = True
        db.session.commit()

        # 发送欢迎邮件
        send_welcome_email(user)

        # 记录验证日志
        log_user_action(
            user_id=user.id,
            action="email_verified",
            resource_type="user",
            resource_id=user.id,
            details="Email verification completed",
        )

        return jsonify(
            create_response(success=True, message="Email verified successfully")
        )

    except Exception as e:
        current_app.logger.error(f"Email verification error: {e}")
        return jsonify(create_response(False, "Email verification failed")), 500


@auth_bp.route("/forgot-password", methods=["POST"])
@rate_limit(requests_per_minute=3)
def forgot_password():
    """忘记密码"""
    try:
        data = request.get_json()

        if not data:
            raise ValidationError("Request body is required")

        email = data.get("email", "").strip().lower()

        if not email:
            raise ValidationError("Email is required")

        validate_email(email)

        user = User.query.filter_by(email=email).first()

        if user:
            # 生成重置令牌
            reset_token = AuthToken.create_reset_token(user.id)
            reset_url = url_for(
                "auth.reset_password", token=reset_token, _external=True
            )

            # 发送重置邮件
            send_password_reset_email(user, reset_url)

            # 记录重置请求日志
            log_user_action(
                user_id=user.id,
                action="password_reset_requested",
                resource_type="user",
                resource_id=user.id,
                details="Password reset requested",
            )

        # 无论用户是否存在都返回相同消息，防止邮箱枚举
        return jsonify(
            create_response(
                success=True,
                message="If the email exists, a password reset link has been sent",
            )
        )

    except ValidationError as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Forgot password error: {e}")
        return jsonify(create_response(False, "Password reset request failed")), 500


@auth_bp.route("/reset-password/<token>", methods=["POST"])
@rate_limit(requests_per_minute=5)
def reset_password(token):
    """重置密码"""
    try:
        data = request.get_json()

        if not data:
            raise ValidationError("Request body is required")

        new_password = data.get("password", "")

        if not new_password:
            raise ValidationError("New password is required")

        # 验证密码强度
        is_strong, message = validate_password_strength(new_password)
        if not is_strong:
            raise ValidationError(message)

        # 验证重置令牌
        user = AuthToken.verify_reset_token(token)

        if not user:
            raise AuthenticationError("Invalid or expired reset token")

        # 重置密码
        user.set_password(new_password)
        db.session.commit()

        # 撤销重置令牌
        reset_token = AuthToken.query.filter_by(token=token).first()
        if reset_token:
            reset_token.revoke()

        # 记录重置成功日志
        log_user_action(
            user_id=user.id,
            action="password_reset_completed",
            resource_type="user",
            resource_id=user.id,
            details="Password reset completed successfully",
        )

        return jsonify(
            create_response(success=True, message="Password reset successful")
        )

    except (ValidationError, AuthenticationError) as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Password reset error: {e}")
        return jsonify(create_response(False, "Password reset failed")), 500


@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    """修改密码"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            raise AuthenticationError("User not found")

        data = request.get_json()

        if not data:
            raise ValidationError("Request body is required")

        current_password = data.get("current_password", "")
        new_password = data.get("new_password", "")

        if not current_password or not new_password:
            raise ValidationError("Current password and new password are required")

        # 验证当前密码
        if not user.check_password(current_password):
            raise AuthenticationError("Current password is incorrect")

        # 验证新密码强度
        is_strong, message = validate_password_strength(new_password)
        if not is_strong:
            raise ValidationError(message)

        # 更新密码
        user.set_password(new_password)
        db.session.commit()

        # 记录密码修改日志
        log_user_action(
            user_id=user.id,
            action="password_changed",
            resource_type="user",
            resource_id=user.id,
            details="Password changed successfully",
        )

        return jsonify(
            create_response(success=True, message="Password changed successfully")
        )

    except (ValidationError, AuthenticationError) as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Change password error: {e}")
        return jsonify(create_response(False, "Password change failed")), 500
