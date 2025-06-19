#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ./gpt-sovits-backend/celery_worker.py
"""
Celery Worker 启动脚本
修复版本 - 解决 NoneType 错误
"""

import os
import sys

# 确保加载环境变量
from dotenv import load_dotenv

load_dotenv()

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 创建Flask应用实例
from app import create_app

app = create_app()


def create_celery_instance(app):
    """创建Celery实例 - 修复版本"""
    try:
        from celery import Celery

        # 检查必要的配置
        broker_url = app.config.get("CELERY_BROKER_URL")
        if not broker_url:
            print("❌ Error: CELERY_BROKER_URL not configured!")
            print("Please check your .env file contains:")
            print("CELERY_BROKER_URL=redis://localhost:6379/0")
            sys.exit(1)

        print(f"📡 Creating Celery instance with broker: {broker_url}")

        # 创建Celery实例
        celery_app = Celery(
            app.import_name,
            broker=broker_url,
            backend=app.config.get("CELERY_RESULT_BACKEND", broker_url),
            include=[
                "app.services.voice_clone_service",
                "app.services.tts_service",
            ],
        )

        # 更新配置
        celery_app.conf.update(
            task_serializer=app.config.get("CELERY_TASK_SERIALIZER", "json"),
            accept_content=app.config.get("CELERY_ACCEPT_CONTENT", ["json"]),
            result_serializer=app.config.get("CELERY_RESULT_SERIALIZER", "json"),
            timezone=app.config.get("CELERY_TIMEZONE", "UTC"),
            enable_utc=app.config.get("CELERY_ENABLE_UTC", True),
            # Worker配置
            worker_prefetch_multiplier=1,
            task_acks_late=True,
            worker_max_tasks_per_child=1000,
            # 任务路由
            task_routes={
                "app.services.voice_clone_service.*": {"queue": "voice_clone"},
                "app.services.tts_service.*": {"queue": "tts"},
            },
        )

        # 设置Flask应用上下文
        class ContextTask(celery_app.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery_app.Task = ContextTask

        return celery_app

    except ImportError as e:
        print(f"❌ Error: Celery not installed - {e}")
        print("Please install celery: pip install celery")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error creating Celery instance: {e}")
        sys.exit(1)


def test_redis_connection():
    """测试Redis连接"""
    try:
        import redis

        broker_url = app.config.get("CELERY_BROKER_URL", "redis://localhost:6379/0")

        # 解析Redis URL
        if broker_url.startswith("redis://"):
            # 简单解析：redis://localhost:6379/0
            parts = broker_url.replace("redis://", "").split("/")
            host_port = parts[0].split(":")
            host = host_port[0] if host_port[0] else "localhost"
            port = int(host_port[1]) if len(host_port) > 1 else 6379
            db = int(parts[1]) if len(parts) > 1 else 0
        else:
            host, port, db = "localhost", 6379, 0

        print(f"🔍 Testing Redis connection: {host}:{port}/{db}")

        r = redis.Redis(host=host, port=port, db=db)
        result = r.ping()

        if result:
            print(f"✅ Redis connection successful!")
            return True
        else:
            print(f"❌ Redis ping failed")
            return False

    except ImportError:
        print("❌ Redis package not installed: pip install redis")
        return False
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure Redis is running: redis-server")
        print("2. Or start with Docker: docker run -d -p 6379:6379 redis:alpine")
        print("3. Check if port 6379 is available: netstat -an | findstr 6379")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 GPT-SoVITS Celery Worker Starting...")
    print("=" * 60)

    # 显示环境信息
    print(f"📁 Working Directory: {os.getcwd()}")
    print(f"🐍 Python Version: {sys.version}")
    print(f"📦 Project Root: {project_root}")

    # 显示配置信息
    with app.app_context():
        print("\n📋 Configuration:")
        print(f"  Flask Config: {app.config.get('FLASK_CONFIG', 'unknown')}")
        print(
            f"  Database URL: {app.config.get('SQLALCHEMY_DATABASE_URI', 'not configured')[:50]}..."
        )
        print(f"  Broker URL: {app.config.get('CELERY_BROKER_URL', 'not configured')}")
        print(
            f"  Result Backend: {app.config.get('CELERY_RESULT_BACKEND', 'not configured')}"
        )

    # 测试Redis连接
    print("\n🔍 Testing Dependencies:")
    if not test_redis_connection():
        print("\n❌ Redis connection failed! Worker cannot start.")
        print("\n🛠️  To fix this:")
        print("1. Start Redis: redis-server")
        print("2. Or use Docker: docker run -d -p 6379:6379 redis:alpine")
        print("3. Or modify .env to use different Redis instance")
        sys.exit(1)

    # 创建Celery实例
    print("\n⚙️  Initializing Celery Worker...")
    celery_app = create_celery_instance(app)

    print("\n📋 Celery Configuration:")
    print(f"  Broker: {celery_app.conf.broker_url}")
    print(f"  Backend: {celery_app.conf.result_backend}")
    print(f"  Serializer: {celery_app.conf.task_serializer}")

    # 显示已注册的任务
    print("\n📝 Registered Tasks:")
    task_names = sorted(celery_app.tasks.keys())
    for task_name in task_names:
        if not task_name.startswith("celery."):
            print(f"  - {task_name}")

    if not any(task for task in task_names if "app.services" in task):
        print("  ⚠️  Warning: No app tasks found! Check task imports.")

    print("\n" + "=" * 60)
    print("🎯 Starting Celery Worker...")
    print("📝 Use Ctrl+C to stop the worker")
    print("=" * 60)

    try:
        # 启动Worker
        celery_app.worker_main(
            [
                "worker",
                "--loglevel=info",
                "--concurrency=4",
                "--queues=celery,voice_clone,tts",
            ]
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Worker stopped by user")
    except Exception as e:
        print(f"\n❌ Worker failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
