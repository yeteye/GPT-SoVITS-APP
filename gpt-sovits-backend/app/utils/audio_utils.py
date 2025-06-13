# ./gpt-sovits-backend/app/utils/audio_utils.py
import os
import librosa
import soundfile as sf
import numpy as np
from pydub import AudioSegment
from flask import current_app
from app.utils.exceptions import AudioProcessingError


def validate_audio_content(file_path):
    """验证音频内容"""
    try:
        # 加载音频文件
        audio, sr = librosa.load(file_path, sr=None)

        # 检查音频时长
        duration = len(audio) / sr
        min_duration = current_app.config.get("AUDIO_MIN_DURATION", 3)
        max_duration = current_app.config.get("AUDIO_MAX_DURATION", 60)

        if duration < min_duration:
            raise AudioProcessingError(
                f"Audio too short. Minimum {min_duration} seconds required"
            )

        if duration > max_duration:
            raise AudioProcessingError(
                f"Audio too long. Maximum {max_duration} seconds allowed"
            )

        # 检查音频是否有内容（非静音）
        if np.max(np.abs(audio)) < 0.001:
            raise AudioProcessingError("Audio appears to be silent")

        # 检查采样率
        if sr < 8000:
            raise AudioProcessingError("Sample rate too low. Minimum 8kHz required")

        return {
            "duration": duration,
            "sample_rate": sr,
            "channels": 1 if len(audio.shape) == 1 else audio.shape[1],
            "is_valid": True,
        }

    except Exception as e:
        if isinstance(e, AudioProcessingError):
            raise e
        raise AudioProcessingError(f"Failed to validate audio: {str(e)}")


def convert_to_standard_format(input_path, output_path):
    """转换音频到标准格式"""
    try:
        target_sr = current_app.config.get("AUDIO_SAMPLE_RATE", 16000)

        # 加载音频
        audio, sr = librosa.load(input_path, sr=target_sr)

        # 确保单声道
        if len(audio.shape) > 1:
            audio = librosa.to_mono(audio)

        # 标准化音量
        audio = normalize_audio(audio)

        # 保存为WAV格式
        sf.write(output_path, audio, target_sr, format="WAV", subtype="PCM_16")

        return output_path

    except Exception as e:
        raise AudioProcessingError(f"Failed to convert audio: {str(e)}")


def normalize_audio(audio, target_db=-20):
    """标准化音频音量"""
    # 计算RMS
    rms = np.sqrt(np.mean(audio**2))

    if rms > 0:
        # 转换目标分贝到线性比例
        target_rms = 10 ** (target_db / 20)
        # 缩放音频
        audio = audio * (target_rms / rms)

    # 防止削波
    max_val = np.max(np.abs(audio))
    if max_val > 1.0:
        audio = audio / max_val

    return audio


def trim_silence(audio, sr, top_db=20):
    """移除音频首尾的静音部分"""
    try:
        # 使用librosa的trim函数
        trimmed_audio, _ = librosa.effects.trim(audio, top_db=top_db)
        return trimmed_audio
    except Exception:
        # 如果trim失败，返回原音频
        return audio


def extract_audio_features(file_path):
    """提取音频特征"""
    try:
        audio, sr = librosa.load(file_path, sr=16000)

        # 基本特征
        duration = len(audio) / sr
        zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(audio))

        # 频谱特征
        spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sr)
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)

        # MFCC特征
        mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)

        # 音高特征
        pitches, magnitudes = librosa.core.piptrack(y=audio, sr=sr)

        return {
            "duration": duration,
            "sample_rate": sr,
            "zero_crossing_rate": float(zero_crossing_rate),
            "spectral_centroid_mean": float(np.mean(spectral_centroids)),
            "spectral_rolloff_mean": float(np.mean(spectral_rolloff)),
            "mfcc_mean": [float(np.mean(mfcc)) for mfcc in mfccs],
            "pitch_mean": (
                float(np.mean(pitches[pitches > 0])) if np.any(pitches > 0) else 0.0
            ),
        }

    except Exception as e:
        raise AudioProcessingError(f"Failed to extract audio features: {str(e)}")


