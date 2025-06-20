import numpy as np
import wave
from scipy.fft import fft

def bin_to_str(b):
    """将二进制字符串转为普通字符串"""
    chars = [chr(int(b[i:i + 8], 2)) for i in range(0, len(b), 8)]
    return ''.join(chars)

def extract_watermark_fft(wav_path, watermark_length, start_freq_index=2000, delta=10, threshold_factor=0.05):
    """
    从 wav 文件中提取音频水印

    参数：
    - wav_path: str，音频文件路径
    - watermark_length: int，水印字符串长度（字符数）
    - start_freq_index: int，起始频率索引（不是 Hz，是 FFT 索引）
    - delta: int，相邻 bit 的频率间隔（频谱索引）
    - threshold_factor: float，用于判定 0/1 的动态阈值因子
    """
    # 打开 wav 文件
    with wave.open(wav_path, 'rb') as wav:
        framerate = wav.getframerate()
        n_frames = wav.getnframes()
        audio = np.frombuffer(wav.readframes(n_frames), dtype=np.int16)

    # 做 FFT 得到频谱
    spectrum = fft(audio)
    spectrum_mag = np.abs(spectrum[:len(spectrum)//2])  # 只取正频率部分

    # 使用平均幅值作为动态门限基础
    avg_mag = np.mean(spectrum_mag)
    threshold = avg_mag * (1 + threshold_factor)

    # 提取二进制水印
    bits = ''
    for i in range(watermark_length * 8):
        index = start_freq_index + i * delta
        if index >= len(spectrum_mag):
            print("⚠️ 超出频域范围，停止提取")
            break
        mag = spectrum_mag[index]
        bit = '1' if mag > threshold else '0'
        bits += bit

    print(f"🧬 提取到的二进制串: {bits}")

    # 尝试转换为字符串
    try:
        watermark_str = bin_to_str(bits)
        print(f"✅ 识别出的水印字符串: {watermark_str}")
        return watermark_str
    except Exception as e:
        print("❌ 二进制转字符串失败，可能数据损坏")
        return None

# 示例用法
if __name__ == '__main__':
    # 提取 64 个字符（512 bits）水印，起始频域索引 2000，间隔 10
    extract_watermark_fft(
        wav_path='watermarkedResponse.wav',
        watermark_length=64,  # 字符数
        start_freq_index=2000,
        delta=10,
        threshold_factor=0.2
    )
