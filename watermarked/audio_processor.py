import os
import wave
import numpy as np
from scipy.fft import fft, ifft
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import logging

from watermark_database import WatermarkDatabase

logger = logging.getLogger(__name__)


@dataclass
class WatermarkConfig:
    start_freq: int = 800
    delta: int = 15
    strength_factor: float = 1.0
    boost_factor: float = 0.1
    use_error_correction: bool = True
    # 增加高级策略参数
    split_strategy: str = 'fixed_ratio'  # 可选: 'fixed_ratio', 'quartile', 'kmeans_like', 'adaptive_enhanced'
    freq_selection: str = 'linear'     # 可选: 'linear', 'prime', 'fibonacci'


class AudioWatermarkProcessor:
    """音频水印处理器，依赖 WatermarkDatabase 存取"""
    def __init__(self, db_config: Dict = None):
        # db_config: 传给 WatermarkDatabase，用于连接 MySQL 等
        self.config = WatermarkConfig()
        self.db = WatermarkDatabase(db_config)

    def str_to_bin(self, s: str) -> str:
        return ''.join(format(ord(c), '08b') for c in s)

    def bin_to_str(self, b: str) -> Optional[str]:
        try:
            if len(b) % 8 != 0:
                b = b[:-(len(b) % 8)]
            chars = []
            for i in range(0, len(b), 8):
                byte = b[i:i + 8]
                if len(byte) == 8:
                    char_code = int(byte, 2)
                    if 32 <= char_code <= 126:
                        chars.append(chr(char_code))
                    else:
                        chars.append('?')
            return ''.join(chars)
        except Exception as e:
            logger.error(f"bin_to_str 解码异常: {e}")
            return None

    def add_error_correction(self, data: str) -> str:
        # 重复5次纠错编码
        return ''.join(bit * 5 for bit in data)

    def decode_error_correction(self, data: str) -> str:
        if len(data) % 5 != 0:
            return data
        decoded = ''
        for i in range(0, len(data), 5):
            quintuple = data[i:i + 5]
            ones = quintuple.count('1')
            decoded += '1' if ones >= 3 else '0'
        return decoded

    def get_frequency_indices(
        self,
        start_freq: int,
        delta: int,
        num_bits: int,
        freq_selection: str
    ) -> List[int]:
        indices = []
        if freq_selection == 'linear':
            indices = [start_freq + i * delta for i in range(num_bits)]
        elif freq_selection == 'prime':
            primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29,
                      31, 37, 41, 43, 47, 53, 59, 61, 67, 71]
            for i in range(num_bits):
                prime_offset = primes[i % len(primes)]
                indices.append(start_freq + i * delta + prime_offset)
        elif freq_selection == 'fibonacci':
            fib = [1, 1]
            while len(fib) < num_bits:
                fib.append(fib[-1] + fib[-2])
            for i in range(num_bits):
                fib_offset = fib[i] % 50
                indices.append(start_freq + i * delta + fib_offset)
        else:
            # 默认线性
            indices = [start_freq + i * delta for i in range(num_bits)]
        return indices

    def embed_watermark(
        self,
        input_path: str,
        output_path: str,
        username: str,
        model_id: str ,
        code_length: int = 16,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        嵌入水印，返回 dict，包含 success、watermark_code 等信息。
        input_path: 原始 WAV 路径（应为 PCM WAV，带 RIFF 头）。
        output_path: 输出带水印的 WAV 路径。
        username, code_length, description: 存库信息。
        """
        try:
            # 记录文件信息并生成水印码
            file_size = os.path.getsize(input_path)
            file_info = f"size: {file_size} bytes"
            user_id = self.db.get_id_by_username(username)
            watermark_code = self.db.add_watermark(
                username, user_id, model_id, code_length, description, file_info
            )

            # 读取音频 PCM 数据
            with wave.open(input_path, 'rb') as wav:
                params = wav.getparams()
                n_frames = wav.getnframes()
                audio = np.frombuffer(wav.readframes(n_frames), dtype=np.int16)
                if wav.getnchannels() == 2:
                    audio = audio[::2]

            # 频域转换
            spectrum = fft(audio.astype(np.float64))

            # 准备水印 bits
            watermark_bin = self.str_to_bin(watermark_code)
            if self.config.use_error_correction:
                watermark_bin = self.add_error_correction(watermark_bin)

            # 计算频率索引
            freq_indices = self.get_frequency_indices(
                self.config.start_freq,
                self.config.delta,
                len(watermark_bin),
                self.config.freq_selection
            )
            max_freq_idx = max(freq_indices) if freq_indices else 0
            max_allowed = len(spectrum) // 2 - 100
            if max_freq_idx > max_allowed and len(watermark_bin) > 0:
                available = max_allowed - self.config.start_freq
                new_delta = max(20, available // len(watermark_bin))
                logger.info(f"频率索引超出，调整 delta: {self.config.delta} -> {new_delta}")
                self.config.delta = new_delta
                freq_indices = self.get_frequency_indices(
                    self.config.start_freq,
                    self.config.delta,
                    len(watermark_bin),
                    self.config.freq_selection
                )

            # 嵌入循环
            embedding_info = []
            for bit, freq_index in zip(watermark_bin, freq_indices):
                if freq_index >= len(spectrum):
                    break
                orig = spectrum[freq_index]
                orig_mag = abs(orig)
                phase = np.angle(orig)
                if bit == '1':
                    new_mag = orig_mag * (1 + self.config.strength_factor)
                    new_mag += orig_mag * self.config.boost_factor + 1200
                else:
                    new_mag = orig_mag * (1 - self.config.strength_factor)
                    new_mag *= (1 - self.config.boost_factor)
                    new_mag = max(new_mag, orig_mag * 0.008, 8)
                embedding_info.append({
                    'bit': bit,
                    'freq_index': freq_index,
                    'ratio': new_mag / (orig_mag + 1e-6)
                })
                spectrum[freq_index] = new_mag * np.exp(1j * phase)
                # 保持对称
                if freq_index < len(spectrum) - freq_index:
                    spectrum[-freq_index] = np.conj(spectrum[freq_index])

            # 逆 FFT 回时域
            watermarked_audio = np.real(ifft(spectrum))
            max_val = np.max(np.abs(watermarked_audio))
            if max_val > 32767:
                watermarked_audio = watermarked_audio * (29000 / max_val)
            watermarked_audio = watermarked_audio.astype(np.int16)

            # 如果原为双声道，复制通道
            with wave.open(input_path, 'rb') as wav:
                params = wav.getparams()
            if params.nchannels == 2:
                stereo = np.zeros(len(watermarked_audio) * 2, dtype=np.int16)
                stereo[::2] = watermarked_audio
                stereo[1::2] = watermarked_audio
                watermarked_audio = stereo

            # 写入输出 WAV
            with wave.open(output_path, 'wb') as out_wav:
                out_wav.setparams(params)
                out_wav.writeframes(watermarked_audio.tobytes())

            # 记录 embedding ratio 差异，供调参参考
            ratios_1 = [info['ratio'] for info in embedding_info if info['bit'] == '1']
            ratios_0 = [info['ratio'] for info in embedding_info if info['bit'] == '0']
            ratio_diff = float(np.mean(ratios_1) - np.mean(ratios_0)) if ratios_1 and ratios_0 else 0.0
            logger.info(f"嵌入 ratio_diff: {ratio_diff:.3f}")

            return {
                'success': True,
                'watermark_code': watermark_code,
                'code_length': code_length,
                'username': username,
                'embedded_bits': len(watermark_bin),
                'frequency_range': f"{min(freq_indices)} - {max(freq_indices)}" if freq_indices else "",
                'description': description,
                'embedding_ratio_diff': ratio_diff
            }
        except Exception as e:
            logger.error(f"嵌入水印失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def extract_watermark(
        self,
        audio_path: str,
        filename: str = "",
        ip_address: str = "",
        user_agent: str = ""
    ) -> Dict[str, Any]:
        """
        提取并验证水印。尝试多种长度，返回最佳结果或失败信息。
        """
        try:
            with wave.open(audio_path, 'rb') as wav:
                audio = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16)
                if wav.getnchannels() == 2:
                    audio = audio[::2]

            possible_lengths = [32]
            best_result = None
            best_accuracy = 0.0
            for test_length in possible_lengths:
                res = self._extract_watermark_length(audio, test_length)
                if res and res.get('accuracy', 0) > best_accuracy:
                    best_accuracy = res['accuracy']
                    best_result = res

            logger.info(f"提取最佳结果: {best_result}, accuracy={best_accuracy:.3f}")

            if best_result and best_accuracy > 0.95:
                print(best_result, best_accuracy)
                user_info = self.db.get_user_by_watermark(best_result['watermark_code'])
                if user_info:
                    # 更新使用记录并记录日志
                    self.db.update_usage(best_result['watermark_code'])
                    self.db.log_verification(
                        best_result['watermark_code'],
                        filename,
                        best_result['accuracy'],
                        best_result['extracted_raw'],
                        True,
                        ip_address,
                        user_agent
                    )
                    return {
                        'success': True,
                        'verification': 'verified',
                        'username': user_info['username'],
                        'watermark_code': best_result['watermark_code'],
                        'code_length': best_result['code_length'],
                        'accuracy': best_result['accuracy'],
                        'confidence': best_result.get('confidence'),
                        'created_at': user_info.get('created_at'),
                        'usage_count': user_info.get('usage_count', 0) + 1,
                        'description': user_info.get('description')
                    }
                else:
                    # 未在数据库中找到，但检测到水印
                    self.db.log_verification(
                        best_result['watermark_code'],
                        filename,
                        best_result['accuracy'],
                        best_result['extracted_raw'],
                        False,
                        ip_address,
                        user_agent
                    )
                    return {
                        'success': True,
                        'verification': 'watermark_found_but_not_registered',
                        'extracted_code': best_result['watermark_code'],
                        'accuracy': best_result['accuracy'],
                        'message': '检测到水印但未在数据库中找到对应用户'
                    }
            else:
                if best_result:
                    fuzzy_match = self.db.find_closest_watermark(best_result['watermark_code'])
                    if fuzzy_match:
                        self.db.log_verification(
                            fuzzy_match['code'], filename, best_result['accuracy'],
                            best_result['extracted_raw'], True, ip_address, user_agent
                        )
                        return {
                            'success': True,
                            'verification': 'fuzzy_matched',
                            'matched_code': fuzzy_match['code'],
                            'match_score': fuzzy_match['match_score'],
                            'username': fuzzy_match['username'],
                            'description': fuzzy_match.get('description', ''),
                            'created_at': fuzzy_match.get('created_at'),
                            'usage_count': fuzzy_match.get('usage_count', 0) + 1,
                            'extracted_code': best_result['watermark_code'],
                            'accuracy': best_result['accuracy'],
                            'confidence': best_result.get('confidence')
                        }
        except Exception as e:
            logger.error(f"提取水印失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def _extract_watermark_length(
        self,
        audio: np.ndarray,
        code_length: int
    ) -> Optional[Dict[str, Any]]:
        """
        提取指定长度的水印码。返回 dict 包括 watermark_code, extracted_raw, accuracy, confidence, code_length。
        """
        try:
            spectrum = fft(audio.astype(np.float64))
            spectrum_mag = np.abs(spectrum[:len(spectrum)//2])

            expected_bits = code_length * 8
            if self.config.use_error_correction:
                expected_bits *= 5

            freq_indices = self.get_frequency_indices(
                self.config.start_freq,
                self.config.delta,
                expected_bits,
                self.config.freq_selection
            )
            watermark_mags = []
            for idx in freq_indices:
                if idx < len(spectrum_mag):
                    watermark_mags.append(spectrum_mag[idx])
            # 若能用的频率点过少，跳过
            if len(watermark_mags) < expected_bits * 0.9:
                return None

            mag_with_idx = [(mag, i) for i, mag in enumerate(watermark_mags)]
            mag_with_idx.sort(key=lambda x: x[0], reverse=True)
            total = len(watermark_mags)

            # 选择分割策略
            if self.config.split_strategy == 'fixed_ratio':
                split_pt = total // 2
            elif self.config.split_strategy == 'quartile':
                sorted_mags = [x[0] for x in mag_with_idx]
                q75 = np.percentile(sorted_mags, 75)
                q25 = np.percentile(sorted_mags, 25)
                threshold = (q75 + q25) / 2
                above = sum(1 for m in sorted_mags if m > threshold)
                split_pt = above
            elif self.config.split_strategy == 'kmeans_like':
                sorted_vals = [x[0] for x in mag_with_idx]
                best_var = float('inf')
                split_pt = total // 2
                for t in range(total // 5, 4 * total // 5):
                    g1 = sorted_vals[:t]
                    g2 = sorted_vals[t:]
                    if g1 and g2:
                        var = np.var(g1) + np.var(g2)
                        if var < best_var:
                            best_var = var
                            split_pt = t
            else:  # adaptive_enhanced
                sorted_vals = [x[0] for x in mag_with_idx]
                best_sep = 0.0
                split_pt = total // 2
                for ratio in np.arange(0.2, 0.8, 0.05):
                    t = int(total * ratio)
                    if t < 5 or t > total - 5:
                        continue
                    high = sorted_vals[:t]
                    low = sorted_vals[t:]
                    if len(high) > 2 and len(low) > 2:
                        sep = (np.mean(high) - np.mean(low)) / (np.std(high) + np.std(low) + 0.1 * np.mean(high))
                        if sep > best_sep:
                            best_sep = sep
                            split_pt = t

            high_set = set(idx for _, idx in mag_with_idx[:split_pt])
            bits = ''
            confidences = []
            for i in range(min(expected_bits, len(watermark_mags))):
                bit = '1' if i in high_set else '0'
                # rank: 找到 i 在排序列表中的位置，用于 confidence
                rank = next(j for j, (_, idx) in enumerate(mag_with_idx) if idx == i)
                confidence = abs(rank - split_pt) / total
                bits += bit
                confidences.append(confidence)

            if self.config.use_error_correction:
                bits = self.decode_error_correction(bits)
            watermark_str = self.bin_to_str(bits)
            avg_conf = float(np.mean(confidences)) if confidences else 0.0

            if watermark_str and len(watermark_str) >= code_length:
                extracted_code = watermark_str[:code_length]
                # 简单准确度评估
                if code_length == 8 and extracted_code.isdigit():
                    accuracy = 0.9
                elif code_length == 16 and all(c.isalnum() for c in extracted_code):
                    accuracy = 0.85
                elif code_length == 32 and all(c in '0123456789abcdef' for c in extracted_code.lower()):
                    accuracy = 0.8
                else:
                    accuracy = 0.7
                return {
                    'watermark_code': extracted_code,
                    'extracted_raw': watermark_str,
                    'accuracy': accuracy,
                    'confidence': avg_conf,
                    'code_length': code_length
                }
            return None
        except Exception as e:
            logger.error(f"_extract_watermark_length 异常: {e}", exc_info=True)
            return None


if __name__ == "__main__":
    """
    示例：如何使用及配置
    运行前请确保当前目录有一个测试 WAV 文件（如 input.wav），并且 WatermarkDatabase 可正常连接。
    """
    logging.basicConfig(level=logging.INFO)
    # 假设 db_config 是一个字典，包括 MySQL 连接信息等
    db_config = {
        'host': 'localhost',
        'user': 'your_user',
        'password': 'your_password',
        'database': 'watermark_db',
        # 其他可能需要的项
    }
    processor = AudioWatermarkProcessor(db_config=db_config)

    # 配置示例：freq=800, delta=15, strength=1.00, boost=0.10, correction=True, split=fixed_ratio, freq_sel=linear
    processor.config = WatermarkConfig(
        start_freq=800,
        delta=15,
        strength_factor=1.0,
        boost_factor=0.10,
        use_error_correction=True,
        split_strategy='fixed_ratio',
        freq_selection='linear'
    )

    # 打印当前配置
    logger.info(
        f"当前水印配置: start_freq={processor.config.start_freq}, "
        f"delta={processor.config.delta}, strength={processor.config.strength_factor}, "
        f"boost={processor.config.boost_factor}, correction={processor.config.use_error_correction}, "
        f"split={processor.config.split_strategy}, freq_sel={processor.config.freq_selection}"
    )

    # 输入/输出文件示例
    input_wav = "input.wav"       # 请替换为你测试的文件路径
    output_wav = "watermarked.wav"

    username = "testuser"
    code_length = 16
    description = "测试水印嵌入"

    # 嵌入水印
    result = processor.embed_watermark(input_wav, output_wav, username, code_length, description)
    if result.get('success'):
        logger.info(f"嵌入成功: {result}")
        # 嵌入成功后，可播放 output_wav，或直接做提取测试
        # 提取测试
        verify = processor.extract_watermark(output_wav, filename=output_wav, ip_address="127.0.0.1", user_agent="test-agent")
        logger.info(f"提取结果: {verify}")
    else:
        logger.error(f"嵌入失败: {result.get('error')}")

    # 注意：运行完后可删除 watermarked.wav，以免占用空间
