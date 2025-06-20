# ./gpt-sovits-backend/app/api/health.py
from flask import Blueprint, jsonify, current_app
from app.extensions import db, redis_client
from app.utils.helpers import create_response

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """系统健康检查 - 修复版本"""
    status = {
        "status": "healthy",
        "services": {"database": "unknown", "redis": "unknown", "celery": "unknown"},
    }

    # 检查数据库
    try:
        # 修复：使用更简单的数据库检查
        with db.engine.connect() as connection:
            result = connection.execute(db.text("SELECT 1"))
            result.fetchone()
        status["services"]["database"] = "healthy"
        current_app.logger.debug("Database health check: healthy")
    except Exception as e:
        status["services"]["database"] = "unhealthy"
        status["status"] = "unhealthy"
        current_app.logger.warning(f"Database health check failed: {e}")

    # 检查Redis
    try:
        if redis_client:
            redis_client.ping()
            status["services"]["redis"] = "healthy"
            current_app.logger.debug("Redis health check: healthy")
        else:
            status["services"]["redis"] = "unavailable"
            current_app.logger.debug("Redis not configured")
    except Exception as e:
        status["services"]["redis"] = "unhealthy"
        status["status"] = "unhealthy"
        current_app.logger.warning(f"Redis health check failed: {e}")

    # 检查Celery
    try:
        from app.extensions import celery

        if celery:
            # 修复：更准确的Celery检查
            try:
                # 检查是否有活跃的worker
                inspect = celery.control.inspect()
                active_workers = inspect.active()

                if active_workers and any(active_workers.values()):
                    status["services"]["celery"] = "healthy"
                    worker_count = sum(
                        len(workers) for workers in active_workers.values()
                    )
                    current_app.logger.debug(
                        f"Celery health check: {worker_count} active tasks"
                    )
                else:
                    # 检查是否有注册的worker
                    stats = inspect.stats()
                    if stats:
                        status["services"]["celery"] = "no_workers"
                        current_app.logger.debug(
                            "Celery workers registered but no active tasks"
                        )
                    else:
                        status["services"]["celery"] = "no_workers"
                        current_app.logger.debug("No Celery workers found")

            except Exception as celery_error:
                # 如果inspect失败，可能是worker没有启动
                status["services"]["celery"] = "no_workers"
                current_app.logger.debug(f"Celery inspect failed: {celery_error}")
        else:
            status["services"]["celery"] = "unavailable"
            current_app.logger.debug("Celery not configured")

    except Exception as e:
        status["services"]["celery"] = "unhealthy"
        current_app.logger.warning(f"Celery health check failed: {e}")

    # 修复：如果只是Celery没有worker，不应该标记整个系统为不健康
    # 因为在开发环境中，不启动worker是正常的
    if (
        status["services"]["database"] == "healthy"
        and status["services"]["redis"] in ["healthy", "unavailable"]
        and status["services"]["celery"] in ["healthy", "no_workers", "unavailable"]
    ):
        status["status"] = "healthy"

    # 添加额外的系统信息
    status["timestamp"] = (
        db.func.now().scalar() if status["services"]["database"] == "healthy" else None
    )
    status["environment"] = current_app.config.get("FLASK_ENV", "unknown")

    # 根据整体状态返回适当的HTTP状态码
    http_status = 200 if status["status"] == "healthy" else 503

    return jsonify(status), http_status
