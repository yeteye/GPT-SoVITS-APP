# ./gpt-sovits-backend/app/services/__init__.py

from flask import current_app


def init_services():
    """根据环境初始化服务"""
    try:
        if current_app.config.get("TESTING", False):
            # 测试环境：导入但不使用Celery装饰器
            from app.services.voice_clone_service import start_voice_clone_task
            from app.services.tts_service import generate_speech_task

            current_app.logger.info("Services initialized for testing environment")
            return {
                "voice_clone_service": start_voice_clone_task,
                "tts_service": generate_speech_task,
            }
        else:
            # 生产环境：正常导入
            from app.services.voice_clone_service import start_voice_clone_task
            from app.services.tts_service import generate_speech_task

            current_app.logger.info("Services initialized for production environment")
            return {
                "voice_clone_service": start_voice_clone_task,
                "tts_service": generate_speech_task,
            }
    except Exception as e:
        current_app.logger.error(f"Failed to initialize services: {e}")
        return None


# 导出主要服务函数
__all__ = ["init_services"]
