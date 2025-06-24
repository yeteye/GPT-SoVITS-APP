# ./gpt-sovits-backend/app/services/voice_clone_service.py
import os
import shutil
import subprocess
import soundfile as sf
from pydub import AudioSegment
from datetime import datetime
from flask import current_app
from app.extensions import celery, db
from app.models.task import VoiceCloneTask
from app.models.model import VoiceModel
from app.utils.exceptions import TaskProcessingError
from app.utils.helpers import log_user_action


def get_celery_task_decorator():
    """获取Celery任务装饰器，如果Celery不可用则返回普通函数装饰器"""
    if celery is not None:
        return celery.task(
            bind=True, name="app.services.voice_clone_service.clone_voice_task"
        )
    else:
        # 测试环境或没有Celery时的装饰器
        def mock_decorator(func):
            def wrapper(self_or_task_id, task_id=None):
                # 处理两种调用方式：
                # 1. 直接调用：func(None, task_id)
                # 2. Celery风格调用：func(self, task_id)
                if task_id is None:
                    # 直接调用：第一个参数是task_id
                    return func(None, self_or_task_id)
                else:
                    # Celery风格调用：第一个参数是self
                    return func(self_or_task_id, task_id)

            wrapper.delay = lambda task_id: MockCeleryResult()
            wrapper.apply_async = lambda task_id: MockCeleryResult()
            return wrapper

        return mock_decorator


class MockCeleryResult:
    """模拟Celery任务结果"""

    # 这个类用于模拟Celery任务的结果对象, 需要
    def __init__(self, task_id="mock-task-id"):
        self.id = task_id
        self.state = "SUCCESS"

    def get(self, timeout=None):
        return {"status": "completed", "message": "Mock task completed"}


# 使用动态装饰器
@get_celery_task_decorator()
def start_voice_clone_task(self, task_id):
    """启动语音克隆任务（支持Celery和测试环境）"""
    try:
        # 获取任务信息
        task = db.session.get(VoiceCloneTask, task_id)
        if not task:
            raise TaskProcessingError("Task not found")

        # 更新任务状态
        task.update_status("processing", progress=0)

        # 检查是否在测试环境
        if current_app.config.get("TESTING", False) or celery is None:
            # 测试环境：直接模拟处理结果
            result = mock_voice_clone_process(task)
        else:
            # 生产环境：执行实际的语音克隆
            result = process_voice_clone(task)

        # 任务完成
        task.update_status("completed", progress=100)
        task.result_model_id = result["model_id"]
        db.session.commit()

        # 记录成功日志
        log_user_action(
            user_id=task.user_id,
            action="voice_clone_completed",
            resource_type="voice_clone_task",
            resource_id=task.id,
            details=f'Voice clone training completed successfully. Model ID: {result["model_id"]}',
        )

        return {
            "status": "completed",
            "model_id": result["model_id"],
            "message": "Voice clone training completed successfully",
        }

    except Exception as e:
        # 任务失败
        if task:
            task.update_status("failed", error_message=str(e))

        # 记录错误日志
        if task:
            log_user_action(
                user_id=task.user_id,
                action="voice_clone_failed",
                resource_type="voice_clone_task",
                resource_id=task.id,
                details=f"Voice clone training failed: {str(e)}",
            )

        current_app.logger.error(f"Voice clone task {task_id} failed: {e}")
        raise TaskProcessingError(f"Voice clone training failed: {str(e)}")


def mock_voice_clone_process(task):
    """模拟语音克隆处理过程（用于测试）"""
    try:
        current_app.logger.info(f"Mock processing voice clone task: {task.id}")

        # 模拟处理时间
        import time

        time.sleep(0.1)

        # 创建模拟的语音模型
        voice_model = VoiceModel(
            name=task.model_name or f"Test_Model_{task.id}",
            description=f"Mock voice model generated from task {task.id}",
            model_type="user_trained",
            owner_id=task.user_id,
            model_path=f"/mock/path/model_{task.id}.pth",
            config_path=f"/mock/path/config_{task.id}.json",
            quality_score=7.5,
            status="active",
            is_public=False,
        )

        # 设置支持的情感和语言
        voice_model.set_supported_emotions(["neutral", "happy", "sad"])
        voice_model.set_supported_languages(["zh-CN"])

        db.session.add(voice_model)
        db.session.commit()

        return {
            "model_id": voice_model.id,
            "model_path": voice_model.model_path,
            "quality_score": voice_model.quality_score,
        }

    except Exception as e:
        raise TaskProcessingError(f"Mock voice clone process failed: {str(e)}")


