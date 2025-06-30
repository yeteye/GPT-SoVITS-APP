# ./gpt-sovits-backend/app/utils/exceptions.py (修复版)
"""
统一的异常处理系统
提供一致的错误响应格式和状态码
"""
import logging
import time
import datetime

logger = logging.getLogger(__name__)


class APIException(Exception):
    """API异常基类 - 改进版本"""

    def __init__(self, message, code=None, status_code=400, details=None):
        self.message = str(message)
        self.code = code or self.__class__.__name__.upper()
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self):
        """转换为字典格式"""
        error_dict = {
            "success": False,
            "message": self.message,
            "code": self.code,
            "status_code": self.status_code,
        }

        if self.details:
            error_dict["details"] = self.details

        return error_dict

    def __str__(self):
        return f"{self.code}: {self.message}"

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.code}): {self.message}>"


class ValidationError(APIException):
    """验证错误 - 422 Unprocessable Entity"""

    def __init__(self, message, field=None, details=None):
        code = "VALIDATION_ERROR"
        if field:
            code = f"INVALID_{field.upper()}"

        error_details = {"field": field} if field else {}
        if details:
            error_details.update(details)

        super().__init__(message, code, 422, error_details)


class AuthenticationError(APIException):
    """认证错误 - 401 Unauthorized"""

    def __init__(self, message="Authentication required", details=None):
        super().__init__(message, "AUTHENTICATION_ERROR", 401, details)


class AuthorizationError(APIException):
    """授权错误 - 403 Forbidden"""

    def __init__(self, message="Insufficient permissions", details=None):
        super().__init__(message, "AUTHORIZATION_ERROR", 403, details)


class ResourceNotFoundError(APIException):
    """资源未找到错误 - 404 Not Found"""

    def __init__(self, resource_type="Resource", resource_id=None, details=None):
        message = f"{resource_type} not found"
        if resource_id:
            message += f" (ID: {resource_id})"

        error_details = {"resource_type": resource_type}
        if resource_id:
            error_details["resource_id"] = resource_id
        if details:
            error_details.update(details)

        super().__init__(message, "RESOURCE_NOT_FOUND", 404, error_details)


class ResourceConflictError(APIException):
    """资源冲突错误 - 409 Conflict"""

    def __init__(
        self, message="Resource already exists", resource_type=None, details=None
    ):
        error_details = {}
        if resource_type:
            error_details["resource_type"] = resource_type
        if details:
            error_details.update(details)

        super().__init__(message, "RESOURCE_CONFLICT", 409, error_details)


class RateLimitError(APIException):
    """频率限制错误 - 429 Too Many Requests"""

    def __init__(
        self, message="Rate limit exceeded", limit=None, window=None, details=None
    ):
        error_details = {}
        if limit:
            error_details["limit"] = limit
        if window:
            error_details["window_seconds"] = window
        if details:
            error_details.update(details)

        super().__init__(message, "RATE_LIMIT_EXCEEDED", 429, error_details)


class FileUploadError(APIException):
    """文件上传错误 - 400 Bad Request"""

    def __init__(self, message="File upload failed", file_type=None, details=None):
        error_details = {}
        if file_type:
            error_details["file_type"] = file_type
        if details:
            error_details.update(details)

        super().__init__(message, "FILE_UPLOAD_ERROR", 400, error_details)


class ModelNotFoundError(APIException):
    """模型未找到错误 - 404 Not Found"""

    def __init__(self, model_id=None, model_type=None, details=None):
        message = "Voice model not found"
        if model_id:
            message += f" (ID: {model_id})"

        error_details = {"resource_type": "voice_model"}
        if model_id:
            error_details["model_id"] = model_id
        if model_type:
            error_details["model_type"] = model_type
        if details:
            error_details.update(details)

        super().__init__(message, "MODEL_NOT_FOUND", 404, error_details)


