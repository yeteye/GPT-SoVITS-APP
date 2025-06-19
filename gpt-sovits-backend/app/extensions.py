# ./gpt-sovits-backend/app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail

# 全局实例
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
mail = Mail()
redis_client = None
celery = None


def create_celery(app=None):
    """创建Celery实例 - 修复版本"""
    if not app or not app.config.get("CELERY_BROKER_URL"):
        return None

    try:
        from celery import Celery

        # 修复：使用正确的应用名称
        celery = Celery(app.import_name)

        if app:
            # 修复：确保所有Celery配置都正确传递
            celery.conf.update(
                broker_url=app.config["CELERY_BROKER_URL"],
                result_backend=app.config["CELERY_RESULT_BACKEND"],
                task_serializer=app.config.get("CELERY_TASK_SERIALIZER", "json"),
                accept_content=app.config.get("CELERY_ACCEPT_CONTENT", ["json"]),
                result_serializer=app.config.get("CELERY_RESULT_SERIALIZER", "json"),
                timezone=app.config.get("CELERY_TIMEZONE", "UTC"),
                enable_utc=app.config.get("CELERY_ENABLE_UTC", True),
                # 添加任务路由配置
                task_routes={
                    "app.services.voice_clone_service.*": {"queue": "voice_clone"},
                    "app.services.tts_service.*": {"queue": "tts"},
                },
                # 添加worker配置
                worker_prefetch_multiplier=1,
                task_acks_late=True,
                worker_max_tasks_per_child=1000,
            )

            # 修复：确保任务在Flask应用上下文中运行
            class ContextTask(celery.Task):
                def __call__(self, *args, **kwargs):
                    with app.app_context():
                        return self.run(*args, **kwargs)

            celery.Task = ContextTask

            # 自动发现任务
            celery.autodiscover_tasks(
                [
                    "app.services.voice_clone_service",
                    "app.services.tts_service",
                ]
            )

        return celery
    except ImportError:
        app.logger.warning("Celery not available")
        return None


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

    # 初始化邮件 - 只有在配置了邮件服务器时才初始化
    if app.config.get("MAIL_SERVER") and app.config.get("MAIL_USERNAME"):
        try:
            mail.init_app(app)
            app.logger.info("Mail service initialized")
        except Exception as e:
            app.logger.warning(f"Mail initialization failed: {e}")
    else:
        app.logger.info("Mail service not configured")

    # 初始化Redis - 可选
    if app.config.get("REDIS_URL"):
        try:
            import redis

            redis_client = redis.from_url(app.config["REDIS_URL"])
            redis_client.ping()  # 测试连接
            app.logger.info("Redis connected successfully")
        except Exception as e:
            app.logger.warning(f"Redis connection failed: {e}")
            redis_client = None
    else:
        app.logger.info("Redis not configured")

    # 初始化Celery - 可选
    if app.config.get("CELERY_BROKER_URL"):
        try:
            celery = create_celery(app)
            if celery:
                app.logger.info(
                    f"Celery initialized successfully - Broker: {app.config['CELERY_BROKER_URL']}"
                )

                # 验证配置
                app.logger.info(f"Celery broker: {celery.conf.broker_url}")
                app.logger.info(f"Celery backend: {celery.conf.result_backend}")
            else:
                app.logger.warning("Celery initialization failed")
        except Exception as e:
            app.logger.warning(f"Celery initialization failed: {e}")
            celery = None
    else:
        app.logger.info("Celery not configured")
