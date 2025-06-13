import os
import torch
import numpy as np
from datetime import datetime
from celery import current_task
from app.extensions import celery, db
from app.models.task import TTSTask
from app.models.model import VoiceModel
from app.utils.exceptions import TaskProcessingError
from app.utils.helpers import log_user_action, generate_unique_filename
from flask import current_app


@celery.task(bind=True, name="app.services.tts_service.generate_speech_task")
def generate_speech_task(self, task_id):
    """生成语音任务（Celery任务）"""
    try:
        # 获取任务信息
        task = TTSTask.query.get(task_id)
        if not task:
            raise TaskProcessingError("Task not found")

        # 更新任务状态
        task.update_status("processing")

        # 执行语音生成
        result = process_speech_generation(task)

        # 保存结果
        task.set_result(
            audio_path=result["audio_path"],
            audio_url=result["audio_url"],
            duration=result["duration"],
        )

        # 记录成功日志
        log_user_action(
            user_id=task.user_id,
            action="speech_generation_completed",
            resource_type="tts_task",
            resource_id=task.id,
            details=f'Speech generated successfully. Duration: {result["duration"]:.2f}s',
        )

        return {
            "status": "completed",
            "audio_url": result["audio_url"],
            "duration": result["duration"],
            "message": "Speech generation completed successfully",
        }

    except Exception as e:
        # 任务失败
        if task:
            task.update_status("failed", error_message=str(e))

        # 记录错误日志
        if task:
            log_user_action(
                user_id=task.user_id,
                action="speech_generation_failed",
                resource_type="tts_task",
                resource_id=task.id,
                details=f"Speech generation failed: {str(e)}",
            )

        current_app.logger.error(f"TTS task {task_id} failed: {e}")
        raise TaskProcessingError(f"Speech generation failed: {str(e)}")


def process_speech_generation(task):
    """处理语音生成"""
    try:
        # 1. 加载语音模型
        update_tts_task_status(task, "Loading voice model...")
        model_info = load_voice_model(task.model_id)

        # 2. 预处理文本
        update_tts_task_status(task, "Processing text...")
        processed_text = preprocess_text(task.text)

        # 3. 生成语音
        update_tts_task_status(task, "Generating speech...")
        audio_data = generate_audio(
            text=processed_text,
            model_info=model_info,
            emotion=task.emotion,
            speed=task.speed,
        )

        # 4. 后处理音频
        update_tts_task_status(task, "Post-processing audio...")
        audio_data = post_process_audio(audio_data, task.speed)

        # 5. 保存音频文件
        update_tts_task_status(task, "Saving audio file...")
        audio_info = save_generated_audio(audio_data, task)

        return audio_info

    except Exception as e:
        raise TaskProcessingError(f"Speech generation failed: {str(e)}")


def load_voice_model(model_id):
    """加载语音模型"""
    try:
        model = VoiceModel.query.get(model_id)
        if not model:
            raise TaskProcessingError("Voice model not found")

        if not os.path.exists(model.model_path):
            raise TaskProcessingError("Model file not found")

        # 这里简化处理，实际应加载GPT-SoVITS模型
        model_info = {
            "model_id": model.id,
            "model_path": model.model_path,
            "config_path": model.config_path,
            "index_path": model.index_path,
            "supported_emotions": model.get_supported_emotions(),
            "supported_languages": model.get_supported_languages(),
        }

        # 在实际实现中，这里应该加载模型权重
        # model_weights = torch.load(model.model_path, map_location='cpu')
        # model_info['weights'] = model_weights

        return model_info

    except Exception as e:
        raise TaskProcessingError(f"Failed to load voice model: {str(e)}")


def preprocess_text(text):
    """预处理文本"""
    try:
        # 清理和标准化文本
        processed_text = text.strip()

        # 处理标点符号
        import re

        # 标准化标点符号
        processed_text = re.sub(
            r'[，。！？；：""' "（）【】]",
            lambda m: {
                "，": ",",
                "。": ".",
                "！": "!",
                "？": "?",
                "；": ";",
                "：": ":",
                '""': '"',
                "''": "'",
                "（": "(",
                "）": ")",
                "【": "[",
                "】": "]",
            }.get(m.group(), m.group()),
            processed_text,
        )

        # 处理数字（可以扩展为数字转文字）
        processed_text = re.sub(
            r"\d+", lambda m: convert_number_to_text(m.group()), processed_text
        )

        # 处理英文单词（可以扩展为发音标注）
        processed_text = re.sub(
            r"[a-zA-Z]+", lambda m: process_english_word(m.group()), processed_text
        )

        return processed_text

    except Exception as e:
        current_app.logger.warning(f"Text preprocessing failed: {e}")
        return text  # 返回原文本


def convert_number_to_text(number_str):
    """数字转文字（简化版）"""
    try:
        num = int(number_str)

        # 简单的数字转换（可以扩展为完整的中文数字转换）
        digit_map = {
            "0": "零",
            "1": "一",
            "2": "二",
            "3": "三",
            "4": "四",
            "5": "五",
            "6": "六",
            "7": "七",
            "8": "八",
            "9": "九",
        }

        if num < 10:
            return digit_map[str(num)]
        elif num < 100:
            tens = num // 10
            ones = num % 10
            if ones == 0:
                return digit_map[str(tens)] + "十"
            else:
                return digit_map[str(tens)] + "十" + digit_map[str(ones)]
        else:
            # 更复杂的数字转换
            return number_str  # 简化处理

    except:
        return number_str


