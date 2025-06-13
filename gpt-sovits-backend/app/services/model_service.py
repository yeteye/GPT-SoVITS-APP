import os
import shutil
from flask import current_app
from app.extensions import db
from app.models.model import VoiceModel, Tag
from app.utils.exceptions import ValidationError, ResourceNotFoundError
from app.utils.helpers import log_user_action


def create_official_model(model_data, file_paths, creator_id):
    """创建官方模型"""
    try:
        # 验证必需字段
        required_fields = ["name", "description"]
        for field in required_fields:
            if not model_data.get(field):
                raise ValidationError(f"{field} is required")

        # 检查模型名称是否已存在
        existing_model = VoiceModel.query.filter_by(name=model_data["name"]).first()
        if existing_model:
            raise ValidationError("Model name already exists")

        # 创建模型目录
        model_dir = os.path.join(
            current_app.config["UPLOAD_FOLDER"],
            "models",
            "official",
            model_data["name"],
        )
        os.makedirs(model_dir, exist_ok=True)

        # 复制模型文件
        stored_paths = {}
        for file_type, src_path in file_paths.items():
            if src_path and os.path.exists(src_path):
                filename = os.path.basename(src_path)
                dst_path = os.path.join(model_dir, filename)
                shutil.copy2(src_path, dst_path)
                stored_paths[file_type] = dst_path

        # 创建模型记录
        model = VoiceModel(
            name=model_data["name"],
            description=model_data["description"],
            model_type="official",
            model_path=stored_paths.get("model_path"),
            config_path=stored_paths.get("config_path"),
            index_path=stored_paths.get("index_path"),
            voice_characteristics=model_data.get("voice_characteristics"),
            quality_score=model_data.get("quality_score", 9.0),
            status="active",
            is_public=True,
            is_featured=model_data.get("is_featured", True),
            review_status="approved",
            reviewed_by=creator_id,
            reviewed_at=db.func.now(),
        )

        # 设置支持的情感和语言
        model.set_supported_emotions(
            model_data.get("supported_emotions", ["neutral", "happy", "sad", "calm"])
        )
        model.set_supported_languages(model_data.get("supported_languages", ["zh-CN"]))

        # 添加标签
        tag_names = model_data.get("tags", [])
        for tag_name in tag_names:
            tag = Tag.get_or_create(tag_name.strip())
            model.tags.append(tag)

        db.session.add(model)
        db.session.commit()

        # 记录日志
        log_user_action(
            user_id=creator_id,
            action="create_official_model",
            resource_type="voice_model",
            resource_id=model.id,
            details=f"Created official model: {model.name}",
        )

        return model

    except Exception as e:
        # 清理已创建的文件
        if "model_dir" in locals() and os.path.exists(model_dir):
            shutil.rmtree(model_dir, ignore_errors=True)
        raise e


def update_model_quality_score(model_id, quality_score, reviewer_id):
    """更新模型质量评分"""
    try:
        model = VoiceModel.query.get(model_id)
        if not model:
            raise ResourceNotFoundError("Voice model")

        if not (0 <= quality_score <= 10):
            raise ValidationError("Quality score must be between 0 and 10")

        old_score = model.quality_score
        model.quality_score = quality_score
        db.session.commit()

        # 记录日志
        log_user_action(
            user_id=reviewer_id,
            action="update_model_quality",
            resource_type="voice_model",
            resource_id=model.id,
            details=f"Updated quality score from {old_score} to {quality_score}",
        )

        return model

    except Exception as e:
        raise e


def toggle_model_featured(model_id, is_featured, admin_id):
    """切换模型精选状态"""
    try:
        model = VoiceModel.query.get(model_id)
        if not model:
            raise ResourceNotFoundError("Voice model")

        if not model.is_public:
            raise ValidationError("Only public models can be featured")

        if model.status != "active":
            raise ValidationError("Only active models can be featured")

        old_featured = model.is_featured
        model.is_featured = is_featured
        db.session.commit()

        action = "featured" if is_featured else "unfeatured"

        # 记录日志
        log_user_action(
            user_id=admin_id,
            action="toggle_model_featured",
            resource_type="voice_model",
            resource_id=model.id,
            details=f"Model {action}",
        )

        return model

    except Exception as e:
        raise e


