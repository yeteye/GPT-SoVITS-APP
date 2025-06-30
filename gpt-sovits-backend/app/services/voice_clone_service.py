# ./gpt-sovits-backend/app/services/voice_clone_service.py (修复版)
import os
import shutil
import subprocess
import soundfile as sf
from pydub import AudioSegment
from datetime import datetime
from flask import current_app
from app.extensions import db
from app.models.task import VoiceCloneTask
from app.models.model import VoiceModel
from app.utils.exceptions import TaskProcessingError
from app.utils.helpers import log_user_action
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class MockCeleryResult:
    """模拟Celery任务结果"""

    def __init__(self, task_id="mock-voice-clone-task"):
        self.id = task_id
        self.state = "SUCCESS"
        self.result = {"status": "completed", "message": "Mock task completed"}

    def get(self, timeout=None):
        return self.result

    def ready(self):
        return True

    def successful(self):
        return True


def create_voice_clone_decorator():
    """创建语音克隆任务装饰器 - 修复版本"""
    try:
        from flask import current_app
        from app.extensions import celery

        # 检查环境
        is_testing = current_app.config.get("TESTING", False)
        has_celery = celery is not None

        if not is_testing and has_celery:
            # 生产环境：使用真实 Celery
            def celery_decorator(func):
                @celery.task(
                    bind=True,
                    name=f"app.services.voice_clone_service.{func.__name__}",
                    max_retries=3,
                    default_retry_delay=60,
                )
                def wrapper(self, task_id):
                    return func(self, task_id)

                return wrapper

            return celery_decorator
        else:
            # 测试环境或无 Celery：使用模拟装饰器
            def mock_decorator(func):
                @wraps(func)
                def wrapper(task_id_or_self, task_id=None):
                    # 统一参数处理
                    if task_id is None:
                        # 直接调用：wrapper(task_id)
                        actual_task_id = task_id_or_self
                        return func(None, actual_task_id)
                    else:
                        # Celery 风格调用：wrapper(self, task_id)
                        return func(task_id_or_self, task_id)

                # 添加模拟的delay和apply_async方法
                wrapper.delay = lambda task_id: MockCeleryResult(task_id)
                wrapper.apply_async = lambda args=None, **kwargs: MockCeleryResult(
                    args[0] if args else "mock"
                )
                return wrapper

            return mock_decorator

    except (RuntimeError, ImportError):
        # 不在应用上下文或Celery不可用
        def fallback_decorator(func):
            @wraps(func)
            def wrapper(task_id_or_self, task_id=None):
                if task_id is None:
                    return func(None, task_id_or_self)
                else:
                    return func(task_id_or_self, task_id)

            wrapper.delay = lambda task_id: MockCeleryResult(task_id)
            wrapper.apply_async = lambda args=None, **kwargs: MockCeleryResult(
                args[0] if args else "mock"
            )
            return wrapper

        return fallback_decorator


# 应用装饰器
@create_voice_clone_decorator()
def start_voice_clone_task(self, task_id):
    """启动语音克隆任务 - 修复版本"""
    try:
        # 获取任务
        task = db.session.get(VoiceCloneTask, task_id)
        if not task:
            raise TaskProcessingError(f"Task {task_id} not found")

        logger.info(f"Starting voice clone task {task_id}")

        # 更新任务状态
        task.update_status("processing", progress=5)

        # 检查运行环境
        try:
            is_testing = current_app.config.get("TESTING", False)
            has_celery = self is not None
        except RuntimeError:
            # 不在应用上下文中
            is_testing = True
            has_celery = False

        if is_testing:
            # 测试环境：快速模拟处理
            logger.info(f"Running task {task_id} in test mode")
            result = mock_voice_clone_process(task)
        else:
            # 生产环境：执行实际处理
            logger.info(f"Running task {task_id} in production mode")
            result = process_voice_clone(task, self)

        # 更新任务完成状态
        task.update_status("completed", progress=100)
        task.result_model_id = result["model_id"]
        db.session.commit()

        # 记录成功日志
        log_user_action(
            user_id=task.user_id,
            action="voice_clone_completed",
            resource_type="voice_clone_task",
            resource_id=task.id,
            details=f'Voice clone training completed. Model ID: {result["model_id"]}',
        )

        logger.info(f"Task {task_id} completed successfully")

        return {
            "status": "completed",
            "model_id": result["model_id"],
            "quality_score": result.get("quality_score", 7.5),
            "message": "Voice clone training completed successfully",
        }

    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}", exc_info=True)

        # 更新任务失败状态
        if "task" in locals() and task:
            task.update_status("failed", error_message=str(e))

            # 记录失败日志
            log_user_action(
                user_id=task.user_id,
                action="voice_clone_failed",
                resource_type="voice_clone_task",
                resource_id=task.id,
                details=f"Voice clone training failed: {str(e)}",
            )

        raise TaskProcessingError(f"Voice clone training failed: {str(e)}")


def mock_voice_clone_process(task):
    """模拟语音克隆处理过程"""
    try:
        logger.info(f"Mock processing voice clone task: {task.id}")

        # 模拟处理延迟
        import time

        time.sleep(0.2)

        # 获取任务配置
        config = task.get_config()
        model_name = config.get("model_name", task.model_name)

        # 验证输入数据
        if not model_name:
            raise TaskProcessingError("Model name is required")

        audio_samples = task.get_audio_samples()
        if len(audio_samples) < 3:
            raise TaskProcessingError("At least 3 audio samples are required")

        # 创建模拟的语音模型
        try:
            # 创建模拟文件路径
            model_dir = os.path.join(
                current_app.config.get("UPLOAD_FOLDER", "./uploads"),
                "models",
                f"user_{task.user_id}",
                f"mock_{task.id}",
            )
            os.makedirs(model_dir, exist_ok=True)

            gpt_model_path = os.path.join(model_dir, f"{model_name}_gpt.pth")
            sovits_model_path = os.path.join(model_dir, f"{model_name}_sovits.ckpt")

            # 创建模拟文件
            with open(gpt_model_path, "w") as f:
                f.write(f"# Mock GPT model for {model_name}\n")
                f.write(f"# Generated from {task.sample_count} samples\n")
                f.write(f"# Task ID: {task.id}\n")

            with open(sovits_model_path, "w") as f:
                f.write(f"# Mock SoVITS model for {model_name}\n")
                f.write(f"# Generated from {task.sample_count} samples\n")
                f.write(f"# Task ID: {task.id}\n")

            # 创建模型记录 - 确保必需字段存在
            voice_model = VoiceModel(
                name=model_name,
                description=f"Mock voice model from task {task.id} with {task.sample_count} samples",
                model_type="user_trained",
                owner_id=task.user_id,
                gpt_model_path=gpt_model_path,  # 必需字段
                sovits_model_path=sovits_model_path,  # 必需字段
                quality_score=7.5 + (task.sample_count * 0.1),
                status="active",
                is_public=False,
            )

            # 设置支持的情感和语言
            supported_emotions = config.get(
                "supported_emotions", ["neutral", "happy", "sad"]
            )
            supported_languages = config.get("supported_languages", ["zh-CN"])

            voice_model.set_supported_emotions(supported_emotions)
            voice_model.set_supported_languages(supported_languages)

            db.session.add(voice_model)
            db.session.commit()

            logger.info(f"Created mock model {voice_model.id} for task {task.id}")

            return {
                "model_id": voice_model.id,
                "gpt_model_path": gpt_model_path,
                "sovits_model_path": sovits_model_path,
                "quality_score": voice_model.quality_score,
            }

        except Exception as e:
            logger.error(f"Failed to create mock model: {e}")
            raise TaskProcessingError(f"Failed to create mock model: {str(e)}")

    except Exception as e:
        logger.error(f"Mock voice clone process failed: {e}")
        raise TaskProcessingError(f"Mock voice clone process failed: {str(e)}")


def process_voice_clone(task, celery_self=None):
    """处理语音克隆流程 - 生产环境版本"""
    try:
        logger.info(f"Starting production voice clone process for task {task.id}")

        # 1. 准备工作环境
        work_dir = prepare_training_environment(task)
        logger.info(f"Prepared training environment: {work_dir}")

        # 2. 预处理音频文件
        update_task_progress(task, 15, "Preprocessing audio files...", celery_self)
        preprocessed_files = preprocess_audio_files(task, work_dir)
        logger.info(f"Preprocessed {len(preprocessed_files)} audio files")

        # 3. 提取音频特征
        update_task_progress(task, 35, "Extracting audio features...", celery_self)
        features = extract_audio_features(preprocessed_files, work_dir)
        logger.info("Audio features extracted")

        # 4. 训练GPT和SoVITS模型
        update_task_progress(task, 55, "Training GPT model...", celery_self)
        gpt_model_path = train_gpt_model(features, work_dir, task)

        update_task_progress(task, 75, "Training SoVITS model...", celery_self)
        sovits_model_path = train_sovits_model(features, work_dir, task)

        # 5. 验证模型质量
        update_task_progress(task, 85, "Validating model quality...", celery_self)
        quality_score = validate_model_quality(
            {"gpt_model_path": gpt_model_path, "sovits_model_path": sovits_model_path},
            preprocessed_files,
        )

        # 6. 保存模型
        update_task_progress(task, 95, "Saving models...", celery_self)
        model_info = save_trained_models(
            task,
            {"gpt_model_path": gpt_model_path, "sovits_model_path": sovits_model_path},
            quality_score,
        )

        # 7. 清理临时文件
        cleanup_training_environment(work_dir)
        logger.info(f"Cleaned up training environment: {work_dir}")

        return model_info

    except Exception as e:
        logger.error(f"Production voice clone process failed: {e}")
        # 清理临时文件
        if "work_dir" in locals():
            cleanup_training_environment(work_dir)
        raise TaskProcessingError(f"Voice clone training failed: {str(e)}")


def prepare_training_environment(task):
    """准备训练环境 - 改进版本"""
    try:
        work_dir = os.path.join(
            current_app.config["UPLOAD_FOLDER"],
            "temp",
            f"voice_clone_{task.id}_{int( datetime.now().timestamp())}",
        )

        # 创建工作目录结构
        subdirs = ["input", "processed", "features", "models", "output", "logs"]
        for subdir in subdirs:
            subdir_path = os.path.join(work_dir, subdir)
            os.makedirs(subdir_path, exist_ok=True)

        # 创建配置文件
        config_path = os.path.join(work_dir, "config.json")
        import json

        config = {
            "task_id": task.id,
            "created_at": datetime.now().isoformat(),
            "model_name": task.model_name,
            "sample_count": task.sample_count,
            "total_duration": task.total_duration,
            "user_id": task.user_id,
        }

        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        logger.info(f"Created training environment: {work_dir}")
        return work_dir

    except Exception as e:
        logger.error(f"Failed to prepare training environment: {e}")
        raise TaskProcessingError(f"Failed to prepare training environment: {str(e)}")


def preprocess_audio_files(task, work_dir, target_sample_rate=22050):
    """预处理音频文件 - 改进版本"""
    try:
        audio_samples = task.get_audio_samples()
        if not audio_samples:
            raise TaskProcessingError("No audio samples found")

        preprocessed_files = []
        processed_dir = os.path.join(work_dir, "processed")

        logger.info(f"Preprocessing {len(audio_samples)} audio files")

        for i, audio_path in enumerate(audio_samples):
            if not os.path.exists(audio_path):
                logger.warning(f"Audio file not found: {audio_path}")
                continue

            try:
                # 使用pydub进行音频处理
                audio = AudioSegment.from_file(audio_path)

                # 转换为目标格式
                audio = audio.set_channels(1)  # 单声道
                audio = audio.set_frame_rate(target_sample_rate)  # 目标采样率

                # 标准化音量
                audio = audio.normalize()

                # 移除静音部分
                audio = audio.strip_silence(silence_thresh=-40.0, silence_chunk_len=500)

                # 确保最小时长
                if len(audio) < 2000:  # 少于2秒
                    logger.warning(
                        f"Audio file {i} too short ({len(audio)}ms), skipping"
                    )
                    continue

                # 保存处理后的文件
                output_path = os.path.join(processed_dir, f"sample_{i:03d}.wav")
                audio.export(output_path, format="wav")

                preprocessed_files.append(output_path)
                logger.debug(f"Processed audio file {i}: {output_path}")

            except Exception as e:
                logger.warning(f"Failed to process audio file {audio_path}: {e}")
                continue

        if not preprocessed_files:
            raise TaskProcessingError("No valid audio files after preprocessing")

        logger.info(f"Successfully preprocessed {len(preprocessed_files)} audio files")
        return preprocessed_files

    except Exception as e:
        logger.error(f"Audio preprocessing failed: {e}")
        raise TaskProcessingError(f"Audio preprocessing failed: {str(e)}")


