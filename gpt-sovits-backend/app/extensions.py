from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail
from celery import Celery
import redis

# 数据库
db = SQLAlchemy()
migrate = Migrate()

# JWT认证
jwt = JWTManager()

# 跨域
cors = CORS()

# 邮件
mail = Mail()

# Redis
redis_client = None

# Celery
celery = Celery()

def init_extensions(app):
    """初始化所有扩展"""
    global redis_client
    
    # 初始化数据库
    db.init_app(app)
    migrate.init_app(app, db)
    
    # 初始化JWT
    jwt.init_app(app)
    
    # 初始化CORS
    cors.init_app(app)
    
    # 初始化邮件
    mail.init_app(app)
    
    # 初始化Redis
    redis_client = redis.from_url(app.config['REDIS_URL'])
    
    # 初始化Celery
    init_celery(app)

def init_celery(app):
    """初始化Celery"""
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_routes={
            'app.services.voice_clone_service.clone_voice_task': {'queue': 'voice_clone'},
            'app.services.tts_service.generate_speech_task': {'queue': 'tts'},
        }
    )
    
    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery