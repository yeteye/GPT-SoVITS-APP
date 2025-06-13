from flask import Blueprint, request, jsonify, current_app
from app.extensions import db
from app.models.model import VoiceModel, Tag
from app.auth.decorators import auth_required, rate_limit, log_action, verify_ownership
from app.utils.validators import validate_model_name, validate_pagination
from app.utils.helpers import create_response, paginate_query, log_user_action
from app.utils.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    AuthorizationError,
)

model_bp = Blueprint("models", __name__)


@model_bp.route("/my-models", methods=["GET"])
@auth_required
@rate_limit(requests_per_minute=30)
def get_my_models():
    """获取用户的模型列表"""
    try:
        user = request.current_user

        # 分页参数
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        status = request.args.get("status")

        page, per_page = validate_pagination(page, per_page)

        # 构建查询
        query = VoiceModel.query.filter_by(owner_id=user.id)

        if status:
            query = query.filter_by(status=status)

        # 按创建时间倒序排列
        query = query.order_by(VoiceModel.created_at.desc())

        # 分页
        pagination = paginate_query(query, page, per_page)

        return jsonify(
            create_response(
                success=True,
                message="User models retrieved successfully",
                data={
                    "models": [model.to_dict() for model in pagination["items"]],
                    "pagination": {
                        "page": pagination["page"],
                        "per_page": pagination["per_page"],
                        "total": pagination["total"],
                        "pages": pagination["pages"],
                        "has_prev": pagination["has_prev"],
                        "has_next": pagination["has_next"],
                    },
                },
            )
        )

    except ValidationError as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Get my models error: {e}")
        return jsonify(create_response(False, "Failed to retrieve models")), 500


@model_bp.route("/<model_id>", methods=["GET"])
@auth_required
@rate_limit(requests_per_minute=60)
def get_model_detail(model_id):
    """获取模型详情"""
    try:
        user = request.current_user

        model = VoiceModel.query.get(model_id)

        if not model:
            raise ResourceNotFoundError("Voice model")

        # 检查访问权限
        if not model.is_public and model.owner_id != user.id and not user.is_admin():
            raise AuthorizationError("You do not have permission to view this model")

        # 管理员或所有者可以查看完整信息
        include_paths = user.is_admin() or model.owner_id == user.id

        return jsonify(
            create_response(
                success=True,
                message="Model details retrieved successfully",
                data={"model": model.to_dict(include_paths=include_paths)},
            )
        )

    except (ResourceNotFoundError, AuthorizationError) as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Get model detail error: {e}")
        return jsonify(create_response(False, "Failed to retrieve model details")), 500


@model_bp.route("/<model_id>", methods=["PUT"])
@auth_required
@verify_ownership(VoiceModel)
@rate_limit(requests_per_minute=10)
@log_action("update_voice_model", "voice_model")
def update_model(model_id):
    """更新模型信息"""
    try:
        user = request.current_user
        model = request.current_resource
        data = request.get_json()

        if not data:
            raise ValidationError("Request body is required")

        # 可更新的字段
        updatable_fields = ["name", "description", "voice_characteristics", "is_public"]

        # 管理员可以更新更多字段
        if user.is_admin():
            updatable_fields.extend(["status", "is_featured", "quality_score"])

        old_values = {}
        new_values = {}

        for field in updatable_fields:
            if field in data:
                old_values[field] = getattr(model, field)
                new_value = data[field]

                if field == "name":
                    validate_model_name(new_value)
                    # 检查名称是否重复
                    existing = VoiceModel.query.filter(
                        VoiceModel.name == new_value,
                        VoiceModel.owner_id == model.owner_id,
                        VoiceModel.id != model.id,
                    ).first()
                    if existing:
                        raise ValidationError("Model name already exists")

                setattr(model, field, new_value)
                new_values[field] = new_value

        # 处理标签
        if "tags" in data:
            old_values["tags"] = [tag.name for tag in model.tags]
            model.tags.clear()

            for tag_name in data["tags"]:
                tag = Tag.get_or_create(tag_name)
                model.tags.append(tag)

            new_values["tags"] = data["tags"]

        # 处理支持的情感
        if "supported_emotions" in data:
            old_values["supported_emotions"] = model.get_supported_emotions()
            model.set_supported_emotions(data["supported_emotions"])
            new_values["supported_emotions"] = data["supported_emotions"]

        # 处理支持的语言
        if "supported_languages" in data:
            old_values["supported_languages"] = model.get_supported_languages()
            model.set_supported_languages(data["supported_languages"])
            new_values["supported_languages"] = data["supported_languages"]

        db.session.commit()

        # 记录审计日志
        from app.models.audit import AuditLog

        AuditLog.log_action(
            action="update_voice_model",
            resource_type="voice_model",
            user_id=user.id,
            resource_id=model.id,
            old_values=old_values,
            new_values=new_values,
            description=f"Updated voice model: {model.name}",
        )

        return jsonify(
            create_response(
                success=True,
                message="Model updated successfully",
                data={
                    "model": model.to_dict(
                        include_paths=user.is_admin() or model.owner_id == user.id
                    )
                },
            )
        )

    except (ValidationError, ResourceNotFoundError) as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Update model error: {e}")
        return jsonify(create_response(False, "Failed to update model")), 500


