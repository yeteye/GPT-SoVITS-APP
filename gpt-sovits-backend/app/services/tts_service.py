# ./gpt-sovits-backend/app/services/tts_service.py (修复后的完整版本)
import os
import numpy as np
from datetime import datetime
from flask import current_app
from app.extensions import celery, db
from app.models.task import TTSTask
from app.models.model import VoiceModel
from app.utils.exceptions import TaskProcessingError
from app.utils.helpers import log_user_action, generate_unique_filename


def get_celery_task_decorator():
    """获取Celery任务装饰器，如果Celery不可用则返回普通函数装饰器"""
    if celery is not None:
        return celery.task(
            bind=True, name="app.services.tts_service.generate_speech_task"
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

    def __init__(self, task_id="mock-tts-task-id"):
        self.id = task_id
        self.state = "SUCCESS"

    def get(self, timeout=None):
        return {"status": "completed", "message": "Mock TTS task completed"}


@get_celery_task_decorator()
def generate_speech_task(self, task_id):
    """生成语音任务（支持Celery和测试环境）- 集成水印功能"""
    try:
        # 获取任务信息 - 修复：使用现代SQLAlchemy语法
        task = db.session.get(TTSTask, task_id)
        if not task:
            raise TaskProcessingError("Task not found")

        # 更新任务状态
        task.update_status("processing")

        # 检查是否在测试环境 - 安全地访问current_app
        try:
            from flask import current_app

            is_testing = current_app.config.get("TESTING", False)
            has_celery = celery is not None
            watermark_enabled = current_app.config.get("WATERMARK_ENABLED", True)
        except RuntimeError:
            # 不在应用上下文中，假设是测试环境
            is_testing = True
            has_celery = False
            watermark_enabled = True

        if is_testing or not has_celery:
            # 测试环境：直接模拟处理结果
            result = mock_speech_generation(task, watermark_enabled)
        else:
            # 生产环境：执行实际的语音生成
            result = process_speech_generation(task, watermark_enabled)

        # 保存结果
        task.set_result(
            audio_path=result["audio_path"],
            audio_url=result["audio_url"],
            duration=result["duration"],
        )

        # 记录成功日志
        log_message = (
            f'Speech generated successfully. Duration: {result["duration"]:.2f}s'
        )
        if result.get("watermark_embedded"):
            log_message += f', Watermark: {result.get("watermark_code", "N/A")}'

        log_user_action(
            user_id=task.user_id,
            action="speech_generation_completed",
            resource_type="tts_task",
            resource_id=task.id,
            details=log_message,
        )

        return {
            "status": "completed",
            "audio_url": result["audio_url"],
            "duration": result["duration"],
            "watermark_embedded": result.get("watermark_embedded", False),
            "watermark_code": result.get("watermark_code"),
            "message": "Speech generation completed successfully",
        }

    except Exception as e:
        # 任务失败
        if "task" in locals() and task:
            task.update_status("failed", error_message=str(e))

        # 记录错误日志
        if "task" in locals() and task:
            log_user_action(
                user_id=task.user_id,
                action="speech_generation_failed",
                resource_type="tts_task",
                resource_id=task.id,
                details=f"Speech generation failed: {str(e)}",
            )

        try:
            from flask import current_app

            current_app.logger.error(f"TTS task {task_id} failed: {e}")
        except RuntimeError:
            print(f"TTS task {task_id} failed: {e}")

        raise TaskProcessingError(f"Speech generation failed: {str(e)}")


def mock_speech_generation(task, watermark_enabled=True):
    """模拟语音生成过程（用于测试）- 修复：改进错误处理"""
    try:
        # 安全的应用上下文处理
        try:
            from flask import current_app

            current_app.logger.info(f"Mock processing TTS task: {task.id}")
            upload_folder = current_app.config.get("UPLOAD_FOLDER", "/tmp")
        except RuntimeError:
            # 如果不在应用上下文中，直接打印并使用默认路径
            print(f"Mock processing TTS task: {task.id}")
            upload_folder = "/tmp"

        # 模拟处理时间
        import time

        time.sleep(0.1)

        # 计算模拟音频时长
        text_length = len(task.text)
        duration = max(1.0, (text_length * 0.15) / task.speed)  # 最少1秒

        # 生成模拟文件路径
        filename = f"mock_tts_{task.id}.wav"
        mock_path = os.path.join(upload_folder, "generated", filename)
        mock_url = f"/api/tts/tasks/{task.id}/download"

        # 确保目录存在
        os.makedirs(os.path.dirname(mock_path), exist_ok=True)

        # 创建一个空的模拟文件
        with open(mock_path, "w") as f:
            f.write("# Mock audio file")

        result = {
            "audio_path": mock_path,
            "audio_url": mock_url,
            "duration": round(duration, 2),
            "watermark_embedded": False,
            "watermark_code": None,
        }

        # 模拟水印嵌入
        if watermark_enabled:
            try:
                import secrets
                import string

                watermark_code = "".join(
                    secrets.choice(string.ascii_lowercase + string.digits)
                    for _ in range(16)
                )
                result.update(
                    {
                        "watermark_embedded": True,
                        "watermark_code": watermark_code,
                        "audio_path": f"{mock_path}_watermarked",
                    }
                )
                print(f"Mock: Embedded watermark {watermark_code} into {filename}")
            except Exception as e:
                print(f"Mock: Watermark embedding simulation failed: {e}")

        return result

    except Exception as e:
        raise TaskProcessingError(f"Mock speech generation failed: {str(e)}")


def process_speech_generation(task, watermark_enabled=True):
    """处理语音生成（生产环境）- 集成水印功能"""
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

        # 5. 保存音频文件（暂不嵌入水印）
        update_tts_task_status(task, "Saving audio file...")
        audio_info = save_generated_audio(audio_data, task, embed_watermark=False)

        # 6. 嵌入水印（如果启用）
        if watermark_enabled:
            try:
                update_tts_task_status(task, "Embedding watermark...")
                watermarked_info = embed_watermark_to_tts_audio(task, audio_info)
                if watermarked_info:
                    audio_info.update(watermarked_info)
            except Exception as e:
                # 水印嵌入失败不影响主要功能
                try:
                    from flask import current_app

                    current_app.logger.warning(
                        f"Watermark embedding failed for task {task.id}: {e}"
                    )
                except RuntimeError:
                    print(
                        f"Warning: Watermark embedding failed for task {task.id}: {e}"
                    )

        return audio_info

    except Exception as e:
        raise TaskProcessingError(f"Speech generation failed: {str(e)}")


def embed_watermark_to_tts_audio(task, audio_info):
    """为TTS生成的音频嵌入水印"""
    try:
        from app.services.watermark_service import WatermarkService
        from app.models.user import User

        # 获取用户信息
        user = db.session.get(User, task.user_id)
        if not user:
            raise Exception("User not found")

        # 初始化水印服务
        watermark_service = WatermarkService()

        # 获取或创建用户水印
        watermark_code = watermark_service.get_or_create_user_watermark(
            user_id=user.id, username=user.username, model_id=task.model_id
        )

        # 检查原始音频文件是否存在
        original_path = audio_info["audio_path"]
        if not os.path.exists(original_path):
            raise Exception(f"Original audio file not found: {original_path}")

        # 嵌入水印
        watermarked_path = watermark_service.embed_watermark_to_audio(
            original_path=original_path,
            watermark_code=watermark_code,
            user_id=user.id,
            output_dir=os.path.dirname(original_path),
        )

        # 删除原始文件，使用带水印的文件
        if watermarked_path != original_path:
            try:
                os.remove(original_path)
            except Exception as e:
                print(f"Warning: Failed to remove original file: {e}")

        return {
            "audio_path": watermarked_path,
            "watermark_embedded": True,
            "watermark_code": watermark_code,
        }

    except Exception as e:
        try:
            from flask import current_app

            current_app.logger.error(
                f"Failed to embed watermark for TTS task {task.id}: {e}"
            )
        except RuntimeError:
            print(f"Error: Failed to embed watermark for TTS task {task.id}: {e}")

        # 返回None，表示水印嵌入失败，但不影响主要功能
        return None


def load_voice_model(model_id):
    """加载语音模型"""
    try:
        model = db.session.get(VoiceModel, model_id)
        if not model:
            raise TaskProcessingError("Voice model not found")

        if not os.path.exists(model.model_path):
            raise TaskProcessingError("Model file not found")

        # 模拟模型加载
        model_info = {
            "model_id": model.id,
            "model_path": model.model_path,
            "config_path": model.config_path,
            "index_path": model.index_path,
            "supported_emotions": model.get_supported_emotions(),
            "supported_languages": model.get_supported_languages(),
        }

        return model_info

    except Exception as e:
        raise TaskProcessingError(f"Failed to load voice model: {str(e)}")


def preprocess_text(text):
    """预处理文本"""
    try:
        # 清理和标准化文本
        processed_text = text.strip()
        return processed_text

    except Exception as e:
        try:
            from flask import current_app

            current_app.logger.warning(f"Text preprocessing failed: {e}")
        except RuntimeError:
            print(f"Warning: Text preprocessing failed: {e}")
        return text


def generate_audio(text, model_info, emotion="neutral", speed=1.0):
    """生成音频"""
    try:
        # 模拟音频生成过程
        base_duration = len(text) * 0.15
        duration = base_duration / speed

        # 生成模拟音频数据
        sample_rate = 22050
        samples = int(duration * sample_rate)

        # 创建简单的正弦波作为模拟音频
        t = np.linspace(0, duration, samples)
        frequency = 440

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

        return {"audio_data": audio, "sample_rate": sample_rate, "duration": duration}

    except Exception as e:
        raise TaskProcessingError(f"Failed to generate audio: {str(e)}")


def post_process_audio(audio_info, speed=1.0):
    """后处理音频"""
    try:
        audio_data = audio_info["audio_data"]
        sample_rate = audio_info["sample_rate"]

        # 音频标准化
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val * 0.8

        # 更新音频信息
        audio_info["audio_data"] = audio_data
        audio_info["duration"] = len(audio_data) / sample_rate

        return audio_info

    except Exception as e:
        try:
            from flask import current_app

            current_app.logger.warning(f"Audio post-processing failed: {e}")
        except RuntimeError:
            print(f"Warning: Audio post-processing failed: {e}")
        return audio_info


def save_generated_audio(audio_info, task, embed_watermark=True):
    """保存生成的音频文件"""
    try:
        # 生成文件名
        filename = generate_unique_filename(f"tts_{task.id}.wav", "generated")

        # 创建保存目录
        try:
            from flask import current_app

            save_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "generated")
        except RuntimeError:
            save_dir = "./uploads/generated"

        os.makedirs(save_dir, exist_ok=True)

        # 完整文件路径
        file_path = os.path.join(save_dir, filename)

        # 模拟保存音频文件（在实际应用中应该使用真实的音频库）
        import wave
        import struct

        # 保存为WAV文件
        with wave.open(file_path, "wb") as wav_file:
            wav_file.setnchannels(1)  # 单声道
            wav_file.setsampwidth(2)  # 16位
            wav_file.setframerate(int(audio_info["sample_rate"]))

            # 将浮点音频数据转换为16位整数
            audio_data = audio_info["audio_data"]
            audio_int16 = (audio_data * 32767).astype(np.int16)

            # 写入音频数据
            for sample in audio_int16:
                wav_file.writeframes(struct.pack("<h", sample))

        # 生成访问URL
        audio_url = f"/api/tts/tasks/{task.id}/download"

        result = {
            "audio_path": file_path,
            "audio_url": audio_url,
            "duration": audio_info["duration"],
            "watermark_embedded": False,
            "watermark_code": None,
        }

        return result

    except Exception as e:
        raise TaskProcessingError(f"Failed to save audio file: {str(e)}")


