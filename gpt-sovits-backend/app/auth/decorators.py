from functools import wraps
from flask import request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models.user import User
from app.utils.exceptions import AuthenticationError, AuthorizationError
from app.utils.helpers import get_client_ip, get_user_agent, log_user_action


def auth_required(f):
    """需要认证的装饰器"""

    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        try:
            current_user_id = get_jwt_identity()
            current_user = User.query.get(current_user_id)

            if not current_user or not current_user.is_active:
                raise AuthenticationError("User account is inactive")

            # 将当前用户添加到请求上下文
            request.current_user = current_user

            return f(*args, **kwargs)
        except Exception as e:
            if isinstance(e, (AuthenticationError, AuthorizationError)):
                raise e
            raise AuthenticationError("Invalid token")

    return decorated_function


def admin_required(f):
    """需要管理员权限的装饰器"""

    @wraps(f)
    @auth_required
    def decorated_function(*args, **kwargs):
        current_user = request.current_user

        if not current_user.is_admin():
            log_user_action(
                user_id=current_user.id,
                action="unauthorized_access_attempt",
                resource_type="admin_function",
                details=f"Attempted to access {request.endpoint}",
            )
            raise AuthorizationError("Administrator privileges required")

        return f(*args, **kwargs)

    return decorated_function


def auditor_required(f):
    """需要审核员或管理员权限的装饰器"""

    @wraps(f)
    @auth_required
    def decorated_function(*args, **kwargs):
        current_user = request.current_user

        if not current_user.is_auditor():
            log_user_action(
                user_id=current_user.id,
                action="unauthorized_access_attempt",
                resource_type="auditor_function",
                details=f"Attempted to access {request.endpoint}",
            )
            raise AuthorizationError("Auditor privileges required")

        return f(*args, **kwargs)

    return decorated_function


def owner_or_admin_required(resource_getter):
    """需要资源所有者或管理员权限的装饰器"""

    def decorator(f):
        @wraps(f)
        @auth_required
        def decorated_function(*args, **kwargs):
            current_user = request.current_user

            # 获取资源
            resource = resource_getter(*args, **kwargs)

            if not resource:
                raise AuthorizationError("Resource not found")

            # 检查权限：管理员或资源所有者
            is_owner = (
                hasattr(resource, "owner_id") and resource.owner_id == current_user.id
            )
            is_user_resource = (
                hasattr(resource, "user_id") and resource.user_id == current_user.id
            )

            if not (current_user.is_admin() or is_owner or is_user_resource):
                log_user_action(
                    user_id=current_user.id,
                    action="unauthorized_resource_access",
                    resource_type=resource.__class__.__name__,
                    resource_id=getattr(resource, "id", None),
                    details="Attempted to access resource without permission",
                )
                raise AuthorizationError(
                    "You do not have permission to access this resource"
                )

            # 将资源添加到请求上下文
            request.current_resource = resource

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def rate_limit(requests_per_minute=60):
    """简单的速率限制装饰器"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from app.extensions import redis_client

            # 获取客户端标识符
            if hasattr(request, "current_user"):
                identifier = f"user:{request.current_user.id}"
            else:
                identifier = f"ip:{get_client_ip()}"

            # Redis键
            key = f"rate_limit:{identifier}:{request.endpoint}"

            try:
                # 获取当前请求数
                current_requests = redis_client.get(key)
                if current_requests is None:
                    # 首次请求
                    redis_client.setex(key, 60, 1)
                else:
                    current_requests = int(current_requests)
                    if current_requests >= requests_per_minute:
                        from app.utils.exceptions import RateLimitError

                        raise RateLimitError(
                            f"Rate limit exceeded: {requests_per_minute} requests per minute"
                        )

                    # 增加请求计数
                    redis_client.incr(key)

            except Exception as e:
                # Redis错误时允许请求通过
                current_app.logger.warning(f"Rate limiting failed: {e}")

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def api_key_required(f):
    """API密钥认证装饰器"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("X-API-Key") or request.args.get("api_key")

        if not api_key:
            raise AuthenticationError("API key required")

        # 验证API密钥（这里简化处理，实际应该查询数据库）
        # 可以扩展为支持用户API密钥
        if api_key != current_app.config.get("MASTER_API_KEY"):
            raise AuthenticationError("Invalid API key")

        return f(*args, **kwargs)

    return decorated_function


def log_action(action, resource_type=None):
    """记录操作日志的装饰器"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = None
            resource_id = None

            # 获取用户ID
            if hasattr(request, "current_user"):
                user_id = request.current_user.id

            # 获取资源ID
            if hasattr(request, "current_resource"):
                resource_id = getattr(request.current_resource, "id", None)
            elif "id" in kwargs:
                resource_id = kwargs["id"]

            try:
                # 执行原函数
                result = f(*args, **kwargs)

                # 记录成功操作
                log_user_action(
                    user_id=user_id,
                    action=action,
                    resource_type=resource_type or f.__name__,
                    resource_id=resource_id,
                    details=f"Successfully executed {action}",
                )

                return result

            except Exception as e:
                # 记录失败操作
                log_user_action(
                    user_id=user_id,
                    action=f"{action}_failed",
                    resource_type=resource_type or f.__name__,
                    resource_id=resource_id,
                    details=f"Failed to execute {action}: {str(e)}",
                )
                raise

        return decorated_function

    return decorator


def verify_ownership(resource_class, id_param="id"):
    """验证资源所有权的装饰器"""

    def decorator(f):
        @wraps(f)
        @auth_required
        def decorated_function(*args, **kwargs):
            current_user = request.current_user
            resource_id = kwargs.get(id_param)

            if not resource_id:
                raise AuthorizationError("Resource ID required")

            resource = resource_class.query.get(resource_id)
            if not resource:
                raise AuthorizationError("Resource not found")

            # 检查所有权
            owner_field = "user_id" if hasattr(resource, "user_id") else "owner_id"
            if hasattr(resource, owner_field):
                if (
                    getattr(resource, owner_field) != current_user.id
                    and not current_user.is_admin()
                ):
                    raise AuthorizationError("You do not own this resource")

            request.current_resource = resource
            return f(*args, **kwargs)

        return decorated_function

    return decorator