def process_voice_clone(task):
    """处理语音克隆流程（生产环境）"""
    try:
        # 1. 准备工作目录
        work_dir = prepare_training_environment(task)

        # 2. 预处理音频文件
        update_task_progress(task, 10, "Preprocessing audio files...")
        preprocessed_files = preprocess_audio_files(
            task, work_dir, target_sample_rate=16000
        )

        # 3. 提取音频特征
        update_task_progress(task, 30, "Extracting audio features...")
        features = extract_audio_features(preprocessed_files, work_dir)

        # 4. 训练语音模型
        update_task_progress(task, 50, "Training voice model...")
        model_files = train_voice_model(features, work_dir, task)

        # 5. 验证模型质量
        update_task_progress(task, 80, "Validating model quality...")
        quality_score = validate_model_quality(model_files, preprocessed_files)

        # 6. 保存模型
        update_task_progress(task, 90, "Saving model...")
        model_info = save_trained_model(task, model_files, quality_score)

        # 7. 清理临时文件
        cleanup_training_environment(work_dir)

        return model_info

    except Exception as e:
        # 清理临时文件
        if "work_dir" in locals():
            cleanup_training_environment(work_dir)
        raise e


def prepare_training_environment(task):
    """准备训练环境"""
    try:
        # 创建工作目录
        work_dir = os.path.join(
            current_app.config["UPLOAD_FOLDER"], "temp", f"voice_clone_{task.id}"
        )
        os.makedirs(work_dir, exist_ok=True)

        # 创建子目录
        subdirs = ["input", "processed", "features", "models", "output"]
        for subdir in subdirs:
            os.makedirs(os.path.join(work_dir, subdir), exist_ok=True)

        return work_dir

    except Exception as e:
        raise TaskProcessingError(f"Failed to prepare training environment: {str(e)}")


def preprocess_audio_files(task, work_dir, target_sample_rate=16000):
    """对音频文件进行预处理（采样率、通道数、格式标准化）"""
    try:
        audio_samples = task.get_audio_samples()
        preprocessed_files = []
        processed_dir = os.path.join(work_dir, "processed")

        os.makedirs(processed_dir, exist_ok=True)

        for i, audio_path in enumerate(audio_samples):
            if not os.path.exists(audio_path):
                current_app.logger.warning(f"Audio file not found: {audio_path}")
                continue

            try:
                # 加载原始音频（pydub 支持多数格式）
                audio = AudioSegment.from_file(audio_path)

                # 转为单声道 & 目标采样率
                audio = audio.set_channels(1).set_frame_rate(target_sample_rate)

                # 输出路径
                output_path = os.path.join(processed_dir, f"sample_{i}.wav")

                # 导出为 wav 文件
                audio.export(output_path, format="wav")

                preprocessed_files.append(output_path)
            except Exception as e:
                current_app.logger.warning(f"Failed to process {audio_path}: {e}")
                continue

        if not preprocessed_files:
            raise TaskProcessingError("No valid audio files to process")

        return preprocessed_files

    except Exception as e:
        raise TaskProcessingError(f"Failed to preprocess audio files: {str(e)}")


import os
import numpy as np
import librosa
import soundfile as sf
from app.utils.exceptions import TaskProcessingError


def extract_audio_features(audio_files, work_dir, sample_rate=16000):
    """从多个音频文件中提取 MFCC、Mel Spectrogram 和 F0 特征"""
    try:
        # 确保特征输出目录存在
        feature_dir = os.path.join(work_dir, "features")
        os.makedirs(feature_dir, exist_ok=True)

        features = {
            "mfcc": [],
            "mel_spectrogram": [],
            "f0": [],
        }

        for audio_file in audio_files:
            try:
                # 加载音频，强制指定采样率（避免 librosa 自动重采样）
                y, sr = librosa.load(audio_file, sr=sample_rate)

                # --- MFCC ---
                mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)  # (13, T)

                # --- Mel Spectrogram ---
                mel = librosa.feature.melspectrogram(
                    y=y, sr=sr, n_mels=80, fmax=sr // 2
                )
                mel_db = librosa.power_to_db(mel, ref=np.max)  # dB 归一化

                # --- F0 (基频) ---
                f0, voiced_flag, voiced_probs = librosa.pyin(
                    y,
                    sr=sr,
                    fmin=librosa.note_to_hz("C2"),
                    fmax=librosa.note_to_hz("C7"),
                )
                # 补全无声段为0
                f0 = np.nan_to_num(f0)

                features["mfcc"].append(mfcc)
                features["mel_spectrogram"].append(mel_db)
                features["f0"].append(f0)

            except Exception as e:
                print(f"Feature extraction failed for {audio_file}: {e}")
                continue

        # 保存为 .npz
        feature_file = os.path.join(feature_dir, "extracted_features.npz")
        np.savez(feature_file, **features)

        return feature_file

    except Exception as e:
        raise TaskProcessingError(f"Failed to extract audio features: {str(e)}")


