# ./gpt-sovits-backend/app/config.py (修改后的版本)
import os
from datetime import timedelta


def build_database_url():
    """构建数据库URL，支持两种配置方式"""
    # 方式1：直接使用 DATABASE_URL
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        return database_url

    # 方式2：从分离的环境变量构建
    mysql_host = os.environ.get("MYSQL_HOST", "localhost")
    mysql_port = os.environ.get("MYSQL_PORT", "3306")
    mysql_user = os.environ.get("MYSQL_USER", "root")
    mysql_password = os.environ.get("MYSQL_PASSWORD", "")
    mysql_database = os.environ.get("MYSQL_DATABASE", "gpt_sovits_db")

    # URL编码密码中的特殊字符
    if mysql_password:
        import urllib.parse

        mysql_password = urllib.parse.quote_plus(mysql_password)

    return f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8mb4"


def get_env_bool(key, default=False):
    """安全地获取布尔环境变量"""
    value = os.environ.get(key, str(default)).lower()
    return value in ["true", "1", "yes", "on"]


def get_env_int(key, default=0):
    """安全地获取整数环境变量"""
    try:
        return int(os.environ.get(key, default))
    except (ValueError, TypeError):
        return default


def get_env_float(key, default=0.0):
    """安全地获取浮点数环境变量"""
    try:
        return float(os.environ.get(key, default))
    except (ValueError, TypeError):
        return default


def get_env_list(key, default=None, separator=","):
    """安全地获取列表环境变量"""
    if default is None:
        default = []
    value = os.environ.get(key)
    if not value:
        return default
    return [item.strip() for item in value.split(separator) if item.strip()]