class TaskNotFoundError(APIException):
    """任务未找到错误 - 404 Not Found"""

    def __init__(self, task_id=None, task_type=None, details=None):
        message = "Task not found"
        if task_id:
            message += f" (ID: {task_id})"

        error_details = {"resource_type": "task"}
        if task_id:
            error_details["task_id"] = task_id
        if task_type:
            error_details["task_type"] = task_type
        if details:
            error_details.update(details)

        super().__init__(message, "TASK_NOT_FOUND", 404, error_details)


class AudioProcessingError(APIException):
    """音频处理错误 - 422 Unprocessable Entity"""

    def __init__(
        self, message="Audio processing failed", audio_format=None, details=None
    ):
        error_details = {}
        if audio_format:
            error_details["audio_format"] = audio_format
        if details:
            error_details.update(details)

        super().__init__(message, "AUDIO_PROCESSING_ERROR", 422, error_details)


class TaskProcessingError(APIException):
    """任务处理错误 - 500 Internal Server Error"""

    def __init__(self, message="Task processing failed", task_type=None, details=None):
        error_details = {}
        if task_type:
            error_details["task_type"] = task_type
        if details:
            error_details.update(details)

        super().__init__(message, "TASK_PROCESSING_ERROR", 500, error_details)


class ServiceUnavailableError(APIException):
    """服务不可用错误 - 503 Service Unavailable"""

    def __init__(
        self, message="Service temporarily unavailable", service_name=None, details=None
    ):
        error_details = {}
        if service_name:
            error_details["service_name"] = service_name
        if details:
            error_details.update(details)

        super().__init__(message, "SERVICE_UNAVAILABLE", 503, error_details)


class ConfigurationError(APIException):
    """配置错误 - 500 Internal Server Error"""

    def __init__(self, message="Configuration error", config_key=None, details=None):
        error_details = {}
        if config_key:
            error_details["config_key"] = config_key
        if details:
            error_details.update(details)

        super().__init__(message, "CONFIGURATION_ERROR", 500, error_details)


class DatabaseError(APIException):
    """数据库错误 - 500 Internal Server Error"""

    def __init__(
        self, message="Database operation failed", operation=None, details=None
    ):
        error_details = {}
        if operation:
            error_details["operation"] = operation
        if details:
            error_details.update(details)

        super().__init__(message, "DATABASE_ERROR", 500, error_details)


class ExternalServiceError(APIException):
    """外部服务错误 - 502 Bad Gateway"""

    def __init__(
        self, message="External service error", service_name=None, details=None
    ):
        error_details = {}
        if service_name:
            error_details["service_name"] = service_name
        if details:
            error_details.update(details)

        super().__init__(message, "EXTERNAL_SERVICE_ERROR", 502, error_details)


class SecurityError(APIException):
    """安全错误 - 403 Forbidden"""

    def __init__(
        self, message="Security violation detected", violation_type=None, details=None
    ):
        error_details = {}
        if violation_type:
            error_details["violation_type"] = violation_type
        if details:
            error_details.update(details)

        super().__init__(message, "SECURITY_ERROR", 403, error_details)


# 错误处理装饰器
def handle_exceptions(func):
    """统一异常处理装饰器"""
    from functools import wraps
    from flask import jsonify

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIException as e:
            logger.warning(f"API Exception in {func.__name__}: {e}")
            return jsonify(e.to_dict()), e.status_code
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            error = APIException(
                message="Internal server error",
                code="INTERNAL_ERROR",
                status_code=500,
                details={"function": func.__name__},
            )
            return jsonify(error.to_dict()), 500

    return wrapper


def create_error_response(error, request_id=None):
    """创建标准化的错误响应"""
    if isinstance(error, APIException):
        response_data = error.to_dict()
    elif isinstance(error, Exception):
        response_data = {
            "success": False,
            "message": str(error),
            "code": "UNKNOWN_ERROR",
            "status_code": 500,
        }
    else:
        response_data = {
            "success": False,
            "message": "Unknown error occurred",
            "code": "UNKNOWN_ERROR",
            "status_code": 500,
        }

    # 添加请求ID（如果提供）
    if request_id:
        response_data["request_id"] = request_id

    # 添加时间戳
    from datetime import datetime

    response_data["timestamp"] = datetime.now().isoformat()

    return response_data


