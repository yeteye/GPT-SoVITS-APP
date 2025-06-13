class APIException(Exception):
    """API异常基类"""

    def __init__(self, message, code="API_ERROR", status_code=400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(APIException):
    """验证错误"""

    def __init__(self, message, field=None):
        code = "VALIDATION_ERROR"
        if field:
            code = f"INVALID_{field.upper()}"
        super().__init__(message, code, 422)


class AuthenticationError(APIException):
    """认证错误"""

    def __init__(self, message="Authentication required"):
        super().__init__(message, "AUTHENTICATION_ERROR", 401)


class AuthorizationError(APIException):
    """授权错误"""

    def __init__(self, message="Insufficient permissions"):
        super().__init__(message, "AUTHORIZATION_ERROR", 403)


class ResourceNotFoundError(APIException):
    """资源未找到错误"""

    def __init__(self, resource_type="Resource"):
        message = f"{resource_type} not found"
        super().__init__(message, "RESOURCE_NOT_FOUND", 404)


class ResourceConflictError(APIException):
    """资源冲突错误"""

    def __init__(self, message="Resource already exists"):
        super().__init__(message, "RESOURCE_CONFLICT", 409)


class RateLimitError(APIException):
    """频率限制错误"""

    def __init__(self, message="Rate limit exceeded"):
        super().__init__(message, "RATE_LIMIT_EXCEEDED", 429)


class ServiceUnavailableError(APIException):
    """服务不可用错误"""

    def __init__(self, message="Service temporarily unavailable"):
        super().__init__(message, "SERVICE_UNAVAILABLE", 503)


class FileUploadError(APIException):
    """文件上传错误"""

    def __init__(self, message="File upload failed"):
        super().__init__(message, "FILE_UPLOAD_ERROR", 400)


class AudioProcessingError(APIException):
    """音频处理错误"""

    def __init__(self, message="Audio processing failed"):
        super().__init__(message, "AUDIO_PROCESSING_ERROR", 400)


class ModelNotFoundError(APIException):
    """模型未找到错误"""

    def __init__(self, message="Voice model not found"):
        super().__init__(message, "MODEL_NOT_FOUND", 404)


class TaskNotFoundError(APIException):
    """任务未找到错误"""

    def __init__(self, message="Task not found"):
        super().__init__(message, "TASK_NOT_FOUND", 404)


class TaskProcessingError(APIException):
    """任务处理错误"""

    def __init__(self, message="Task processing failed"):
        super().__init__(message, "TASK_PROCESSING_ERROR", 500)