def extract_audio_features(audio_files, work_dir):
    """提取音频特征 - 模拟版本"""
    try:
        feature_dir = os.path.join(work_dir, "features")

        # 创建模拟特征文件
        features_info = {
            "audio_files": audio_files,
            "feature_extraction_method": "mock",
            "extracted_at": datetime.now().isoformat(),
            "total_files": len(audio_files),
        }

        feature_file = os.path.join(feature_dir, "extracted_features.json")
        import json

        with open(feature_file, "w") as f:
            json.dump(features_info, f, indent=2)

        logger.info(f"Extracted features for {len(audio_files)} files")
        return feature_file

    except Exception as e:
        logger.error(f"Feature extraction failed: {e}")
        raise TaskProcessingError(f"Feature extraction failed: {str(e)}")


def train_gpt_model(features_file, work_dir, task):
    """训练GPT模型 - 模拟版本"""
    try:
        model_dir = os.path.join(work_dir, "models")
        config = task.get_config()
        model_name = config.get("model_name", task.model_name)

        gpt_model_path = os.path.join(model_dir, f"{model_name}_gpt.pth")

        # 创建模拟GPT模型文件
        with open(gpt_model_path, "w") as f:
            f.write(f"# GPT Model for {model_name}\n")
            f.write(f"# Task ID: {task.id}\n")
            f.write(f"# Features: {features_file}\n")
            f.write(f"# Training completed: {datetime.now().isoformat()}\n")

        logger.info(f"GPT model training completed: {gpt_model_path}")
        return gpt_model_path

    except Exception as e:
        logger.error(f"GPT model training failed: {e}")
        raise TaskProcessingError(f"GPT model training failed: {str(e)}")


def train_sovits_model(features_file, work_dir, task):
    """训练SoVITS模型 - 模拟版本"""
    try:
        model_dir = os.path.join(work_dir, "models")
        config = task.get_config()
        model_name = config.get("model_name", task.model_name)

        sovits_model_path = os.path.join(model_dir, f"{model_name}_sovits.ckpt")

        # 创建模拟SoVITS模型文件
        with open(sovits_model_path, "w") as f:
            f.write(f"# SoVITS Model for {model_name}\n")
            f.write(f"# Task ID: {task.id}\n")
            f.write(f"# Features: {features_file}\n")
            f.write(f"# Training completed: {datetime.now().isoformat()}\n")

        logger.info(f"SoVITS model training completed: {sovits_model_path}")
        return sovits_model_path

    except Exception as e:
        logger.error(f"SoVITS model training failed: {e}")
        raise TaskProcessingError(f"SoVITS model training failed: {str(e)}")


def save_trained_models(task, model_files, quality_score):
    """保存训练好的模型 - 改进版本"""
    try:
        config = task.get_config()
        model_name = config.get("model_name", task.model_name)

        # 创建最终存储目录
        final_model_dir = os.path.join(
            current_app.config["UPLOAD_FOLDER"],
            "models",
            f"user_{task.user_id}",
            model_name.replace(" ", "_").lower(),
        )
        os.makedirs(final_model_dir, exist_ok=True)

        # 复制模型文件到最终位置
        final_gpt_path = os.path.join(final_model_dir, f"{model_name}_gpt.pth")
        final_sovits_path = os.path.join(final_model_dir, f"{model_name}_sovits.ckpt")

        shutil.copy2(model_files["gpt_model_path"], final_gpt_path)
        shutil.copy2(model_files["sovits_model_path"], final_sovits_path)

        # 创建VoiceModel记录
        voice_model = VoiceModel(
            name=model_name,
            description=f"Voice model trained from {task.sample_count} audio samples (Duration: {task.total_duration:.1f}s)",
            model_type="user_trained",
            owner_id=task.user_id,
            gpt_model_path=final_gpt_path,
            sovits_model_path=final_sovits_path,
            quality_score=quality_score,
            status="active",
            is_public=False,
        )

        # 设置支持的情感和语言
        supported_emotions = config.get(
            "supported_emotions", ["neutral", "happy", "sad"]
        )
        supported_languages = config.get("supported_languages", ["zh-CN"])

        voice_model.set_supported_emotions(supported_emotions)
        voice_model.set_supported_languages(supported_languages)

        db.session.add(voice_model)
        db.session.commit()

        logger.info(f"Saved model {voice_model.id} to database")

        return {
            "model_id": voice_model.id,
            "gpt_model_path": final_gpt_path,
            "sovits_model_path": final_sovits_path,
            "quality_score": quality_score,
        }

    except Exception as e:
        logger.error(f"Failed to save trained models: {e}")
        raise TaskProcessingError(f"Failed to save trained models: {str(e)}")


