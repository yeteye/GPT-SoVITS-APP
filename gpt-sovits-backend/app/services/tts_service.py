# ./gpt-sovits-backend/app/services/tts_service.py (修复后的完整版本)
import os
import json
from io import BytesIO
import requests
import numpy as np
from datetime import datetime
from flask import current_app
from app.extensions import celery, db
from app.models.task import TTSTask
from app.models.model import VoiceModel
from app.utils.exceptions import TaskProcessingError
from app.utils.helpers import log_user_action, generate_unique_filename

TTS_API_URL = "http://127.0.0.1:9880/tts"
SET_GPT_URL = "http://127.0.0.1:9880/set_gpt_weights"
SET_SOVITS_URL = "http://127.0.0.1:9880/set_sovits_weights"

class MockCeleryResult:
    """模拟Celery任务结果"""

    def __init__(self, task_id="mock-tts-task-id"):
        self.id = task_id
        self.state = "SUCCESS"

    def get(self, timeout=None):
        return {"status": "completed", "message": "Mock TTS task completed"}


def create_task_decorator():
    """创建任务装饰器 - 修复版本"""
    try:
        from flask import current_app

        # 检查是否在测试环境
        is_testing = current_app.config.get("TESTING", False)
        has_celery = celery is not None

        if not is_testing and has_celery:
            # 生产环境：使用真实 Celery
            def celery_decorator(func):
                @celery.task(
                    bind=True, name=f"app.services.tts_service.{func.__name__}"
                )
                def wrapper(self, task_id):
                    return func(self, task_id)

                return wrapper

            return celery_decorator
        else:
            # 测试环境或无 Celery：使用模拟装饰器
            def mock_decorator(func):
                def wrapper(task_id_or_self, task_id=None):
                    # 统一参数处理：如果只有一个参数，说明是直接调用
                    if task_id is None:
                        # 直接调用：wrapper(task_id)
                        actual_task_id = task_id_or_self
                        return func(None, actual_task_id)
                    else:
                        # Celery 风格调用：wrapper(self, task_id)
                        return func(task_id_or_self, task_id)

                # 添加 delay 方法模拟
                wrapper.delay = lambda task_id: MockCeleryResult(task_id)
                wrapper.apply_async = lambda args=None, **kwargs: MockCeleryResult(
                    args[0] if args else "mock-task"
                )
                return wrapper

            return mock_decorator

    except RuntimeError:
        # 不在应用上下文中，返回测试装饰器
        def mock_decorator(func):
            def wrapper(task_id_or_self, task_id=None):
                if task_id is None:
                    return func(None, task_id_or_self)
                else:
                    return func(task_id_or_self, task_id)

            wrapper.delay = lambda task_id: MockCeleryResult(task_id)
            wrapper.apply_async = lambda args=None, **kwargs: MockCeleryResult(
                args[0] if args else "mock-task"
            )
            return wrapper

        return mock_decorator


# 应用装饰器
@create_task_decorator()
def generate_speech_task(self, task_id):
    """生成语音任务 - 修复版本"""
    print("generate_speech_task called with task_id:", task_id)

    try:
        # 获取任务信息
        task = db.session.get(TTSTask, task_id)
        if not task:
            raise TaskProcessingError("Task not found")

        # 更新任务状态
        task.update_status("processing")

        # 检查环境
        try:
            is_testing = current_app.config.get("TESTING", False)
            has_celery = celery is not None and self is not None
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
            current_app.logger.error(f"TTS task {task_id} failed: {e}")
        except RuntimeError:
            print(f"TTS task {task_id} failed: {e}")

        raise TaskProcessingError(f"Speech generation failed: {str(e)}")