@model_bp.route("/<model_id>", methods=["DELETE"])
@auth_required
@verify_ownership(VoiceModel)
@rate_limit(requests_per_minute=5)
@log_action("delete_voice_model", "voice_model")
def delete_model(model_id):
    """删除模型"""
    try:
        user = request.current_user
        model = request.current_resource

        # 检查模型是否正在使用中
        from app.models.task import TTSTask

        active_tasks = TTSTask.query.filter_by(
            model_id=model.id, status="processing"
        ).count()

        if active_tasks > 0:
            raise ValidationError(
                "Cannot delete model while it is being used in active tasks"
            )

        # 软删除：设置状态为inactive
        model.status = "inactive"
        db.session.commit()

        # 可选：删除物理文件
        import os

        files_to_delete = [model.model_path, model.config_path, model.index_path]
        for file_path in files_to_delete:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    current_app.logger.warning(
                        f"Failed to delete file {file_path}: {e}"
                    )

        return jsonify(
            create_response(success=True, message="Model deleted successfully")
        )

    except (ValidationError, ResourceNotFoundError) as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Delete model error: {e}")
        return jsonify(create_response(False, "Failed to delete model")), 500


@model_bp.route("/<model_id>/toggle-public", methods=["POST"])
@auth_required
@verify_ownership(VoiceModel)
@rate_limit(requests_per_minute=10)
@log_action("toggle_model_visibility", "voice_model")
def toggle_model_public(model_id):
    """切换模型公开状态"""
    try:
        model = request.current_resource

        # 只有活跃状态的模型才能设为公开
        if not model.is_public and model.status != "active":
            raise ValidationError("Only active models can be made public")

        # 切换公开状态
        old_status = model.is_public
        model.is_public = not model.is_public

        # 如果设为公开，需要重置审核状态
        if model.is_public and model.review_status != "approved":
            model.review_status = "pending"

        db.session.commit()

        action = "made public" if model.is_public else "made private"

        return jsonify(
            create_response(
                success=True,
                message=f"Model {action} successfully",
                data={
                    "is_public": model.is_public,
                    "review_status": model.review_status,
                },
            )
        )

    except (ValidationError, ResourceNotFoundError) as e:
        return jsonify(create_response(False, str(e))), e.status_code
    except Exception as e:
        current_app.logger.error(f"Toggle model public error: {e}")
        return jsonify(create_response(False, "Failed to toggle model visibility")), 500


@model_bp.route("/tags", methods=["GET"])
@rate_limit(requests_per_minute=100)
def get_tags():
    """获取可用标签列表"""
    try:
        tags = Tag.query.order_by(Tag.usage_count.desc(), Tag.name).all()

        return jsonify(
            create_response(
                success=True,
                message="Tags retrieved successfully",
                data={"tags": [tag.to_dict() for tag in tags]},
            )
        )

    except Exception as e:
        current_app.logger.error(f"Get tags error: {e}")
        return jsonify(create_response(False, "Failed to retrieve tags")), 500


@model_bp.route("/stats", methods=["GET"])
@auth_required
@rate_limit(requests_per_minute=30)
def get_model_stats():
    """获取用户模型统计信息"""
    try:
        user = request.current_user

        # 统计用户模型
        total_models = VoiceModel.query.filter_by(owner_id=user.id).count()
        active_models = VoiceModel.query.filter_by(
            owner_id=user.id, status="active"
        ).count()
        public_models = VoiceModel.query.filter_by(
            owner_id=user.id, is_public=True, status="active"
        ).count()

        # 统计使用次数
        total_usage = (
            db.session.query(db.func.sum(VoiceModel.usage_count))
            .filter_by(owner_id=user.id)
            .scalar()
            or 0
        )

        # 统计下载次数
        total_downloads = (
            db.session.query(db.func.sum(VoiceModel.download_count))
            .filter_by(owner_id=user.id)
            .scalar()
            or 0
        )

        # 平均质量分数
        avg_quality = (
            db.session.query(db.func.avg(VoiceModel.quality_score))
            .filter_by(owner_id=user.id, status="active")
            .scalar()
            or 0
        )

        return jsonify(
            create_response(
                success=True,
                message="Model statistics retrieved successfully",
                data={
                    "total_models": total_models,
                    "active_models": active_models,
                    "public_models": public_models,
                    "total_usage": int(total_usage),
                    "total_downloads": int(total_downloads),
                    "average_quality_score": (
                        round(float(avg_quality), 2) if avg_quality else 0
                    ),
                },
            )
        )

    except Exception as e:
        current_app.logger.error(f"Get model stats error: {e}")
        return (
            jsonify(create_response(False, "Failed to retrieve model statistics")),
            500,
        )