class Config:
    # ================================
    # 基础配置
    # ================================
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"

    # ================================
    # 数据库配置
    # ================================
    SQLALCHEMY_DATABASE_URI = build_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = get_env_bool("SQLALCHEMY_ECHO", False)

    # 数据库连接池配置
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": get_env_int("DB_POOL_RECYCLE", 300),
        "pool_timeout": get_env_int("DB_POOL_TIMEOUT", 20),
        "max_overflow": get_env_int("DB_MAX_OVERFLOW", 10),
        "pool_size": get_env_int("DB_POOL_SIZE", 5),
        "connect_args": {
            "charset": "utf8mb4",
            "connect_timeout": get_env_int("DB_CONNECT_TIMEOUT", 60),
            "read_timeout": get_env_int("DB_READ_TIMEOUT", 30),
            "write_timeout": get_env_int("DB_WRITE_TIMEOUT", 30),
        },
    }

    # ================================
    # JWT配置
    # ================================
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or "jwt-secret-string"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=get_env_int("JWT_ACCESS_TOKEN_EXPIRES_HOURS", 24)
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=get_env_int("JWT_REFRESH_TOKEN_EXPIRES_DAYS", 30)
    )

    # ================================
    # 文件上传配置 - 修改：支持GPT+SoVITS文件格式
    # ================================
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER") or os.path.abspath("./uploads")
    MAX_CONTENT_LENGTH = get_env_int(
        "MAX_CONTENT_LENGTH", 1024 * 1024 * 1024
    )  # 修改：提高到1GB支持大模型文件

    # 修改：允许的文件扩展名 - 支持GPT(.pth)和SoVITS(.ckpt)
    ALLOWED_AUDIO_EXTENSIONS = set(
        get_env_list(
            "ALLOWED_AUDIO_EXTENSIONS", ["wav", "mp3", "flac", "m4a", "ogg", "aac"]
        )
    )
    ALLOWED_MODEL_EXTENSIONS = set(
        get_env_list(
            "ALLOWED_MODEL_EXTENSIONS", ["pth", "ckpt"]  # 修改：只允许pth和ckpt文件
        )
    )

    # ================================
    # 安全配置
    # ================================
    WTF_CSRF_ENABLED = get_env_bool("WTF_CSRF_ENABLED", True)
    SESSION_COOKIE_SECURE = get_env_bool("SESSION_COOKIE_SECURE", False)
    SESSION_COOKIE_HTTPONLY = get_env_bool("SESSION_COOKIE_HTTPONLY", True)
    SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")

    # ================================
    # 音频处理配置
    # ================================
    AUDIO_SAMPLE_RATE = get_env_int("AUDIO_SAMPLE_RATE", 22050)
    AUDIO_MIN_DURATION = get_env_int("AUDIO_MIN_DURATION", 3)
    AUDIO_MAX_DURATION = get_env_int("AUDIO_MAX_DURATION", 120)

    # ================================
    # Celery配置
    # ================================
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND") or os.environ.get(
        "CELERY_BROKER_URL"
    )

    # Celery任务配置
    CELERY_TASK_SERIALIZER = os.environ.get("CELERY_TASK_SERIALIZER", "json")
    CELERY_ACCEPT_CONTENT = get_env_list("CELERY_ACCEPT_CONTENT", ["json"])
    CELERY_RESULT_SERIALIZER = os.environ.get("CELERY_RESULT_SERIALIZER", "json")
    CELERY_TIMEZONE = os.environ.get("CELERY_TIMEZONE", "Asia/Shanghai")
    CELERY_ENABLE_UTC = get_env_bool("CELERY_ENABLE_UTC", True)

    # ================================
    # Redis配置
    # ================================
    REDIS_URL = os.environ.get("REDIS_URL")
    REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")

    # ================================
    # 邮件配置
    # ================================
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = get_env_int("MAIL_PORT", 587)
    MAIL_USE_TLS = get_env_bool("MAIL_USE_TLS", True)
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")

    # ================================
    # GPT-SoVITS模型配置 - 修改：支持新的目录结构
    # ================================
    SOVITS_MODEL_PATH = os.environ.get("SOVITS_MODEL_PATH") or os.path.abspath(
        "./models/sovits"
    )
    GPT_MODEL_PATH = os.environ.get("GPT_MODEL_PATH") or os.path.abspath("./models/gpt")

    # 模型加载配置
    MODEL_CACHE_SIZE = get_env_int("MODEL_CACHE_SIZE", 3)
    ENABLE_MODEL_PRELOAD = get_env_bool("ENABLE_MODEL_PRELOAD", False)

    # 新增：模型文件验证配置
    VALIDATE_MODEL_FILES_ON_UPLOAD = get_env_bool(
        "VALIDATE_MODEL_FILES_ON_UPLOAD", True
    )
    REQUIRE_BOTH_MODEL_FILES = get_env_bool(
        "REQUIRE_BOTH_MODEL_FILES", True
    )  # 要求同时上传GPT和SoVITS文件

    # ================================
    # 业务配置
    # ================================
    MAX_CONCURRENT_TASKS = get_env_int("MAX_CONCURRENT_TASKS", 5)
    TASK_TIMEOUT = get_env_int("TASK_TIMEOUT", 600)

    # 用户限制
    MAX_MODELS_PER_USER = get_env_int("MAX_MODELS_PER_USER", 20)
    MAX_DAILY_TASKS = get_env_int("MAX_DAILY_TASKS", 100)

    # 任务并发限制
    MAX_CONCURRENT_VC_TASKS = get_env_int("MAX_CONCURRENT_VC_TASKS", 2)
    MAX_CONCURRENT_TTS_TASKS = get_env_int("MAX_CONCURRENT_TTS_TASKS", 5)
    MAX_DAILY_VC_TASKS = get_env_int("MAX_DAILY_VC_TASKS", 10)
    MAX_DAILY_TTS_TASKS = get_env_int("MAX_DAILY_TTS_TASKS", 50)

    # ================================
    # 语言支持配置 - 新增：支持的语言列表
    # ================================
    SUPPORTED_LANGUAGES = {
        "zh": {"name": "中文", "display_name": "Chinese (Simplified)"},
        "ja": {"name": "日语", "display_name": "Japanese"},
        "en": {"name": "英语", "display_name": "English (US)"},
    }

    # ================================
    # 分页配置
    # ================================
    ITEMS_PER_PAGE = get_env_int("ITEMS_PER_PAGE", 20)

    # ================================
    # 日志配置
    # ================================
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE = os.environ.get("LOG_FILE", "./logs/app.log")
    LOG_MAX_BYTES = get_env_int("LOG_MAX_BYTES", 10 * 1024 * 1024)  # 10MB
    LOG_BACKUP_COUNT = get_env_int("LOG_BACKUP_COUNT", 5)

    # ================================
    # 系统监控配置
    # ================================
    ENABLE_METRICS = get_env_bool("ENABLE_METRICS", True)
    METRICS_PORT = get_env_int("METRICS_PORT", 9090)

    # ================================
    # API密钥配置
    # ================================
    MASTER_API_KEY = os.environ.get("MASTER_API_KEY")

    # ================================
    # 水印功能配置
    # ================================
    WATERMARK_ENABLED = get_env_bool("WATERMARK_ENABLED", True)

    # 水印算法参数
    WATERMARK_START_FREQ = get_env_int("WATERMARK_START_FREQ", 1000)
    WATERMARK_DELTA = get_env_int("WATERMARK_DELTA", 30)
    WATERMARK_STRENGTH = get_env_float("WATERMARK_STRENGTH", 2.0)
    WATERMARK_BOOST = get_env_float("WATERMARK_BOOST", 0.3)
    WATERMARK_ERROR_CORRECTION = get_env_bool("WATERMARK_ERROR_CORRECTION", True)

    # 水印策略配置
    WATERMARK_SPLIT_STRATEGY = os.environ.get("WATERMARK_SPLIT_STRATEGY", "quartile")
    WATERMARK_FREQ_SELECTION = os.environ.get("WATERMARK_FREQ_SELECTION", "prime")

    # 水印质量配置
    WATERMARK_MIN_ACCURACY = get_env_float("WATERMARK_MIN_ACCURACY", 0.7)
    WATERMARK_FUZZY_MATCH_THRESHOLD = get_env_float(
        "WATERMARK_FUZZY_MATCH_THRESHOLD", 0.6
    )

    # 自动水印配置
    AUTO_WATERMARK_TTS = get_env_bool("AUTO_WATERMARK_TTS", True)
    AUTO_WATERMARK_VOICE_CLONE = get_env_bool("AUTO_WATERMARK_VOICE_CLONE", True)

    # 水印存储配置
    WATERMARK_CLEANUP_DAYS = get_env_int("WATERMARK_CLEANUP_DAYS", 90)
    MAX_WATERMARKS_PER_USER = get_env_int("MAX_WATERMARKS_PER_USER", 10)


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = get_env_bool("SQLALCHEMY_ECHO", False)

    # 开发环境降低限制
    MAX_CONCURRENT_TASKS = get_env_int("MAX_CONCURRENT_TASKS", 2)
    SESSION_COOKIE_SECURE = False

    # 开发环境文件大小限制可以更宽松
    MAX_CONTENT_LENGTH = get_env_int("MAX_CONTENT_LENGTH", 1024 * 1024 * 1024)  # 1GB

    # 开发环境水印配置
    WATERMARK_START_FREQ = get_env_int("WATERMARK_START_FREQ", 800)
    WATERMARK_DELTA = get_env_int("WATERMARK_DELTA", 25)
    WATERMARK_STRENGTH = get_env_float("WATERMARK_STRENGTH", 1.5)
    WATERMARK_BOOST = get_env_float("WATERMARK_BOOST", 0.2)
    WATERMARK_MIN_ACCURACY = get_env_float("WATERMARK_MIN_ACCURACY", 0.5)


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False

    # 生产环境强制HTTPS
    SESSION_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = "https"

    # 生产环境日志
    LOG_LEVEL = "WARNING"

    # 生产环境更严格的限制
    MAX_CONCURRENT_TASKS = get_env_int("MAX_CONCURRENT_TASKS", 5)

    # 生产环境水印配置（更保守的参数）
    WATERMARK_START_FREQ = get_env_int("WATERMARK_START_FREQ", 1200)
    WATERMARK_DELTA = get_env_int("WATERMARK_DELTA", 35)
    WATERMARK_STRENGTH = get_env_float("WATERMARK_STRENGTH", 2.5)
    WATERMARK_BOOST = get_env_float("WATERMARK_BOOST", 0.4)
    WATERMARK_MIN_ACCURACY = get_env_float("WATERMARK_MIN_ACCURACY", 0.8)


class TestingConfig(Config):
    TESTING = True
    # 测试环境使用SQLite
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_ENGINE_OPTIONS = {}  # SQLite不需要连接池配置

    # 测试环境使用临时目录
    import tempfile

    UPLOAD_FOLDER = tempfile.mkdtemp()
    SOVITS_MODEL_PATH = tempfile.mkdtemp()
    GPT_MODEL_PATH = tempfile.mkdtemp()

    # 测试环境降低限制
    MAX_CONCURRENT_TASKS = 1
    MAX_CONCURRENT_VC_TASKS = 1
    MAX_CONCURRENT_TTS_TASKS = 1

    # 测试环境水印配置
    WATERMARK_START_FREQ = 500
    WATERMARK_DELTA = 20
    WATERMARK_STRENGTH = 1.0
    WATERMARK_BOOST = 0.1
    WATERMARK_MIN_ACCURACY = 0.5
    MAX_WATERMARKS_PER_USER = 5

    # 禁用外部服务
    CELERY_BROKER_URL = None
    CELERY_RESULT_BACKEND = None
    REDIS_URL = None
    WATERMARK_ENABLED = True  # 测试水印功能


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