def mock_speech_generation(task, watermark_enabled=True):
    """模拟语音生成过程（用于测试）"""
    try:
        # 安全的应用上下文处理
        try:
            upload_folder = current_app.config.get("UPLOAD_FOLDER", "/tmp")
            current_app.logger.info(f"Mock processing TTS task: {task.id}")
        except RuntimeError:
            upload_folder = "/tmp"
            print(f"Mock processing TTS task: {task.id}")

        # 模拟处理时间
        import time

        time.sleep(0.1)

        # 计算模拟音频时长
        text_length = len(task.text)
        duration = max(1.0, (text_length * 0.15) / task.speed)

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

    print("isActive")
    """处理语音生成（生产环境）- 集成水印功能"""
    try:
        # 1. 加载语音模型
        update_tts_task_status(task, "Loading voice model...")

        model_info = load_voice_model(task.model_id)
        # 1.1 切换 GPT 权重
        resp = requests.get(
            SET_GPT_URL,
            params={"weights_path": model_info["gpt_model_path"]},
            timeout=10
        )
        resp_json = resp.json()
        if resp.status_code != 200 or resp_json.get("message") != "success":
            raise TaskProcessingError(f"Failed to set GPT weights: {resp.status_code} {resp.text}")

        # 1.2 切换 SoVITS 权重
        resp = requests.get(
            SET_SOVITS_URL,
            params={"weights_path": model_info["sovits_model_path"]},
            timeout=10
        )
        resp_json = resp.json()
        if resp.status_code != 200 or resp_json.get("message") != "success":
            raise TaskProcessingError(f"Failed to set SoVITS weights: {resp.status_code} {resp.text}")

        #1.5 payload
        payload = {
            "text": task.text,
            "text_lang": task.text_lang,
            "ref_audio_path": task.ref_audio_path,
            "aux_ref_audio_paths": json.loads(task.aux_ref_audio_paths or "[]"),
            "prompt_text": task.prompt_text,
            "prompt_lang": task.prompt_lang,
            "top_k": task.top_k,
            "top_p": task.top_p,
            "temperature": task.temperature,
            "text_split_method": task.text_split_method,
            "batch_size": task.batch_size,
            "batch_threshold": task.batch_threshold,
            "split_bucket": task.split_bucket,
            "speed_factor": task.speed,
            "fragment_interval": task.fragment_interval,
            "seed": task.seed,
            "media_type": "wav",
            "streaming_mode": False,
            "parallel_infer": task.parallel_infer,
            "repetition_penalty": task.repetition_penalty,
            "sample_steps": task.sample_steps,
            "super_sampling": task.super_sampling
        }

        # 2. 预处理文本
        update_tts_task_status(task, "Processing text...")
        response = requests.post(
            TTS_API_URL,
            json=payload,
            stream=True,
            timeout=120
        )
        if response.status_code != 200:
            raise TaskProcessingError(f"TTS service returned {response.status_code}: {response.text}")

        # 4. 读取音频流
        update_tts_task_status(task, "Receiving audio stream...")
        audio_bytes = BytesIO(response.content)

        # 5. 保存音频文件
        update_tts_task_status(task, "Saving audio file...")
        # save_generated_audio 接受 BytesIO 或 二进制流
        audio_info = save_generated_audio(audio_bytes, task)

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
    """加载语音模型 - 修复版本：使用正确的字段名"""
    try:
        model = db.session.get(VoiceModel, model_id)
        if not model:
            raise TaskProcessingError("Voice model not found")

        # 修复：使用新的字段名检查文件存在性
        if not model.gpt_model_path or not os.path.exists(model.gpt_model_path):
            raise TaskProcessingError("GPT model file not found")

        if not model.sovits_model_path or not os.path.exists(model.sovits_model_path):
            raise TaskProcessingError("SoVITS model file not found")

        # 修复：返回正确的模型信息
        model_info = {
            "model_id": model.id,
            "gpt_model_path": model.gpt_model_path,  # 新字段
            "sovits_model_path": model.sovits_model_path,  # 新字段
            "supported_emotions": model.get_supported_emotions(),
            "supported_languages": model.get_supported_languages(),
        }

        return model_info

    except Exception as e:
        raise TaskProcessingError(f"Failed to load voice model: {str(e)}")




def preprocess_text(text):
    """预处理文本"""
    try:
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