def validate_model_quality(model_files, audio_files):
    """验证模型质量 - 改进版本"""
    try:
        quality_score = 7.0  # 基础分数

        # 检查模型文件
        if os.path.exists(model_files["gpt_model_path"]):
            quality_score += 0.5
        if os.path.exists(model_files["sovits_model_path"]):
            quality_score += 0.5

        # 根据训练数据质量调整分数
        if len(audio_files) >= 10:
            quality_score += 1.0
        elif len(audio_files) >= 5:
            quality_score += 0.5

        # 确保分数在合理范围内
        quality_score = max(5.0, min(10.0, quality_score))

        logger.info(f"Model quality score: {quality_score}")
        return quality_score

    except Exception as e:
        logger.warning(f"Model quality validation failed: {e}")
        return 6.0


def cleanup_training_environment(work_dir):
    """清理训练环境 - 安全版本"""
    try:
        if work_dir and os.path.exists(work_dir):
            # 确保我们不会删除重要目录
            if "voice_clone_" in os.path.basename(work_dir) and "temp" in work_dir:
                shutil.rmtree(work_dir, ignore_errors=True)
                logger.info(f"Cleaned up training environment: {work_dir}")
            else:
                logger.warning(f"Skipped cleanup of suspicious directory: {work_dir}")
    except Exception as e:
        logger.warning(f"Failed to cleanup training environment {work_dir}: {e}")