# 全局错误处理器注册函数
def register_error_handlers(app):
    """注册全局错误处理器"""
    from flask import jsonify, request
    import traceback
    import uuid

    @app.errorhandler(APIException)
    def handle_api_exception(e):
        """处理API异常"""
        request_id = getattr(request, "id", str(uuid.uuid4()))
        logger.warning(f"API Exception [{request_id}]: {e}")

        response_data = create_error_response(e, request_id)
        return jsonify(response_data), e.status_code

    @app.errorhandler(400)
    def handle_bad_request(error):
        """处理400错误"""
        request_id = getattr(request, "id", str(uuid.uuid4()))

        response_data = {
            "success": False,
            "message": "Bad request",
            "code": "BAD_REQUEST",
            "status_code": 400,
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
        }
        return jsonify(response_data), 400

    @app.errorhandler(404)
    def handle_not_found(error):
        """处理404错误"""
        request_id = getattr(request, "id", str(uuid.uuid4()))

        response_data = {
            "success": False,
            "message": "Resource not found",
            "code": "NOT_FOUND",
            "status_code": 404,
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
        }
        return jsonify(response_data), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """处理405错误"""
        request_id = getattr(request, "id", str(uuid.uuid4()))

        response_data = {
            "success": False,
            "message": "Method not allowed",
            "code": "METHOD_NOT_ALLOWED",
            "status_code": 405,
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
        }
        return jsonify(response_data), 405

    @app.errorhandler(413)
    def handle_file_too_large(error):
        """处理413错误 - 文件过大"""
        request_id = getattr(request, "id", str(uuid.uuid4()))

        max_size = app.config.get("MAX_CONTENT_LENGTH", 0)
        max_size_mb = max_size / (1024 * 1024) if max_size else 0

        response_data = {
            "success": False,
            "message": (
                f"File too large (max: {max_size_mb:.1f}MB)"
                if max_size_mb
                else "File too large"
            ),
            "code": "FILE_TOO_LARGE",
            "status_code": 413,
            "details": {"max_size_mb": max_size_mb} if max_size_mb else {},
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
        }
        return jsonify(response_data), 413

    @app.errorhandler(500)
    def handle_internal_error(error):
        """处理500错误"""
        from app.extensions import db

        request_id = getattr(request, "id", str(uuid.uuid4()))

        # 记录详细错误信息
        logger.error(f"Internal error [{request_id}]: {error}")
        logger.error(f"Traceback: {traceback.format_exc()}")

        # 回滚数据库事务
        try:
            db.session.rollback()
        except Exception as rollback_error:
            logger.error(f"Failed to rollback database: {rollback_error}")

        response_data = {
            "success": False,
            "message": "Internal server error",
            "code": "INTERNAL_ERROR",
            "status_code": 500,
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
        }

        # 在开发环境中包含更多错误信息
        if app.debug:
            response_data["details"] = {
                "error_type": type(error).__name__,
                "error_message": str(error),
            }

        return jsonify(response_data), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """处理未预期的错误"""
        request_id = getattr(request, "id", str(uuid.uuid4()))

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """处理未预期的错误"""
        request_id = getattr(request, "id", str(uuid.uuid4()))

        logger.error(f"Unexpected error [{request_id}]: {error}", exc_info=True)

        # 回滚数据库事务
        try:
            from app.extensions import db

            db.session.rollback()
        except Exception as rollback_error:
            logger.error(f"Failed to rollback database: {rollback_error}")

        response_data = {
            "success": False,
            "message": "An unexpected error occurred",
            "code": "UNEXPECTED_ERROR",
            "status_code": 500,
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
        }

        # 在开发环境中包含错误详情
        if app.debug:
            response_data["details"] = {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc().split("\n"),
            }

        return jsonify(response_data), 500

    # 添加请求ID中间件
    @app.before_request
    def add_request_id():
        """为每个请求添加唯一ID"""
        request.id = str(uuid.uuid4())

    # 添加CORS错误处理
    @app.after_request
    def after_request(response):
        """处理响应后的操作"""
        # 添加请求ID到响应头
        if hasattr(request, "id"):
            response.headers["X-Request-ID"] = request.id

        # 记录API调用
        if request.endpoint and not request.endpoint.startswith("static"):
            duration = getattr(request, "start_time", None)
            if duration:
                duration = time.time() - duration
                logger.info(
                    f"API {request.method} {request.path} - {response.status_code} - {duration:.3f}s"
                )

        return response

    # 添加请求计时
    @app.before_request
    def before_request():
        """请求开始前的操作"""
        import time

        request.start_time = time.time()