def process_english_word(word):
    """处理英文单词（简化版）"""
    # 这里可以添加英文发音标注
    # 简化处理，直接返回原单词
    return word


def generate_audio(text, model_info, emotion="neutral", speed=1.0):
    """生成音频"""
    try:
        # 这里应该调用实际的GPT-SoVITS推理代码
        # 由于模型复杂性，这里提供框架代码

        # 模拟音频生成过程
        import numpy as np

        # 计算音频长度（基于文本长度和语速）
        base_duration = len(text) * 0.15  # 每个字符大约0.15秒
        duration = base_duration / speed

        # 生成模拟音频数据
        sample_rate = 22050
        samples = int(duration * sample_rate)

        # 创建简单的正弦波作为模拟音频
        t = np.linspace(0, duration, samples)
        frequency = 440  # A4音符

        # 根据情感调整频率
        emotion_freq_map = {
            "happy": 1.2,
            "sad": 0.8,
            "angry": 1.5,
            "calm": 0.9,
            "excited": 1.3,
            "fearful": 1.1,
            "surprised": 1.4,
            "disgusted": 0.7,
            "neutral": 1.0,
        }

        freq_multiplier = emotion_freq_map.get(emotion, 1.0)
        frequency *= freq_multiplier

        # 生成音频波形
        audio = np.sin(2 * np.pi * frequency * t) * 0.3

        # 添加一些随机性使其更像语音
        noise = np.random.normal(0, 0.05, samples)
        audio += noise

        # 应用包络以避免突然开始/结束
        fade_samples = int(0.1 * sample_rate)  # 0.1秒淡入淡出
        audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
        audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)

        return {"audio_data": audio, "sample_rate": sample_rate, "duration": duration}

    except Exception as e:
        raise TaskProcessingError(f"Failed to generate audio: {str(e)}")


def post_process_audio(audio_info, speed=1.0):
    """后处理音频"""
    try:
        import librosa

        audio_data = audio_info["audio_data"]
        sample_rate = audio_info["sample_rate"]

        # 应用语速调整（如果需要）
        if speed != 1.0:
            audio_data = librosa.effects.time_stretch(audio_data, rate=speed)

        # 音频标准化
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val * 0.8  # 标准化到80%音量

        # 更新音频信息
        audio_info["audio_data"] = audio_data
        audio_info["duration"] = len(audio_data) / sample_rate

        return audio_info

    except Exception as e:
        current_app.logger.warning(f"Audio post-processing failed: {e}")
        return audio_info  # 返回原音频


def save_generated_audio(audio_info, task):
    """保存生成的音频文件"""
    try:
        import soundfile as sf

        # 生成文件名
        filename = generate_unique_filename(f"tts_{task.id}.wav", "generated")

        # 创建保存目录
        save_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "generated")
        os.makedirs(save_dir, exist_ok=True)

        # 完整文件路径
        file_path = os.path.join(save_dir, filename)

        # 保存音频文件
        sf.write(
            file_path,
            audio_info["audio_data"],
            audio_info["sample_rate"],
            format="WAV",
            subtype="PCM_16",
        )

        # 生成访问URL（简化处理）
        audio_url = f"/api/tts/tasks/{task.id}/download"

        return {
            "audio_path": file_path,
            "audio_url": audio_url,
            "duration": audio_info["duration"],
        }

    except Exception as e:
        raise TaskProcessingError(f"Failed to save audio file: {str(e)}")


def update_tts_task_status(task, message):
    """更新TTS任务状态"""
    try:
        # 这里可以扩展为更详细的状态跟踪
        db.session.commit()

        # 更新Celery任务状态
        if current_task:
            current_task.update_state(state="PROGRESS", meta={"message": message})
    except Exception as e:
        current_app.logger.warning(f"Failed to update TTS task status: {e}")


def get_tts_task_status(task_id):
    """获取TTS任务状态"""
    try:
        task = TTSTask.query.get(task_id)
        if not task:
            return None

        return {
            "task_id": task.id,
            "status": task.status,
            "text": task.text,
            "emotion": task.emotion,
            "speed": task.speed,
            "audio_url": task.audio_url,
            "duration": task.audio_duration,
            "error_message": task.error_message,
            "created_at": task.created_at.isoformat(),
            "completed_at": (
                task.completed_at.isoformat() if task.completed_at else None
            ),
        }
    except Exception as e:
        current_app.logger.error(f"Failed to get TTS task status: {e}")
        return None


def cancel_tts_task(task_id):
    """取消TTS任务"""
    try:
        task = TTSTask.query.get(task_id)
        if not task:
            return False

        if task.status not in ["pending", "processing"]:
            return False

        # 取消Celery任务
        if task.celery_task_id:
            from app.extensions import celery

            celery.control.revoke(task.celery_task_id, terminate=True)

        # 更新任务状态
        task.update_status("failed", error_message="Cancelled by user")

        return True

    except Exception as e:
        current_app.logger.error(f"Failed to cancel TTS task: {e}")
        return False