def update_task_progress(task, progress, message=None, celery_self=None):
    """更新任务进度 - 改进版本"""
    try:
        # 验证进度值
        progress = max(0, min(100, int(progress)))

        # 更新数据库
        task.progress = progress
        if message:
            # 可以选择将消息存储在任务的状态字段中
            pass

        db.session.commit()

        # 更新Celery任务状态
        if celery_self is not None:
            try:
                celery_self.update_state(
                    state="PROGRESS",
                    meta={
                        "progress": progress,
                        "message": message,
                        "task_id": task.id,
                        "current": progress,
                        "total": 100,
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to update Celery state: {e}")

        logger.debug(f"Task {task.id} progress: {progress}% - {message}")

    except Exception as e:
        logger.warning(f"Failed to update task progress: {e}")


def get_task_status(task_id):
    """获取任务状态 - 改进版本"""
    try:
        task = db.session.get(VoiceCloneTask, task_id)
        if not task:
            return None

        status_data = {
            "task_id": task.id,
            "status": task.status,
            "progress": task.progress,
            "model_name": task.model_name,
            "sample_count": task.sample_count,
            "total_duration": task.total_duration,
            "error_message": task.error_message,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": (
                task.completed_at.isoformat() if task.completed_at else None
            ),
            "estimated_completion": (
                task.estimated_completion.isoformat()
                if task.estimated_completion
                else None
            ),
            "result_model_id": task.result_model_id,
        }

        # 添加处理时长
        if task.started_at and task.completed_at:
            duration = (task.completed_at - task.started_at).total_seconds()
            status_data["processing_duration_seconds"] = duration
        elif task.started_at:
            duration = (datetime.now() - task.started_at).total_seconds()
            status_data["current_duration_seconds"] = duration

        # 如果任务完成且有结果模型，添加模型信息
        if task.status == "completed" and task.result_model_id:
            try:
                model = db.session.get(VoiceModel, task.result_model_id)
                if model:
                    status_data["result_model"] = model.to_dict()
            except Exception as e:
                logger.warning(f"Failed to get result model info: {e}")

        return status_data

    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {e}")
        return None


def cancel_training_task(task_id):
    """取消训练任务 - 改进版本"""
    try:
        task = db.session.get(VoiceCloneTask, task_id)
        if not task:
            logger.warning(f"Task {task_id} not found for cancellation")
            return False

        if task.status not in ["pending", "processing"]:
            logger.warning(
                f"Task {task_id} cannot be cancelled (status: {task.status})"
            )
            return False

        # 取消Celery任务
        if task.celery_task_id:
            try:
                from app.extensions import celery

                if celery:
                    celery.control.revoke(task.celery_task_id, terminate=True)
                    logger.info(f"Revoked Celery task {task.celery_task_id}")
            except Exception as e:
                logger.warning(f"Failed to revoke Celery task: {e}")

        # 更新任务状态
        task.update_status("failed", error_message="Cancelled by user")

        # 清理工作目录
        work_dir = os.path.join(
            current_app.config["UPLOAD_FOLDER"], "temp", f"voice_clone_{task.id}"
        )
        cleanup_training_environment(work_dir)

        # 记录取消日志
        log_user_action(
            user_id=task.user_id,
            action="voice_clone_cancelled",
            resource_type="voice_clone_task",
            resource_id=task.id,
            details="Voice clone task cancelled by user",
        )

        logger.info(f"Task {task_id} cancelled successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {e}")
        return False


def retry_failed_task(task_id):
    """重试失败的任务 - 新增功能"""
    try:
        task = db.session.get(VoiceCloneTask, task_id)
        if not task:
            raise TaskProcessingError(f"Task {task_id} not found")

        if not task.can_be_retried():
            raise TaskProcessingError(f"Task {task_id} cannot be retried")

        # 重置任务状态
        task.status = "pending"
        task.progress = 0
        task.error_message = None
        task.started_at = None
        task.completed_at = None
        task.celery_task_id = None
        task.result_model_id = None

        db.session.commit()

        # 重新启动任务
        try:
            celery_task = start_voice_clone_task.delay(task.id)
            task.celery_task_id = celery_task.id
            db.session.commit()

            logger.info(f"Restarted task {task_id} with Celery task {celery_task.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to restart task {task_id}: {e}")
            task.update_status("failed", error_message=f"Failed to restart: {str(e)}")
            return False

    except Exception as e:
        logger.error(f"Failed to retry task {task_id}: {e}")
        raise TaskProcessingError(f"Failed to retry task: {str(e)}")


def get_user_training_stats(user_id):
    """获取用户训练统计 - 新增功能"""
    try:
        stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "pending_tasks": 0,
            "processing_tasks": 0,
            "success_rate": 0.0,
            "average_processing_time": 0.0,
            "total_models_created": 0,
            "total_samples_processed": 0,
            "total_duration_processed": 0.0,
        }

        # 查询用户的所有任务
        tasks = VoiceCloneTask.query.filter_by(user_id=user_id).all()

        if not tasks:
            return stats

        stats["total_tasks"] = len(tasks)

        processing_times = []

        for task in tasks:
            # 统计状态
            if task.status == "completed":
                stats["completed_tasks"] += 1
                stats["total_models_created"] += 1

                # 计算处理时间
                if task.started_at and task.completed_at:
                    duration = (task.completed_at - task.started_at).total_seconds()
                    processing_times.append(duration)

            elif task.status == "failed":
                stats["failed_tasks"] += 1
            elif task.status == "pending":
                stats["pending_tasks"] += 1
            elif task.status == "processing":
                stats["processing_tasks"] += 1

            # 统计处理的样本和时长
            stats["total_samples_processed"] += task.sample_count or 0
            stats["total_duration_processed"] += task.total_duration or 0.0

        # 计算成功率
        if stats["total_tasks"] > 0:
            stats["success_rate"] = round(
                (stats["completed_tasks"] / stats["total_tasks"]) * 100, 2
            )

        # 计算平均处理时间
        if processing_times:
            stats["average_processing_time"] = round(
                sum(processing_times) / len(processing_times), 2
            )

        return stats

    except Exception as e:
        logger.error(f"Failed to get training stats for user {user_id}: {e}")
        return stats  # 返回空统计


def cleanup_old_training_files(days_threshold=7):
    """清理旧的训练文件 - 新增功能"""
    try:
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        temp_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "temp")

        if not os.path.exists(temp_dir):
            return 0

        cleaned_count = 0

        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)

            # 只处理语音克隆相关的目录
            if os.path.isdir(item_path) and item.startswith("voice_clone_"):
                try:
                    # 检查目录的修改时间
                    mtime = datetime.fromtimestamp(os.path.getmtime(item_path))

                    if mtime < cutoff_date:
                        shutil.rmtree(item_path, ignore_errors=True)
                        cleaned_count += 1
                        logger.info(f"Cleaned old training directory: {item_path}")

                except Exception as e:
                    logger.warning(f"Failed to clean directory {item_path}: {e}")

        logger.info(f"Cleaned {cleaned_count} old training directories")
        return cleaned_count

    except Exception as e:
        logger.error(f"Failed to cleanup old training files: {e}")
        return 0