def get_model_usage_statistics(model_id):
    """获取模型使用统计"""
    try:
        model = VoiceModel.query.get(model_id)
        if not model:
            raise ResourceNotFoundError("Voice model")

        from app.models.task import TTSTask
        from datetime import datetime, timedelta

        # 总使用次数
        total_usage = model.usage_count
        total_downloads = model.download_count

        # 最近30天使用次数
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_usage = TTSTask.query.filter(
            TTSTask.model_id == model.id, TTSTask.created_at >= thirty_days_ago
        ).count()

        # 成功率
        total_tasks = TTSTask.query.filter_by(model_id=model.id).count()
        successful_tasks = TTSTask.query.filter_by(
            model_id=model.id, status="completed"
        ).count()

        success_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0

        return {
            "model_id": model.id,
            "model_name": model.name,
            "total_usage": total_usage,
            "total_downloads": total_downloads,
            "recent_usage_30_days": recent_usage,
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "success_rate": round(success_rate, 2),
            "quality_score": model.quality_score,
            "is_featured": model.is_featured,
        }

    except Exception as e:
        raise e


def cleanup_inactive_models(days_threshold=90):
    """清理长期未使用的非活跃模型"""
    try:
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)

        # 查找需要清理的模型
        inactive_models = VoiceModel.query.filter(
            VoiceModel.status == "inactive",
            VoiceModel.updated_at < cutoff_date,
            VoiceModel.model_type == "user_trained",  # 只清理用户训练的模型
        ).all()

        cleaned_count = 0

        for model in inactive_models:
            try:
                # 删除物理文件
                files_to_delete = [
                    model.model_path,
                    model.config_path,
                    model.index_path,
                ]
                for file_path in files_to_delete:
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)

                # 删除模型目录
                if model.model_path:
                    model_dir = os.path.dirname(model.model_path)
                    if os.path.exists(model_dir) and not os.listdir(model_dir):
                        os.rmdir(model_dir)

                # 删除数据库记录
                db.session.delete(model)
                cleaned_count += 1

            except Exception as e:
                current_app.logger.warning(f"Failed to cleanup model {model.id}: {e}")
                continue

        db.session.commit()

        return {"cleaned_models": cleaned_count, "cutoff_date": cutoff_date.isoformat()}

    except Exception as e:
        current_app.logger.error(f"Model cleanup failed: {e}")
        raise e


def get_popular_models(limit=10, time_period_days=30):
    """获取热门模型"""
    try:
        from datetime import datetime, timedelta

        # 查询公开且活跃的模型
        query = VoiceModel.query.filter(
            VoiceModel.is_public == True, VoiceModel.status == "active"
        )

        # 按使用次数和质量评分排序
        models = (
            query.order_by(
                VoiceModel.usage_count.desc(), VoiceModel.quality_score.desc()
            )
            .limit(limit)
            .all()
        )

        return [model.to_dict() for model in models]

    except Exception as e:
        raise e


def search_models(query_text, filters=None, page=1, per_page=20):
    """搜索模型"""
    try:
        from sqlalchemy import or_

        # 构建基础查询
        query = VoiceModel.query.filter(
            VoiceModel.is_public == True, VoiceModel.status == "active"
        )

        # 文本搜索
        if query_text:
            search_filter = or_(
                VoiceModel.name.contains(query_text),
                VoiceModel.description.contains(query_text),
                VoiceModel.voice_characteristics.contains(query_text),
            )
            query = query.filter(search_filter)

        # 应用过滤器
        if filters:
            if filters.get("model_type"):
                query = query.filter_by(model_type=filters["model_type"])

            if filters.get("min_quality"):
                query = query.filter(VoiceModel.quality_score >= filters["min_quality"])

            if filters.get("tags"):
                for tag_name in filters["tags"]:
                    query = query.join(VoiceModel.tags).filter(Tag.name == tag_name)

            if filters.get("emotions"):
                # 这里需要JSON查询，简化处理
                pass

        # 排序
        sort_by = filters.get("sort_by", "usage") if filters else "usage"
        if sort_by == "quality":
            query = query.order_by(VoiceModel.quality_score.desc())
        elif sort_by == "newest":
            query = query.order_by(VoiceModel.created_at.desc())
        else:  # usage
            query = query.order_by(VoiceModel.usage_count.desc())

        # 分页
        from app.utils.helpers import paginate_query

        pagination = paginate_query(query, page, per_page)

        return {
            "models": [model.to_dict() for model in pagination["items"]],
            "pagination": {
                "page": pagination["page"],
                "per_page": pagination["per_page"],
                "total": pagination["total"],
                "pages": pagination["pages"],
                "has_prev": pagination["has_prev"],
                "has_next": pagination["has_next"],
            },
        }

    except Exception as e:
        raise e
