import numpy as np
import wave
import struct
import matplotlib.pyplot as plt
from scipy.fft import fft, ifft


def str_to_bin(s):
    return ''.join(format(ord(c), '08b') for c in s)


def bin_to_str(b):
    chars = [chr(int(b[i:i + 8], 2)) for i in range(0, len(b), 8)]
    return ''.join(chars)


def embed_watermark_fft(input_wav, output_wav, watermark: str, start_freq=2000, delta=10):
    # 读取 wav 文件
    with wave.open(input_wav, 'rb') as wav:
        params = wav.getparams()
        n_frames = wav.getnframes()
        framerate = wav.getframerate()
        audio = np.frombuffer(wav.readframes(n_frames), dtype=np.int16)

    # 转换为频域
    spectrum = fft(audio)

    # 将水印转换为二进制
    watermark_bin = str_to_bin(watermark)
    print(f"Embedding watermark bits: {watermark_bin}")

    # 每个位对应频域中的一个频率点偏移
    for i, bit in enumerate(watermark_bin):
        freq_index = start_freq + i * delta
        if freq_index >= len(spectrum) // 2:
            break
        mag = abs(spectrum[freq_index])
        phase = np.angle(spectrum[freq_index])
        if bit == '1':
            mag *= 1.1  # 增强该频率幅值
        else:
            mag *= 0.9  # 减弱该频率幅值
        spectrum[freq_index] = mag * np.exp(1j * phase)
        spectrum[-freq_index] = np.conj(spectrum[freq_index])  # 保持对称性（实信号）

    # 逆 FFT
    watermarked_audio = np.real(ifft(spectrum)).astype(np.int16)

    # 写入新音频
    with wave.open(output_wav, 'wb') as out_wav:
        out_wav.setparams(params)
        out_wav.writeframes(watermarked_audio.tobytes())


def extract_watermark_fft(watermarked_wav, watermark_length, start_freq=2000, delta=10):
    with wave.open(watermarked_wav, 'rb') as wav:
        n_frames = wav.getnframes()
        audio = np.frombuffer(wav.readframes(n_frames), dtype=np.int16)

    spectrum = fft(audio)
    bits = ''
    for i in range(watermark_length * 8):
        freq_index = start_freq + i * delta
        mag = abs(spectrum[freq_index])
        # 设定门限以判断是 0 还是 1
        bits += '1' if mag > 100 else '0'
    print(f"Extracted bits: {bits}")
    return bin_to_str(bits)


# 示例用法
if __name__ == '__main__':
    embed_watermark_fft('response.wav', 'watermarkedResponse.wav', '789409db4586bc75c7835fb749d3908626673612ec0d6ce27d47aaad23dd3706')
    recovered = extract_watermark_fft('watermarkedResponse.wav', watermark_length=64)
    print(f"Recovered watermark: {recovered}")
