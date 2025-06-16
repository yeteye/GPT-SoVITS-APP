# ./gpt-sovits-backend/app/config.py
import os
from datetime import timedelta


class Config:
    # 基础配置
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"

    # 数据库配置 - 修改为本地数据库
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or "mysql+pymysql://root:your_password@localhost:3306/gpt_sovits_db?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_timeout": 20,
        "max_overflow": 10,  # 增加连接池大小
        "pool_size": 20,  # 增加基础连接数
    }

    # JWT配置
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or "jwt-secret-string"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # 文件上传配置 - 使用绝对路径
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER") or "/var/www/gpt-sovits/uploads"
    MAX_CONTENT_LENGTH = int(
        os.environ.get("MAX_CONTENT_LENGTH") or 50 * 1024 * 1024
    )  # 增加到50MB
    ALLOWED_AUDIO_EXTENSIONS = {"wav", "mp3", "flac", "m4a", "ogg", "aac"}
    ALLOWED_MODEL_EXTENSIONS = {"pth", "index", "json", "ckpt", "safetensors"}

    # 安全配置 - 生产环境调整
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = os.environ.get("HTTPS_ENABLED", "false").lower() == "true"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # 音频处理配置
    AUDIO_SAMPLE_RATE = int(os.environ.get("AUDIO_SAMPLE_RATE") or 22050)  # 提高采样率
    AUDIO_MIN_DURATION = int(os.environ.get("AUDIO_MIN_DURATION") or 3)
    AUDIO_MAX_DURATION = int(
        os.environ.get("AUDIO_MAX_DURATION") or 120
    )  # 增加最大时长

    # Celery配置 - 本地Redis
    CELERY_BROKER_URL = (
        os.environ.get("CELERY_BROKER_URL") or "redis://localhost:6379/0"
    )
    CELERY_RESULT_BACKEND = (
        os.environ.get("CELERY_RESULT_BACKEND") or "redis://localhost:6379/0"
    )

    # Celery任务配置
    CELERY_TASK_SERIALIZER = "json"
    CELERY_ACCEPT_CONTENT = ["json"]
    CELERY_RESULT_SERIALIZER = "json"
    CELERY_TIMEZONE = "Asia/Shanghai"  # 设置时区
    CELERY_ENABLE_UTC = True

    # Redis配置
    REDIS_URL = os.environ.get("REDIS_URL") or "redis://localhost:6379/1"
    REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")  # 如果Redis有密码

    # 邮件配置
    MAIL_SERVER = os.environ.get("MAIL_SERVER") or "smtp.gmail.com"
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 587)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ["true", "on", "1"]
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")

    # GPT-SoVITS模型配置 - 绝对路径
    SOVITS_MODEL_PATH = (
        os.environ.get("SOVITS_MODEL_PATH") or "/opt/gpt-sovits/models/sovits"
    )
    GPT_MODEL_PATH = os.environ.get("GPT_MODEL_PATH") or "/opt/gpt-sovits/models/gpt"

    # 模型加载配置
    MODEL_CACHE_SIZE = int(os.environ.get("MODEL_CACHE_SIZE") or 3)  # 缓存模型数量
    ENABLE_MODEL_PRELOAD = (
        os.environ.get("ENABLE_MODEL_PRELOAD", "false").lower() == "true"
    )

    # 业务配置
    MAX_CONCURRENT_TASKS = int(
        os.environ.get("MAX_CONCURRENT_TASKS") or 10
    )  # 根据服务器性能调整
    TASK_TIMEOUT = int(os.environ.get("TASK_TIMEOUT") or 600)  # 增加超时时间

    # 用户限制
    MAX_MODELS_PER_USER = int(os.environ.get("MAX_MODELS_PER_USER") or 20)
    MAX_DAILY_TASKS = int(os.environ.get("MAX_DAILY_TASKS") or 100)

    # 分页配置
    ITEMS_PER_PAGE = int(os.environ.get("ITEMS_PER_PAGE") or 20)

    # 日志配置
    LOG_LEVEL = os.environ.get("LOG_LEVEL") or "INFO"
    LOG_FILE = os.environ.get("LOG_FILE") or "/var/log/gpt-sovits/app.log"
    LOG_MAX_BYTES = int(os.environ.get("LOG_MAX_BYTES") or 10 * 1024 * 1024)  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get("LOG_BACKUP_COUNT") or 5)

    # 系统监控配置
    ENABLE_METRICS = os.environ.get("ENABLE_METRICS", "true").lower() == "true"
    METRICS_PORT = int(os.environ.get("METRICS_PORT") or 9090)


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True

    # 开发环境使用相对路径
    UPLOAD_FOLDER = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "uploads"
    )
    SOVITS_MODEL_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "models", "sovits"
    )
    GPT_MODEL_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "models", "gpt"
    )

    # 开发环境降低限制
    MAX_CONCURRENT_TASKS = 2
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False

    # 生产环境强制HTTPS
    SESSION_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = "https"

    # 生产环境日志
    LOG_LEVEL = "WARNING"


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False

    # 测试环境使用临时目录
    import tempfile

    UPLOAD_FOLDER = tempfile.mkdtemp()
    SOVITS_MODEL_PATH = tempfile.mkdtemp()
    GPT_MODEL_PATH = tempfile.mkdtemp()


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
