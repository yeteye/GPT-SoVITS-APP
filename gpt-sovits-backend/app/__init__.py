# ./gpt-sovits-backend/app/__init__.py
import os
from flask import Flask
from app.extensions import init_extensions
from app.config import config


def create_app(config_name=None):
    """应用工厂函数"""
    if config_name is None:
        config_name = os.environ.get("FLASK_CONFIG", "default")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 初始化扩展
    init_extensions(app)

    # 注册蓝图
    register_blueprints(app)

    # 注册错误处理器
    register_error_handlers(app)

    # 创建上传目录
    create_upload_directories(app)

    return app


def register_blueprints(app):
    """注册蓝图"""
    from app.auth.routes import auth_bp
    from app.api.voice_clone import voice_clone_bp
    from app.api.tts import tts_bp
    from app.api.model_management import model_bp
    from app.api.admin import admin_bp
    from app.api.user import user_bp
    from app.api.health import health_bp  # 添加健康检查路由

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(voice_clone_bp, url_prefix="/api/voice-clone")
    app.register_blueprint(tts_bp, url_prefix="/api/tts")
    app.register_blueprint(model_bp, url_prefix="/api/models")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(user_bp, url_prefix="/api/user")
    app.register_blueprint(health_bp, url_prefix="/api")  # 添加健康检查路由


def register_error_handlers(app):
    """注册错误处理器"""
    from app.utils.exceptions import APIException
    from flask import jsonify
    import traceback

    @app.errorhandler(APIException)
    def handle_api_exception(e):
        return (
            jsonify({"success": False, "message": e.message, "code": e.code}),
            e.status_code,
        )

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify(
                {"success": False, "message": "Resource not found", "code": "NOT_FOUND"}
            ),
            404,
        )

    @app.errorhandler(500)
    def internal_error(error):
        # 记录错误详情
        app.logger.error(f"Internal error: {error}")
        app.logger.error(traceback.format_exc())

        # 回滚数据库事务
        from app.extensions import db

        db.session.rollback()

        return (
            jsonify(
                {
                    "success": False,
                    "message": "Internal server error",
                    "code": "INTERNAL_ERROR",
                }
            ),
            500,
        )

    @app.errorhandler(413)
    def file_too_large(error):
        return (
            jsonify(
                {
                    "success": False,
                    "message": "File too large",
                    "code": "FILE_TOO_LARGE",
                }
            ),
            413,
        )


def create_upload_directories(app):
    """创建上传目录"""
    upload_dirs = ["audio_samples", "models", "generated", "temp"]

    for dir_name in upload_dirs:
        dir_path = os.path.join(app.config["UPLOAD_FOLDER"], dir_name)
        os.makedirs(dir_path, exist_ok=True)
