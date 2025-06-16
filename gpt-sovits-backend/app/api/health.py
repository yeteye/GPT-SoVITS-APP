from flask import Blueprint, jsonify
from app.extensions import db, redis_client
from app.utils.helpers import create_response

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """系统健康检查"""
    status = {
        "status": "healthy",
        "services": {"database": "unknown", "redis": "unknown", "celery": "unknown"},
    }

    # 检查数据库
    try:
        db.session.execute("SELECT 1")
        status["services"]["database"] = "healthy"
    except Exception:
        status["services"]["database"] = "unhealthy"
        status["status"] = "unhealthy"

    # 检查Redis
    try:
        if redis_client:
            redis_client.ping()
            status["services"]["redis"] = "healthy"
        else:
            status["services"]["redis"] = "unavailable"
    except Exception:
        status["services"]["redis"] = "unhealthy"
        status["status"] = "unhealthy"

    # 检查Celery
    try:
        from app.extensions import celery

        if celery:
            inspect = celery.control.inspect()
            active = inspect.active()
            if active:
                status["services"]["celery"] = "healthy"
            else:
                status["services"]["celery"] = "no_workers"
        else:
            status["services"]["celery"] = "unavailable"
    except Exception:
        status["services"]["celery"] = "unhealthy"

    return jsonify(status), 200 if status["status"] == "healthy" else 503
