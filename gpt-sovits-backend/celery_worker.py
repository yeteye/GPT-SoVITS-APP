import os
from app import create_app
from app.extensions import celery

# 创建应用实例
app = create_app()

# 确保Celery在Flask应用上下文中运行
app.app_context().push()

if __name__ == "__main__":
    # 启动Celery worker
    # 使用命令: python celery_worker.py
    # 或者: celery -A celery_worker.celery worker --loglevel=info
    celery.start()