# 业务逻辑异常类
class BusinessLogicError(APIException):
    """业务逻辑错误"""

    def __init__(self, message, business_code=None, details=None):
        error_details = {}
        if business_code:
            error_details["business_code"] = business_code
        if details:
            error_details.update(details)

        super().__init__(message, "BUSINESS_LOGIC_ERROR", 422, error_details)


class ModelValidationError(ValidationError):
    """模型验证错误"""

    def __init__(self, message, model_type=None, validation_failures=None):
        details = {}
        if model_type:
            details["model_type"] = model_type
        if validation_failures:
            details["validation_failures"] = validation_failures

        super().__init__(message, "model_validation", details)


class TaskStateError(BusinessLogicError):
    """任务状态错误"""

    def __init__(self, message, current_state=None, expected_states=None, task_id=None):
        details = {}
        if current_state:
            details["current_state"] = current_state
        if expected_states:
            details["expected_states"] = expected_states
        if task_id:
            details["task_id"] = task_id

        super().__init__(message, "INVALID_TASK_STATE", details)


class QuotaExceededError(BusinessLogicError):
    """配额超出错误"""

    def __init__(self, message, quota_type=None, current_usage=None, limit=None):
        details = {}
        if quota_type:
            details["quota_type"] = quota_type
        if current_usage is not None:
            details["current_usage"] = current_usage
        if limit is not None:
            details["limit"] = limit

        super().__init__(message, "QUOTA_EXCEEDED", details)


class DependencyError(ServiceUnavailableError):
    """依赖服务错误"""

    def __init__(self, message, dependency_name=None, dependency_status=None):
        details = {}
        if dependency_name:
            details["dependency_name"] = dependency_name
        if dependency_status:
            details["dependency_status"] = dependency_status

        super().__init__(message, dependency_name, details)


# 异常收集器 - 用于批量验证
class ValidationErrorCollector:
    """验证错误收集器"""

    def __init__(self):
        self.errors = []

    def add_error(self, field, message):
        """添加验证错误"""
        self.errors.append({"field": field, "message": message})

    def add_field_error(self, field, message):
        """添加字段验证错误"""
        self.add_error(field, message)

    def has_errors(self):
        """检查是否有错误"""
        return len(self.errors) > 0

    def raise_if_errors(self):
        """如果有错误则抛出异常"""
        if self.has_errors():
            error_messages = []
            error_details = {"field_errors": self.errors}

            for error in self.errors:
                error_messages.append(f"{error['field']}: {error['message']}")

            message = "Validation failed: " + "; ".join(error_messages)
            raise ValidationError(message, details=error_details)

    def get_errors(self):
        """获取所有错误"""
        return self.errors.copy()

    def clear(self):
        """清除所有错误"""
        self.errors.clear()


