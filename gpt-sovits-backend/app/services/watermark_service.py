# ./gpt-sovits-backend/app/services/watermark_service.py
import os
import wave
import struct
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import logging
from flask import current_app
from datetime import datetime

from app.extensions import db
from app.models.watermark import Watermark, WatermarkVerificationLog
from app.utils.exceptions import AudioProcessingError, ValidationError
from app.utils.helpers import generate_unique_filename

# 科学计算库检查
try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from scipy.fft import fft, ifft

    SCIPY_AVAILABLE = True
except ImportError:
    try:
        from numpy.fft import fft, ifft

        SCIPY_AVAILABLE = True
    except ImportError:
        SCIPY_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class WatermarkConfig:
    """水印配置"""

    start_freq: int = 1000
    delta: int = 30
    strength_factor: float = 2.0
    boost_factor: float = 0.3
    use_error_correction: bool = True
    split_strategy: str = "quartile"  # 可选: 'fixed_ratio', 'quartile', 'adaptive'
    freq_selection: str = "prime"  # 可选: 'linear', 'prime', 'fibonacci'


class WatermarkService:
    """音频水印服务 - 兼容版本"""

    def __init__(self):
        self.config = WatermarkConfig()
        self._load_config()
        self._check_dependencies()

    def _load_config(self):
        """从Flask配置加载水印参数"""
        try:
            self.config.start_freq = current_app.config.get(
                "WATERMARK_START_FREQ", 1000
            )
            self.config.delta = current_app.config.get("WATERMARK_DELTA", 30)
            self.config.strength_factor = current_app.config.get(
                "WATERMARK_STRENGTH", 2.0
            )
            self.config.boost_factor = current_app.config.get("WATERMARK_BOOST", 0.3)
            self.config.use_error_correction = current_app.config.get(
                "WATERMARK_ERROR_CORRECTION", True
            )
        except RuntimeError:
            # 不在应用上下文中，使用默认值
            logger.warning("Not in application context, using default watermark config")

    def _check_dependencies(self):
        """检查必需的依赖库"""
        self.dependencies_available = True
        self.missing_deps = []

        try:
            import numpy as np

            self.np = np
        except ImportError:
            self.dependencies_available = False
            self.missing_deps.append("numpy")

        try:
            from scipy.fft import fft, ifft

            self.fft = fft
            self.ifft = ifft
        except ImportError:
            try:
                import numpy.fft as npfft

                self.fft = npfft.fft
                self.ifft = npfft.ifft
            except ImportError:
                self.dependencies_available = False
                self.missing_deps.append("scipy or numpy.fft")

        try:
            import wave

            self.wave = wave
        except ImportError:
            self.dependencies_available = False
            self.missing_deps.append("wave")

    def str_to_bin(self, s: str) -> str:
        """字符串转二进制"""
        return "".join(format(ord(c), "08b") for c in s)

    def bin_to_str(self, b: str) -> Optional[str]:
        """二进制转字符串"""
        try:
            if len(b) % 8 != 0:
                b = b[: -(len(b) % 8)]
            chars = []
            for i in range(0, len(b), 8):
                byte = b[i : i + 8]
                if len(byte) == 8:
                    char_code = int(byte, 2)
                    if 32 <= char_code <= 126:
                        chars.append(chr(char_code))
                    else:
                        chars.append("?")
            return "".join(chars)
        except Exception as e:
            logger.error(f"bin_to_str 解码异常: {e}")
            return None

    def add_error_correction(self, data: str) -> str:
        """添加5重复纠错编码"""
        return "".join(bit * 5 for bit in data)

    def decode_error_correction(self, data: str) -> str:
        """解码5重复纠错"""
        if len(data) % 5 != 0:
            return data
        decoded = ""
        for i in range(0, len(data), 5):
            quintuple = data[i : i + 5]
            ones = quintuple.count("1")
            decoded += "1" if ones >= 3 else "0"
        return decoded

    def get_frequency_indices(
        self, start_freq: int, delta: int, num_bits: int
    ) -> List[int]:
        """生成频率索引"""
        indices = []

        if self.config.freq_selection == "linear":
            indices = [start_freq + i * delta for i in range(num_bits)]
        elif self.config.freq_selection == "prime":
            primes = [
                2,
                3,
                5,
                7,
                11,
                13,
                17,
                19,
                23,
                29,
                31,
                37,
                41,
                43,
                47,
                53,
                59,
                61,
                67,
                71,
            ]
            for i in range(num_bits):
                prime_offset = primes[i % len(primes)]
                indices.append(start_freq + i * delta + prime_offset)
        elif self.config.freq_selection == "fibonacci":
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

    def get_or_create_user_watermark(
        self, user_id: str, username: str, model_id: str = None
    ) -> str:
        """获取或创建用户水印"""
        try:
            # 查找现有水印
            watermark = Watermark.query.filter_by(
                user_id=user_id, model_id=model_id, is_active=True
            ).first()

            if watermark:
                return watermark.watermark_code

            # 创建新水印
            watermark = Watermark.create_for_user(
                user_id=user_id,
                username=username,
                model_id=model_id,
                code_length=16,
                description=(
                    f"Auto-generated for model {model_id}"
                    if model_id
                    else "Auto-generated for user"
                ),
            )

            logger.info(
                f"Created new watermark {watermark.watermark_code} for user {username}"
            )
            return watermark.watermark_code

        except Exception as e:
            logger.error(f"Failed to get/create watermark for user {user_id}: {e}")
            raise AudioProcessingError(f"Failed to create watermark: {str(e)}")

    def embed_watermark_to_audio(
        self, original_path, watermark_code, user_id, output_dir=None
    ):
        """为音频文件嵌入水印 - 修复：添加依赖检查"""
        if not self.dependencies_available:
            raise AudioProcessingError(
                f"Missing required dependencies: {', '.join(self.missing_deps)}. "
                "Please install scipy and numpy for watermark functionality."
            )

        try:
            if not os.path.exists(original_path):
                raise AudioProcessingError("Original audio file not found")

            # 生成输出路径
            if output_dir is None:
                output_dir = os.path.dirname(original_path)

            filename = os.path.basename(original_path)
            name, ext = os.path.splitext(filename)
            output_filename = f"{name}_watermarked{ext}"
            output_path = os.path.join(output_dir, output_filename)

            # 读取音频 - 改进错误处理
            try:
                with self.wave.open(original_path, "rb") as wav:
                    params = wav.getparams()
                    n_frames = wav.getnframes()
                    audio = self.np.frombuffer(
                        wav.readframes(n_frames), dtype=self.np.int16
                    )
                    if wav.getnchannels() == 2:
                        audio = audio[::2]  # 转为单声道
            except Exception as e:
                raise AudioProcessingError(f"Failed to read audio file: {str(e)}")

            # 转换为频域
            spectrum = self.fft(audio.astype(self.np.float64))

            # 准备水印数据
            watermark_bin = self.str_to_bin(watermark_code)
            if self.config.use_error_correction:
                watermark_bin = self.add_error_correction(watermark_bin)

            # 获取频率索引
            freq_indices = self.get_frequency_indices(
                self.config.start_freq, self.config.delta, len(watermark_bin)
            )

            # 检查频率范围并自动调整
            max_freq_idx = max(freq_indices) if freq_indices else 0
            max_allowed = len(spectrum) // 2 - 100

            if max_freq_idx > max_allowed and len(watermark_bin) > 0:
                available = max_allowed - self.config.start_freq
                new_delta = max(20, available // len(watermark_bin))
                logger.info(
                    f"Adjusting frequency delta: {self.config.delta} -> {new_delta}"
                )
                self.config.delta = new_delta
                freq_indices = self.get_frequency_indices(
                    self.config.start_freq, self.config.delta, len(watermark_bin)
                )

            # 嵌入水印
            embedding_info = []
            for bit, freq_index in zip(watermark_bin, freq_indices):
                if freq_index >= len(spectrum):
                    break

                original_complex = spectrum[freq_index]
                original_mag = abs(original_complex)
                phase = self.np.angle(original_complex)

                if bit == "1":
                    new_mag = original_mag * (1 + self.config.strength_factor)
                    new_mag += original_mag * self.config.boost_factor + 1200
                else:
                    new_mag = original_mag * (1 - self.config.strength_factor)
                    new_mag *= 1 - self.config.boost_factor
                    new_mag = max(new_mag, original_mag * 0.008, 8)

                embedding_info.append(
                    {
                        "bit": bit,
                        "freq_index": freq_index,
                        "ratio": new_mag / (original_mag + 1e-6),
                    }
                )

                spectrum[freq_index] = new_mag * self.np.exp(1j * phase)

                # 保持频谱对称性
                if freq_index < len(spectrum) - freq_index:
                    spectrum[-freq_index] = self.np.conj(spectrum[freq_index])

            # 逆FFT回时域
            watermarked_audio = self.np.real(self.ifft(spectrum))

            # 归一化防止削波
            max_val = self.np.max(self.np.abs(watermarked_audio))
            if max_val > 32767:
                watermarked_audio = watermarked_audio * (29000 / max_val)

            watermarked_audio = watermarked_audio.astype(self.np.int16)

            # 如果原音频是双声道，复制到两个声道
            if params.nchannels == 2:
                stereo_audio = self.np.zeros(
                    len(watermarked_audio) * 2, dtype=self.np.int16
                )
                stereo_audio[::2] = watermarked_audio
                stereo_audio[1::2] = watermarked_audio
                watermarked_audio = stereo_audio

            # 保存带水印的音频
            try:
                with self.wave.open(output_path, "wb") as out_wav:
                    out_wav.setparams(params)
                    out_wav.writeframes(watermarked_audio.tobytes())
            except Exception as e:
                raise AudioProcessingError(
                    f"Failed to save watermarked audio: {str(e)}"
                )

            # 更新水印使用统计
            watermark = Watermark.query.filter_by(watermark_code=watermark_code).first()
            if watermark:
                watermark.increment_usage()
                file_info = {
                    "original_file": original_path,
                    "watermarked_file": output_path,
                    "embedded_bits": len(watermark_bin),
                    "frequency_range": (
                        f"{min(freq_indices)}-{max(freq_indices)}"
                        if freq_indices
                        else ""
                    ),
                    "embedding_time": datetime.now().isoformat(),
                }
                watermark.set_file_info(file_info)
                db.session.commit()

            logger.info(
                f"Successfully embedded watermark {watermark_code} into {output_path}"
            )
            return output_path

        except Exception as e:
            logger.error(f"Failed to embed watermark: {e}")
            raise AudioProcessingError(f"Watermark embedding failed: {str(e)}")

    def extract_and_verify_watermark(
        self,
        audio_path: str,
        filename: str = "",
        ip_address: str = "",
        user_agent: str = "",
    ) -> Dict[str, Any]:
        """提取并验证音频中的水印 - 兼容版本"""
        try:
            if not os.path.exists(audio_path):
                raise AudioProcessingError("Audio file not found")

            # 检查科学计算库可用性
            if not NUMPY_AVAILABLE or not SCIPY_AVAILABLE:
                logger.warning(
                    "NumPy/SciPy not available, returning mock verification result"
                )
                return {
                    "success": False,
                    "verification": "no_watermark_detected",
                    "message": "Watermark extraction requires NumPy and SciPy libraries",
                    "max_accuracy": 0.0,
                }

            # 读取音频
            with wave.open(audio_path, "rb") as wav:
                audio = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16)
                if wav.getnchannels() == 2:
                    audio = audio[::2]  # 转为单声道

            # 尝试不同长度的水印码
            possible_lengths = [8, 16, 32]
            best_result = None
            best_accuracy = 0.0

            for test_length in possible_lengths:
                result = self._extract_watermark_length(audio, test_length)
                if result and result.get("accuracy", 0) > best_accuracy:
                    best_accuracy = result["accuracy"]
                    best_result = result

            logger.info(
                f"Extraction best result: {best_result}, accuracy={best_accuracy:.3f}"
            )

            if best_result and best_accuracy > 0.7:
                watermark_code = best_result["watermark_code"]

                # 查找水印记录
                watermark = Watermark.query.filter_by(
                    watermark_code=watermark_code, is_active=True
                ).first()

                if watermark:
                    # 更新使用统计
                    watermark.increment_usage()

                    # 记录验证日志
                    self._log_verification(
                        watermark_code=watermark_code,
                        filename=filename,
                        accuracy=best_result["accuracy"],
                        extracted_code=best_result["extracted_raw"],
                        success=True,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        details=best_result,
                    )

                    return {
                        "success": True,
                        "verification": "verified",
                        "watermark": watermark.to_dict(),
                        "extraction_details": {
                            "accuracy": best_result["accuracy"],
                            "confidence": best_result.get("confidence"),
                            "code_length": best_result["code_length"],
                        },
                        "message": "水印验证成功",
                    }
                else:
                    # 检测到水印但未在数据库中找到
                    self._log_verification(
                        watermark_code=watermark_code,
                        filename=filename,
                        accuracy=best_result["accuracy"],
                        extracted_code=best_result["extracted_raw"],
                        success=False,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        details=best_result,
                    )

                    return {
                        "success": True,
                        "verification": "watermark_found_but_not_registered",
                        "extracted_code": watermark_code,
                        "accuracy": best_result["accuracy"],
                        "message": "检测到水印但未在数据库中找到对应记录",
                    }
            else:
                # 尝试模糊匹配
                if best_result:
                    fuzzy_match = self._find_closest_watermark(
                        best_result["watermark_code"]
                    )
                    if fuzzy_match:
                        return {
                            "success": True,
                            "verification": "fuzzy_matched",
                            "matched_watermark": fuzzy_match["watermark"].to_dict(),
                            "match_score": fuzzy_match["match_score"],
                            "extracted_code": best_result["watermark_code"],
                            "accuracy": best_result["accuracy"],
                            "message": f"模糊匹配到水印，相似度: {fuzzy_match['match_score']:.2f}",
                        }

                return {
                    "success": False,
                    "verification": "no_watermark_detected",
                    "message": "未检测到有效水印",
                    "max_accuracy": best_accuracy,
                }

        except Exception as e:
            logger.error(f"Watermark extraction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "水印提取过程中发生错误",
            }

    def _extract_watermark_length(
        self, audio: "np.ndarray", code_length: int
    ) -> Optional[Dict]:
        """提取指定长度的水印码"""
        if not NUMPY_AVAILABLE or not SCIPY_AVAILABLE:
            return None

        try:
            spectrum = fft(audio.astype(np.float64))
            spectrum_mag = np.abs(spectrum[: len(spectrum) // 2])

            expected_bits = code_length * 8
            if self.config.use_error_correction:
                expected_bits *= 5

            freq_indices = self.get_frequency_indices(
                self.config.start_freq, self.config.delta, expected_bits
            )

            watermark_mags = []
            for idx in freq_indices:
                if idx < len(spectrum_mag):
                    watermark_mags.append(spectrum_mag[idx])

            # 如果可用频率点太少，跳过
            if len(watermark_mags) < expected_bits * 0.9:
                return None

            # 使用配置的分割策略
            if self.config.split_strategy == "quartile":
                bits, confidences = self._extract_bits_quartile(watermark_mags)
            elif self.config.split_strategy == "adaptive":
                bits, confidences = self._extract_bits_adaptive(watermark_mags)
            else:  # fixed_ratio
                bits, confidences = self._extract_bits_fixed_ratio(watermark_mags)

            # 限制bits长度
            bits = bits[:expected_bits]

            if self.config.use_error_correction:
                bits = self.decode_error_correction(bits)

            watermark_str = self.bin_to_str(bits)
            avg_confidence = float(np.mean(confidences)) if confidences else 0.0

            if watermark_str and len(watermark_str) >= code_length:
                extracted_code = watermark_str[:code_length]

                # 验证格式并计算准确度
                accuracy = self._calculate_accuracy(extracted_code, code_length)

                return {
                    "watermark_code": extracted_code,
                    "extracted_raw": watermark_str,
                    "accuracy": accuracy,
                    "confidence": avg_confidence,
                    "code_length": code_length,
                }

            return None

        except Exception as e:
            logger.error(f"_extract_watermark_length error: {e}")
            return None

    def _extract_bits_quartile(self, watermark_mags: List[float]) -> tuple:
        """使用四分位数方法提取bits"""
        if not NUMPY_AVAILABLE:
            return "", []

        mag_with_index = [(mag, i) for i, mag in enumerate(watermark_mags)]
        mag_with_index.sort(key=lambda x: x[0], reverse=True)

        sorted_mags = [x[0] for x in mag_with_index]
        q75 = np.percentile(sorted_mags, 75)
        q25 = np.percentile(sorted_mags, 25)
        threshold = (q75 + q25) / 2

        above_count = sum(1 for mag in sorted_mags if mag > threshold)
        high_mag_indices = set(x[1] for x in mag_with_index[:above_count])

        bits = ""
        confidences = []

        for i in range(len(watermark_mags)):
            bit = "1" if i in high_mag_indices else "0"
            rank = next(j for j, (_, idx) in enumerate(mag_with_index) if idx == i)
            confidence = abs(rank - above_count) / len(watermark_mags)

            bits += bit
            confidences.append(confidence)

        return bits, confidences

    def _extract_bits_fixed_ratio(self, watermark_mags: List[float]) -> tuple:
        """使用固定比例方法提取bits"""
        mag_with_index = [(mag, i) for i, mag in enumerate(watermark_mags)]
        mag_with_index.sort(key=lambda x: x[0], reverse=True)

        split_point = len(watermark_mags) // 2
        high_mag_indices = set(x[1] for x in mag_with_index[:split_point])

        bits = ""
        confidences = []

        for i in range(len(watermark_mags)):
            bit = "1" if i in high_mag_indices else "0"
            rank = next(j for j, (_, idx) in enumerate(mag_with_index) if idx == i)
            confidence = abs(rank - split_point) / len(watermark_mags)

            bits += bit
            confidences.append(confidence)

        return bits, confidences

    def _extract_bits_adaptive(self, watermark_mags: List[float]) -> tuple:
        """使用自适应方法提取bits"""
        if not NUMPY_AVAILABLE:
            return "", []

        mag_with_index = [(mag, i) for i, mag in enumerate(watermark_mags)]
        mag_with_index.sort(key=lambda x: x[0], reverse=True)

        sorted_vals = [x[0] for x in mag_with_index]
        total = len(sorted_vals)

        best_separation = 0.0
        best_split = total // 2

        for ratio in np.arange(0.2, 0.8, 0.05):
            split_pt = int(total * ratio)
            if split_pt < 5 or split_pt > total - 5:
                continue

            high_group = sorted_vals[:split_pt]
            low_group = sorted_vals[split_pt:]

            if len(high_group) > 2 and len(low_group) > 2:
                separation = (np.mean(high_group) - np.mean(low_group)) / (
                    np.std(high_group) + np.std(low_group) + 0.1 * np.mean(high_group)
                )
                if separation > best_separation:
                    best_separation = separation
                    best_split = split_pt

        high_mag_indices = set(x[1] for x in mag_with_index[:best_split])

        bits = ""
        confidences = []

        for i in range(len(watermark_mags)):
            bit = "1" if i in high_mag_indices else "0"
            rank = next(j for j, (_, idx) in enumerate(mag_with_index) if idx == i)
            confidence = abs(rank - best_split) / len(watermark_mags)

            bits += bit
            confidences.append(confidence)

        return bits, confidences

    def _calculate_accuracy(self, extracted_code: str, code_length: int) -> float:
        """计算提取准确度"""
        if code_length == 8 and extracted_code.isdigit():
            return 0.9
        elif code_length == 16 and all(c.isalnum() for c in extracted_code):
            return 0.85
        elif code_length == 32 and all(
            c in "0123456789abcdef" for c in extracted_code.lower()
        ):
            return 0.8
        else:
            return 0.7

    def _find_closest_watermark(self, extracted_code: str) -> Optional[Dict]:
        """在数据库中查找最相似的水印"""

        def similarity(a: str, b: str) -> float:
            if not a or not b:
                return 0.0
            matches = sum(1 for x, y in zip(a, b) if x == y)
            return matches / max(len(a), len(b))

        all_watermarks = Watermark.query.filter_by(is_active=True).all()
        best_match = None
        best_score = 0.0

        for watermark in all_watermarks:
            score = similarity(extracted_code, watermark.watermark_code)
            if score > best_score and score >= 0.6:  # 最低相似度阈值
                best_score = score
                best_match = watermark

        if best_match:
            return {"watermark": best_match, "match_score": best_score}

        return None

    def _log_verification(
        self,
        watermark_code: str,
        filename: str,
        accuracy: float,
        extracted_code: str,
        success: bool,
        ip_address: str = "",
        user_agent: str = "",
        details: Dict = None,
    ):
        """记录验证日志"""
        try:
            log_entry = WatermarkVerificationLog(
                watermark_code=watermark_code,
                original_filename=filename,
                extraction_accuracy=accuracy,
                extracted_code=extracted_code,
                success=success,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            if details:
                log_entry.set_verification_details(details)

            db.session.add(log_entry)
            db.session.commit()

        except Exception as e:
            logger.error(f"Failed to log verification: {e}")

    def get_user_watermarks(self, user_id: str) -> List[Dict]:
        """获取用户的所有水印"""
        try:
            watermarks = (
                Watermark.query.filter_by(user_id=user_id, is_active=True)
                .order_by(Watermark.created_at.desc())
                .all()
            )

            return [watermark.to_dict() for watermark in watermarks]

        except Exception as e:
            logger.error(f"Failed to get user watermarks: {e}")
            return []

    def get_watermark_statistics(self, user_id: str = None) -> Dict:
        """获取水印统计信息"""
        try:
            query = Watermark.query.filter_by(is_active=True)
            if user_id:
                query = query.filter_by(user_id=user_id)

            total_watermarks = query.count()
            total_usage = db.session.query(
                db.func.sum(Watermark.usage_count)
            ).filter_by(is_active=True)
            if user_id:
                total_usage = total_usage.filter_by(user_id=user_id)
            total_usage = total_usage.scalar() or 0

            # 验证统计
            log_query = WatermarkVerificationLog.query
            if user_id:
                watermark_codes = [w.watermark_code for w in query.all()]
                if watermark_codes:
                    log_query = log_query.filter(
                        WatermarkVerificationLog.watermark_code.in_(watermark_codes)
                    )
                else:
                    log_query = log_query.filter(False)  # 空结果

            total_verifications = log_query.count()
            successful_verifications = log_query.filter_by(success=True).count()

            return {
                "total_watermarks": total_watermarks,
                "total_usage": int(total_usage),
                "total_verifications": total_verifications,
                "successful_verifications": successful_verifications,
                "success_rate": (
                    (successful_verifications / total_verifications * 100)
                    if total_verifications > 0
                    else 0
                ),
            }

        except Exception as e:
            logger.error(f"Failed to get watermark statistics: {e}")
            return {
                "total_watermarks": 0,
                "total_usage": 0,
                "total_verifications": 0,
                "successful_verifications": 0,
                "success_rate": 0,
            }
