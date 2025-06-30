# ./gpt-sovits-backend/app/services/task_service.py
import os
from datetime import datetime, timedelta
from flask import current_app
from app.extensions import db, celery
from app.models.task import VoiceCloneTask, TTSTask
from app.models.user import User
from app.models.model import VoiceModel
from app.utils.exceptions import TaskProcessingError, ResourceNotFoundError
from app.utils.helpers import log_user_action


class TaskService:
    """任务管理服务 - 优化配置使用版本"""

    @staticmethod
    def get_user_task_limits(user_id):
        """获取用户任务限制 - 使用环境变量配置"""
        try:
            user = User.query.get(user_id)
            if not user:
                raise ResourceNotFoundError("User not found")

            # 根据用户角色设置不同的限制 - 从配置中获取
            if user.role >= 2:  # 管理员
                limits = {
                    "max_concurrent_vc": current_app.config.get(
                        "MAX_CONCURRENT_VC_TASKS", 5
                    )
                    * 2,
                    "max_concurrent_tts": current_app.config.get(
                        "MAX_CONCURRENT_TTS_TASKS", 10
                    )
                    * 2,
                    "max_daily_vc": current_app.config.get("MAX_DAILY_VC_TASKS", 20)
                    * 2,
                    "max_daily_tts": current_app.config.get("MAX_DAILY_TTS_TASKS", 100)
                    * 2,
                }
            elif user.role >= 1:  # 审核员
                limits = {
                    "max_concurrent_vc": current_app.config.get(
                        "MAX_CONCURRENT_VC_TASKS", 3
                    ),
                    "max_concurrent_tts": current_app.config.get(
                        "MAX_CONCURRENT_TTS_TASKS", 8
                    ),
                    "max_daily_vc": current_app.config.get("MAX_DAILY_VC_TASKS", 15),
                    "max_daily_tts": current_app.config.get("MAX_DAILY_TTS_TASKS", 80),
                }
            else:  # 普通用户
                limits = {
                    "max_concurrent_vc": current_app.config.get(
                        "MAX_CONCURRENT_VC_TASKS", 2
                    ),
                    "max_concurrent_tts": current_app.config.get(
                        "MAX_CONCURRENT_TTS_TASKS", 5
                    ),
                    "max_daily_vc": current_app.config.get("MAX_DAILY_VC_TASKS", 10),
                    "max_daily_tts": current_app.config.get("MAX_DAILY_TTS_TASKS", 50),
                }

            # 获取当前使用情况
            current_vc = VoiceCloneTask.query.filter(
                VoiceCloneTask.user_id == user_id,
                VoiceCloneTask.status.in_(["pending", "processing"]),
            ).count()

            current_tts = TTSTask.query.filter(
                TTSTask.user_id == user_id,
                TTSTask.status.in_(["pending", "processing"]),
            ).count()

            # 今日任务数
            today = datetime.now().date()
            today_vc = VoiceCloneTask.query.filter(
                VoiceCloneTask.user_id == user_id, VoiceCloneTask.created_at >= today
            ).count()

            today_tts = TTSTask.query.filter(
                TTSTask.user_id == user_id, TTSTask.created_at >= today
            ).count()

            return {
                "limits": limits,
                "current_usage": {
                    "concurrent_vc": current_vc,
                    "concurrent_tts": current_tts,
                    "daily_vc": today_vc,
                    "daily_tts": today_tts,
                },
                "can_create_vc": (
                    current_vc < limits["max_concurrent_vc"]
                    and today_vc < limits["max_daily_vc"]
                ),
                "can_create_tts": (
                    current_tts < limits["max_concurrent_tts"]
                    and today_tts < limits["max_daily_tts"]
                ),
            }

        except Exception as e:
            current_app.logger.error(f"Get user task limits error: {e}")
            raise TaskProcessingError(f"Failed to get user task limits: {str(e)}")

    @staticmethod
    def cleanup_old_tasks(days_threshold=None, keep_completed=True):
        """清理旧任务 - 使用配置中的阈值"""
        try:
            # 使用配置的清理阈值
            if days_threshold is None:
                days_threshold = current_app.config.get("TASK_CLEANUP_DAYS", 30)

            cutoff_date = datetime.now() - timedelta(days=days_threshold)

            # 清理语音克隆任务
            vc_query = VoiceCloneTask.query.filter(
                VoiceCloneTask.created_at < cutoff_date
            )

            if keep_completed:
                vc_query = vc_query.filter(
                    VoiceCloneTask.status.in_(["failed", "cancelled"])
                )

            vc_tasks_to_delete = vc_query.all()
            vc_deleted_count = 0

            for task in vc_tasks_to_delete:
                try:
                    # 清理相关文件
                    TaskService._cleanup_task_files(task)
                    db.session.delete(task)
                    vc_deleted_count += 1
                except Exception as e:
                    current_app.logger.warning(
                        f"Failed to delete VC task {task.id}: {e}"
                    )

            # 清理TTS任务
            tts_query = TTSTask.query.filter(TTSTask.created_at < cutoff_date)

            if keep_completed:
                tts_query = tts_query.filter(
                    TTSTask.status.in_(["failed", "cancelled"])
                )

            tts_tasks_to_delete = tts_query.all()
            tts_deleted_count = 0

            for task in tts_tasks_to_delete:
                try:
                    # 清理音频文件
                    if task.audio_path and os.path.exists(task.audio_path):
                        os.remove(task.audio_path)
                    db.session.delete(task)
                    tts_deleted_count += 1
                except Exception as e:
                    current_app.logger.warning(
                        f"Failed to delete TTS task {task.id}: {e}"
                    )

            db.session.commit()

            return {
                "voice_clone_deleted": vc_deleted_count,
                "tts_deleted": tts_deleted_count,
                "total_deleted": vc_deleted_count + tts_deleted_count,
                "days_threshold": days_threshold,
            }

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Cleanup old tasks error: {e}")
            raise TaskProcessingError(f"Failed to cleanup old tasks: {str(e)}")

    @staticmethod
    def _cleanup_task_files(task):
        """清理任务相关文件 - 使用配置的路径"""
        try:
            if hasattr(task, "get_audio_samples"):
                # 语音克隆任务的样本文件通常不删除，因为可能被其他任务使用
                pass

            # 清理工作目录 - 使用配置的上传路径
            work_dir = os.path.join(
                current_app.config["UPLOAD_FOLDER"], "temp", f"voice_clone_{task.id}"
            )

            if os.path.exists(work_dir):
                import shutil

                shutil.rmtree(work_dir, ignore_errors=True)

        except Exception as e:
            current_app.logger.warning(
                f"Failed to cleanup files for task {task.id}: {e}"
            )

    @staticmethod
    def get_task_statistics(user_id=None, time_period_days=None):
        """获取任务统计信息 - 使用配置的默认时间段"""
        try:
            # 使用配置的默认统计时间段
            if time_period_days is None:
                time_period_days = current_app.config.get("TASK_STATS_PERIOD_DAYS", 30)

            # 设置时间范围
            if time_period_days:
                start_date = datetime.now() - timedelta(days=time_period_days)
            else:
                start_date = None

            # 构建查询条件
            vc_query = VoiceCloneTask.query
            tts_query = TTSTask.query

            if user_id:
                vc_query = vc_query.filter_by(user_id=user_id)
                tts_query = tts_query.filter_by(user_id=user_id)

            if start_date:
                vc_query = vc_query.filter(VoiceCloneTask.created_at >= start_date)
                tts_query = tts_query.filter(TTSTask.created_at >= start_date)

            # 统计语音克隆任务
            vc_total = vc_query.count()
            vc_completed = vc_query.filter_by(status="completed").count()
            vc_failed = vc_query.filter_by(status="failed").count()
            vc_processing = vc_query.filter_by(status="processing").count()
            vc_pending = vc_query.filter_by(status="pending").count()

            # 统计TTS任务
            tts_total = tts_query.count()
            tts_completed = tts_query.filter_by(status="completed").count()
            tts_failed = tts_query.filter_by(status="failed").count()
            tts_processing = tts_query.filter_by(status="processing").count()
            tts_pending = tts_query.filter_by(status="pending").count()

            # 计算成功率
            vc_success_rate = (vc_completed / vc_total * 100) if vc_total > 0 else 0
            tts_success_rate = (tts_completed / tts_total * 100) if tts_total > 0 else 0

            # 计算平均处理时间
            vc_avg_time = TaskService._calculate_average_processing_time(
                vc_query.filter_by(status="completed").all()
            )
            tts_avg_time = TaskService._calculate_average_processing_time(
                tts_query.filter_by(status="completed").all()
            )

            return {
                "voice_clone": {
                    "total": vc_total,
                    "completed": vc_completed,
                    "failed": vc_failed,
                    "processing": vc_processing,
                    "pending": vc_pending,
                    "success_rate": round(vc_success_rate, 2),
                    "avg_processing_time_seconds": vc_avg_time,
                },
                "tts": {
                    "total": tts_total,
                    "completed": tts_completed,
                    "failed": tts_failed,
                    "processing": tts_processing,
                    "pending": tts_pending,
                    "success_rate": round(tts_success_rate, 2),
                    "avg_processing_time_seconds": tts_avg_time,
                },
                "period_days": time_period_days,
                "total_tasks": vc_total + tts_total,
            }

        except Exception as e:
            current_app.logger.error(f"Get task statistics error: {e}")
            raise TaskProcessingError(f"Failed to get task statistics: {str(e)}")

    @staticmethod
    def _calculate_average_processing_time(tasks):
        """计算平均处理时间"""
        try:
            if not tasks:
                return 0

            total_time = 0
            valid_tasks = 0

            for task in tasks:
                if hasattr(task, "started_at") and hasattr(task, "completed_at"):
                    if task.started_at and task.completed_at:
                        processing_time = (
                            task.completed_at - task.started_at
                        ).total_seconds()
                        total_time += processing_time
                        valid_tasks += 1

            return round(total_time / valid_tasks, 2) if valid_tasks > 0 else 0

        except Exception:
            return 0

    @staticmethod
    def get_active_tasks_count(user_id=None):
        """获取活跃任务数量"""
        try:
            active_statuses = ["pending", "processing"]

            vc_query = VoiceCloneTask.query.filter(
                VoiceCloneTask.status.in_(active_statuses)
            )
            tts_query = TTSTask.query.filter(TTSTask.status.in_(active_statuses))

            if user_id:
                vc_query = vc_query.filter_by(user_id=user_id)
                tts_query = tts_query.filter_by(user_id=user_id)

            vc_count = vc_query.count()
            tts_count = tts_query.count()

            return {
                "voice_clone_active": vc_count,
                "tts_active": tts_count,
                "total_active": vc_count + tts_count,
                "max_concurrent_allowed": current_app.config.get(
                    "MAX_CONCURRENT_TASKS", 5
                ),
            }

        except Exception as e:
            current_app.logger.error(f"Get active tasks count error: {e}")
            return {
                "voice_clone_active": 0,
                "tts_active": 0,
                "total_active": 0,
                "max_concurrent_allowed": 0,
            }

    @staticmethod
    def cancel_user_tasks(user_id, task_type=None):
        """取消用户的所有进行中任务"""
        try:
            cancelled_count = 0

            # 取消语音克隆任务
            if not task_type or task_type == "voice_clone":
                vc_tasks = VoiceCloneTask.query.filter(
                    VoiceCloneTask.user_id == user_id,
                    VoiceCloneTask.status.in_(["pending", "processing"]),
                ).all()

                for task in vc_tasks:
                    try:
                        if task.celery_task_id and celery:
                            celery.control.revoke(task.celery_task_id, terminate=True)
                        task.update_status("failed", error_message="Cancelled by user")
                        cancelled_count += 1
                    except Exception as e:
                        current_app.logger.warning(
                            f"Failed to cancel VC task {task.id}: {e}"
                        )

            # 取消TTS任务
            if not task_type or task_type == "tts":
                tts_tasks = TTSTask.query.filter(
                    TTSTask.user_id == user_id,
                    TTSTask.status.in_(["pending", "processing"]),
                ).all()

                for task in tts_tasks:
                    try:
                        if task.celery_task_id and celery:
                            celery.control.revoke(task.celery_task_id, terminate=True)
                        task.update_status("failed", error_message="Cancelled by user")
                        cancelled_count += 1
                    except Exception as e:
                        current_app.logger.warning(
                            f"Failed to cancel TTS task {task.id}: {e}"
                        )

            db.session.commit()

            # 记录日志
            if cancelled_count > 0:
                log_user_action(
                    user_id=user_id,
                    action="cancel_user_tasks",
                    resource_type="task",
                    details=f"Cancelled {cancelled_count} tasks",
                )

            return cancelled_count

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Cancel user tasks error: {e}")
            raise TaskProcessingError(f"Failed to cancel user tasks: {str(e)}")

    @staticmethod
    def get_task_queue_status():
        """获取任务队列状态"""
        try:
            # 获取Celery队列信息
            if not celery:
                return {
                    "database_status": TaskService._get_db_task_status(),
                    "celery_status": {"error": "Celery not available"},
                }

            inspect = celery.control.inspect()

            # 获取活跃任务
            active_tasks = inspect.active() if inspect else None
            scheduled_tasks = inspect.scheduled() if inspect else None
            reserved_tasks = inspect.reserved() if inspect else None

            return {
                "database_status": TaskService._get_db_task_status(),
                "celery_status": {
                    "active_tasks": active_tasks,
                    "scheduled_tasks": scheduled_tasks,
                    "reserved_tasks": reserved_tasks,
                },
                "config": {
                    "max_concurrent_tasks": current_app.config.get(
                        "MAX_CONCURRENT_TASKS", 5
                    ),
                    "task_timeout": current_app.config.get("TASK_TIMEOUT", 600),
                },
            }

        except Exception as e:
            current_app.logger.error(f"Get task queue status error: {e}")
            return {
                "database_status": TaskService._get_db_task_status(),
                "celery_status": {
                    "error": str(e),
                },
                "config": {
                    "max_concurrent_tasks": current_app.config.get(
                        "MAX_CONCURRENT_TASKS", 5
                    ),
                    "task_timeout": current_app.config.get("TASK_TIMEOUT", 600),
                },
            }

    @staticmethod
    def _get_db_task_status():
        """获取数据库中的任务状态"""
        try:
            vc_pending = VoiceCloneTask.query.filter_by(status="pending").count()
            vc_processing = VoiceCloneTask.query.filter_by(status="processing").count()
            tts_pending = TTSTask.query.filter_by(status="pending").count()
            tts_processing = TTSTask.query.filter_by(status="processing").count()

            return {
                "voice_clone_pending": vc_pending,
                "voice_clone_processing": vc_processing,
                "tts_pending": tts_pending,
                "tts_processing": tts_processing,
            }
        except Exception:
            return {
                "voice_clone_pending": 0,
                "voice_clone_processing": 0,
                "tts_pending": 0,
                "tts_processing": 0,
            }