def split_audio_by_silence(file_path, min_segment_length=2.0, silence_thresh=-40):
    """根据静音分割音频"""
    try:
        # 使用pydub加载音频
        audio = AudioSegment.from_file(file_path)

        # 检测静音段
        chunks = []
        current_chunk = AudioSegment.empty()

        for i, chunk in enumerate(audio[::100]):  # 每100ms检查一次
            if chunk.dBFS < silence_thresh:
                # 静音段
                if len(current_chunk) >= min_segment_length * 1000:  # 转换为毫秒
                    chunks.append(current_chunk)
                current_chunk = AudioSegment.empty()
            else:
                # 非静音段
                current_chunk += audio[i * 100 : (i + 1) * 100]

        # 添加最后一个片段
        if len(current_chunk) >= min_segment_length * 1000:
            chunks.append(current_chunk)

        return chunks

    except Exception as e:
        raise AudioProcessingError(f"Failed to split audio: {str(e)}")


def merge_audio_files(file_paths, output_path):
    """合并多个音频文件"""
    try:
        combined = AudioSegment.empty()

        for file_path in file_paths:
            audio = AudioSegment.from_file(file_path)
            combined += audio

        # 导出合并后的音频
        combined.export(output_path, format="wav")
        return output_path

    except Exception as e:
        raise AudioProcessingError(f"Failed to merge audio files: {str(e)}")


def calculate_audio_hash(file_path):
    """计算音频内容的哈希值"""
    try:
        audio, sr = librosa.load(file_path, sr=16000)

        # 提取音频指纹特征
        chroma = librosa.feature.chroma_stft(y=audio, sr=sr)

        # 计算哈希
        import hashlib

        audio_str = str(chroma.flatten())
        return hashlib.sha256(audio_str.encode()).hexdigest()

    except Exception as e:
        raise AudioProcessingError(f"Failed to calculate audio hash: {str(e)}")


def get_audio_info(file_path):
    """获取音频文件信息"""
    try:
        # 使用pydub获取基本信息
        audio = AudioSegment.from_file(file_path)

        # 使用librosa获取详细信息
        y, sr = librosa.load(file_path, sr=None)

        return {
            "duration": len(audio) / 1000.0,  # 秒
            "sample_rate": sr,
            "channels": audio.channels,
            "frame_rate": audio.frame_rate,
            "sample_width": audio.sample_width,
            "max_possible_amplitude": audio.max_possible_amplitude,
            "dBFS": audio.dBFS,
            "file_size": os.path.getsize(file_path),
        }

    except Exception as e:
        raise AudioProcessingError(f"Failed to get audio info: {str(e)}")


def detect_voice_activity(file_path, frame_length=2048, hop_length=512):
    """检测语音活动"""
    try:
        audio, sr = librosa.load(file_path, sr=16000)

        # 计算能量
        energy = librosa.feature.rms(
            y=audio, frame_length=frame_length, hop_length=hop_length
        )[0]

        # 计算过零率
        zcr = librosa.feature.zero_crossing_rate(
            audio, frame_length=frame_length, hop_length=hop_length
        )[0]

        # 简单的VAD算法
        energy_threshold = np.mean(energy) * 0.5
        zcr_threshold = np.mean(zcr) * 1.5

        # 语音活动检测
        voice_frames = (energy > energy_threshold) & (zcr < zcr_threshold)

        # 计算语音比例
        voice_ratio = np.sum(voice_frames) / len(voice_frames)

        return {
            "voice_ratio": float(voice_ratio),
            "has_voice": voice_ratio > 0.3,  # 30%以上为有效语音
            "voice_frames": voice_frames.tolist(),
        }

    except Exception as e:
        raise AudioProcessingError(f"Failed to detect voice activity: {str(e)}")