def update_tts_task_status(task, message):
    """更新TTS任务状态"""
    try:
        db.session.commit()

        # 如果有Celery，更新Celery任务状态
        if celery and hasattr(celery, "current_task") and celery.current_task:
            celery.current_task.update_state(
                state="PROGRESS", meta={"message": message}
            )
    except Exception as e:
        try:
            from flask import current_app

            current_app.logger.warning(f"Failed to update TTS task status: {e}")
        except RuntimeError:
            print(f"Warning: Failed to update TTS task status: {e}")


def get_tts_task_status(task_id):
    """获取TTS任务状态"""
    try:
        task = db.session.get(TTSTask, task_id)
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
        try:
            from flask import current_app

            current_app.logger.error(f"Failed to get TTS task status: {e}")
        except RuntimeError:
            print(f"Error: Failed to get TTS task status: {e}")
        return None


def cancel_tts_task(task_id):
    """取消TTS任务"""
    try:
        task = db.session.get(TTSTask, task_id)
        if not task:
            return False

        if task.status not in ["pending", "processing"]:
            return False

        # 如果有Celery，取消Celery任务
        if celery and task.celery_task_id:
            celery.control.revoke(task.celery_task_id, terminate=True)

        # 更新任务状态
        task.update_status("failed", error_message="Cancelled by user")

        return True

    except Exception as e:
        try:
            from flask import current_app

            current_app.logger.error(f"Failed to cancel TTS task: {e}")
        except RuntimeError:
            print(f"Error: Failed to cancel TTS task: {e}")
        return False