def train_voice_model(features_file, work_dir, task):
    """训练语音模型"""
    try:
        model_dir = os.path.join(work_dir, "models")

        # 模拟训练过程, 需要修改
        # 实际应用中应该调用真实的训练脚本或库
        model_files = {
            "model_path": os.path.join(model_dir, f"{task.model_name}.pth"),
            "config_path": os.path.join(model_dir, f"{task.model_name}_config.json"),
            "index_path": os.path.join(model_dir, f"{task.model_name}.index"),
        }

        # 创建模拟模型文件, 需要修改
        for file_path in model_files.values():
            with open(file_path, "w") as f:
                f.write(f"# Simulated model file for {task.model_name}\n")

        return model_files

    except Exception as e:
        raise TaskProcessingError(f"Failed to train voice model: {str(e)}")


def validate_model_quality(model_files, audio_files):
    """验证模型质量"""
    try:
        # 简化的质量评估, 需要修改
        # 实际应用中应该使用更复杂的评估方法
        quality_score = 7.5

        # 检查模型文件是否存在
        for file_path in model_files.values():
            if not os.path.exists(file_path):
                quality_score -= 1.0

        # 根据样本数量调整质量分数
        sample_count = len(audio_files)
        if sample_count >= 10:
            quality_score += 1.0
        elif sample_count >= 5:
            quality_score += 0.5

        # 确保分数在合理范围内
        quality_score = max(0.0, min(10.0, quality_score))

        return quality_score

    except Exception as e:
        current_app.logger.warning(f"Model quality validation failed: {e}")
        return 5.0


def save_trained_model(task, model_files, quality_score):
    """保存训练好的模型"""
    try:
        # 创建模型存储目录
        model_storage_dir = os.path.join(
            current_app.config["UPLOAD_FOLDER"],
            "models",
            f"user_{task.user_id}",
            task.model_name,
        )
        os.makedirs(model_storage_dir, exist_ok=True)

        # 复制模型文件到存储目录
        stored_files = {}
        for file_type, src_path in model_files.items():
            if os.path.exists(src_path):
                dst_path = os.path.join(model_storage_dir, os.path.basename(src_path))
                shutil.copy2(src_path, dst_path)
                stored_files[file_type] = dst_path

        # 创建VoiceModel记录
        voice_model = VoiceModel(
            name=task.model_name,
            description=f"Voice model trained from {task.sample_count} audio samples",
            model_type="user_trained",
            owner_id=task.user_id,
            model_path=stored_files.get("model_path"),
            config_path=stored_files.get("config_path"),
            index_path=stored_files.get("index_path"),
            quality_score=quality_score,
            status="active",
            is_public=False,
        )

        # 设置支持的情感和语言
        voice_model.set_supported_emotions(["neutral", "happy", "sad", "angry"])
        voice_model.set_supported_languages(["zh-CN"])

        db.session.add(voice_model)
        db.session.commit()

        return {
            "model_id": voice_model.id,
            "model_path": voice_model.model_path,
            "quality_score": quality_score,
        }

    except Exception as e:
        raise TaskProcessingError(f"Failed to save trained model: {str(e)}")


def cleanup_training_environment(work_dir):
    """清理训练环境"""
    try:
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)
    except Exception as e:
        current_app.logger.warning(f"Failed to cleanup training environment: {e}")


def update_task_progress(task, progress, message=None):
    """更新任务进度"""
    try:
        task.progress = progress
        db.session.commit()

        # 如果有Celery，更新Celery任务状态
        if celery and hasattr(celery, "current_task") and celery.current_task:
            celery.current_task.update_state(
                state="PROGRESS", meta={"progress": progress, "message": message}
            )
    except Exception as e:
        current_app.logger.warning(f"Failed to update task progress: {e}")


# 其他函数保持不变...
def get_task_status(task_id):
    """获取任务状态"""
    try:
        task = VoiceCloneTask.query.get(task_id)
        if not task:
            return None

        return {
            "task_id": task.id,
            "status": task.status,
            "progress": task.progress,
            "error_message": task.error_message,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": (
                task.completed_at.isoformat() if task.completed_at else None
            ),
        }
    except Exception as e:
        current_app.logger.error(f"Failed to get task status: {e}")
        return None


def cancel_training_task(task_id):
    """取消训练任务"""
    try:
        task = VoiceCloneTask.query.get(task_id)
        if not task:
            return False

        if task.status not in ["pending", "processing"]:
            return False

        # 如果有Celery，取消Celery任务
        if celery and task.celery_task_id:
            celery.control.revoke(task.celery_task_id, terminate=True)

        # 更新任务状态
        task.update_status("failed", error_message="Cancelled by user")

        # 清理工作目录
        work_dir = os.path.join(
            current_app.config["UPLOAD_FOLDER"], "temp", f"voice_clone_{task.id}"
        )
        cleanup_training_environment(work_dir)

        return True

    except Exception as e:
        current_app.logger.error(f"Failed to cancel training task: {e}")
        return False