# 错误上下文管理器
class ErrorContext:
    """错误上下文管理器 - 用于添加额外的错误信息"""

    def __init__(self, operation=None, resource_type=None, resource_id=None):
        self.operation = operation
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.start_time = None

    def __enter__(self):
        import time

        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and issubclass(exc_type, APIException):
            # 为API异常添加上下文信息
            duration = time.time() - self.start_time if self.start_time else None

            context_details = {}
            if self.operation:
                context_details["operation"] = self.operation
            if self.resource_type:
                context_details["resource_type"] = self.resource_type
            if self.resource_id:
                context_details["resource_id"] = self.resource_id
            if duration:
                context_details["operation_duration"] = round(duration, 3)

            # 合并上下文信息到异常详情中
            if context_details:
                if not exc_val.details:
                    exc_val.details = {}
                exc_val.details.update(context_details)

        # 不抑制异常
        return False


# 智能错误恢复装饰器
def with_error_recovery(retry_count=3, backoff_factor=1.0, recoverable_exceptions=None):
    """带错误恢复的装饰器"""

    def decorator(func):
        from functools import wraps
        import time
        import random

        @wraps(func)
        def wrapper(*args, **kwargs):
            if recoverable_exceptions is None:
                recoverable = (
                    DatabaseError,
                    ExternalServiceError,
                    ServiceUnavailableError,
                )
            else:
                recoverable = recoverable_exceptions

            last_exception = None

            for attempt in range(retry_count + 1):
                try:
                    return func(*args, **kwargs)
                except recoverable as e:
                    last_exception = e

                    if attempt < retry_count:
                        # 计算退避时间
                        delay = backoff_factor * (2**attempt) + random.uniform(0, 1)
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay:.2f}s"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {retry_count + 1} attempts failed for {func.__name__}: {e}"
                        )
                except Exception as e:
                    # 不可恢复的异常直接抛出
                    logger.error(f"Non-recoverable error in {func.__name__}: {e}")
                    raise

            # 所有重试都失败了
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


# 错误统计和监控
class ErrorMetrics:
    """错误指标收集器"""

    def __init__(self):
        self.error_counts = {}
        self.error_rates = {}

    def record_error(self, error_type, endpoint=None):
        """记录错误"""
        key = f"{error_type}:{endpoint}" if endpoint else error_type
        self.error_counts[key] = self.error_counts.get(key, 0) + 1

    def get_error_count(self, error_type, endpoint=None):
        """获取错误计数"""
        key = f"{error_type}:{endpoint}" if endpoint else error_type
        return self.error_counts.get(key, 0)

    def get_top_errors(self, limit=10):
        """获取最频繁的错误"""
        sorted_errors = sorted(
            self.error_counts.items(), key=lambda x: x[1], reverse=True
        )
        return sorted_errors[:limit]

    def reset(self):
        """重置统计"""
        self.error_counts.clear()
        self.error_rates.clear()


# 全局错误指标实例
error_metrics = ErrorMetrics()


# 错误报告功能
def report_critical_error(error, context=None):
    """报告严重错误"""
    try:
        # 记录到日志
        logger.critical(f"Critical error: {error}", exc_info=True)

        # 可以在这里添加额外的报告逻辑
        # 例如：发送邮件、发送到监控系统等

        # 记录错误指标
        error_type = type(error).__name__
        endpoint = context.get("endpoint") if context else None
        error_metrics.record_error(error_type, endpoint)

    except Exception as e:
        # 报告错误时发生的错误不应该影响主要流程
        logger.error(f"Failed to report critical error: {e}")


# 导出主要类和函数
__all__ = [
    "APIException",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "ResourceNotFoundError",
    "ResourceConflictError",
    "RateLimitError",
    "FileUploadError",
    "ModelNotFoundError",
    "TaskNotFoundError",
    "AudioProcessingError",
    "TaskProcessingError",
    "ServiceUnavailableError",
    "ConfigurationError",
    "DatabaseError",
    "ExternalServiceError",
    "SecurityError",
    "BusinessLogicError",
    "ModelValidationError",
    "TaskStateError",
    "QuotaExceededError",
    "DependencyError",
    "ValidationErrorCollector",
    "ErrorContext",
    "ErrorMetrics",
    "handle_exceptions",
    "create_error_response",
    "register_error_handlers",
    "with_error_recovery",
    "report_critical_error",
    "error_metrics",
]
