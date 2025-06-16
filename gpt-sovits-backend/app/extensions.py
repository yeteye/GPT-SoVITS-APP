# ./gpt-sovits-backend/app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail
from celery import Celery
import redis

# 全局实例
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
mail = Mail()
redis_client = None
celery = None


def create_celery(app=None):
    """创建Celery实例"""
    celery = Celery(app.import_name if app else "gpt-sovits-backend")

    if app:
        celery.conf.update(
            broker_url=app.config["CELERY_BROKER_URL"],
            result_backend=app.config["CELERY_RESULT_BACKEND"],
            task_serializer="json",
            accept_content=["json"],
            result_serializer="json",
            timezone="UTC",
            enable_utc=True,
            task_routes={
                "app.services.voice_clone_service.*": {"queue": "voice_clone"},
                "app.services.tts_service.*": {"queue": "tts"},
            },
        )

        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery.Task = ContextTask

    return celery


def init_extensions(app):
    """初始化所有扩展"""
    global redis_client, celery

    # 初始化数据库
    db.init_app(app)
    migrate.init_app(app, db)

    # 初始化JWT
    jwt.init_app(app)

    # 初始化CORS
    cors.init_app(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

    # 初始化邮件
    if app.config.get("MAIL_SERVER"):
        mail.init_app(app)

    # 初始化Redis
    try:
        redis_client = redis.from_url(app.config["REDIS_URL"])
        redis_client.ping()  # 测试连接
    except Exception as e:
        app.logger.warning(f"Redis connection failed: {e}")
        redis_client = None

    # 初始化Celery
    celery = create_celery(app)
