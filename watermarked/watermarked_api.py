from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import numpy as np
import wave
import sqlite3
import secrets
import string
import os
import tempfile
import uuid
from datetime import datetime
from scipy.fft import fft, ifft
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import logging
import traceback

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max file size

# 允许的音频文件格式
ALLOWED_EXTENSIONS = {"wav"}


@dataclass
class WatermarkConfig:
    """水印配置"""

    start_freq: int = 1000
    delta: int = 30
    strength_factor: float = 2.0
    boost_factor: float = 0.3
    use_error_correction: bool = True


class WatermarkDatabase:
    """水印数据库管理"""

    def __init__(self, db_path: str = "watermark_api.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS watermark (
                id INTEGER AUTO_INCREMENT PRIMARY KEY,
                watermark_code VARCHAR(64) NOT NULL UNIQUE,
                code_length INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                usage_count INTEGER DEFAULT 0,
                description TEXT,
                file_info TEXT,
                model_id VARCHAR(36),
                user_id VARCHAR(36),
                username VARCHAR(50),
                FOREIGN KEY (user_id) REFERENCES users(id)
                    ON DELETE SET NULL ON UPDATE CASCADE,
                FOREIGN KEY (username) REFERENCES users(username)
                    ON DELETE SET NULL ON UPDATE CASCADE,
                FOREIGN KEY (model_id) REFERENCES voice_models(id)
                    ON DELETE SET NULL ON UPDATE CASCADE
            );
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS verification_log (
                id INTEGER AUTO_INCREMENT PRIMARY KEY,
                watermark_code TEXT,
                original_filename TEXT,
                extraction_accuracy REAL,
                extracted_code TEXT,
                verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN,
                ip_address TEXT,
                user_agent TEXT
            )
        """
        )

        conn.commit()
        conn.close()

    def generate_watermark_code(self, length: int = 16) -> str:
        """生成水印识别码"""
        if length == 8:
            return "".join(secrets.choice(string.digits) for _ in range(8))
        elif length == 16:
            chars = string.ascii_lowercase + string.digits
            return "".join(secrets.choice(chars) for _ in range(16))
        elif length == 32:
            return secrets.token_hex(16)
        else:
            chars = string.ascii_lowercase + string.digits
            return "".join(secrets.choice(chars) for _ in range(length))

    def add_watermark(
        self,
        username: str,
        code_length: int,
        description: str = "",
        file_info: str = "",
    ) -> str:
        """添加水印记录"""
        max_attempts = 10
        for _ in range(max_attempts):
            watermark_code = self.generate_watermark_code(code_length)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            try:
                cursor.execute(
                    """
                    INSERT INTO watermark (username, watermark_code, code_length, description, file_info)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (username, watermark_code, code_length, description, file_info),
                )
                conn.commit()
                conn.close()
                return watermark_code
            except sqlite3.IntegrityError:
                conn.close()
                continue

        raise Exception("无法生成唯一的水印码")

    def get_user_by_watermark(self, watermark_code: str) -> Optional[Dict]:
        """根据水印码查找用户"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT username, watermark_code, code_length, created_at, usage_count, description
            FROM watermark WHERE watermark_code = ?
        """,
            (watermark_code,),
        )

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                "username": result[0],
                "watermark_code": result[1],
                "code_length": result[2],
                "created_at": result[3],
                "usage_count": result[4],
                "description": result[5],
            }
        return None

    def update_usage(self, watermark_code: str):
        """更新使用统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE watermark 
            SET usage_count = usage_count + 1, last_used = CURRENT_TIMESTAMP
            WHERE watermark_code = ?
        """,
            (watermark_code,),
        )

        conn.commit()
        conn.close()

    def log_verification(
        self,
        watermark_code: str,
        filename: str,
        accuracy: float,
        extracted_code: str,
        success: bool,
        ip_address: str = "",
        user_agent: str = "",
    ):
        """记录验证日志"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO verification_log 
            (watermark_code, original_filename, extraction_accuracy, extracted_code, 
             success, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                watermark_code,
                filename,
                accuracy,
                extracted_code,
                success,
                ip_address,
                user_agent,
            ),
        )

        conn.commit()
        conn.close()


class AudioWatermarkProcessor:
    """音频水印处理器"""

    def __init__(self):
        self.config = WatermarkConfig()
        self.db = WatermarkDatabase()

    def str_to_bin(self, s: str) -> str:
        return "".join(format(ord(c), "08b") for c in s)

    def bin_to_str(self, b: str) -> str:
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
        except:
            return None

    def add_error_correction(self, data: str) -> str:
        """5重复纠错编码"""
        return "".join(bit * 5 for bit in data)

    def decode_error_correction(self, data: str) -> str:
        """5重复解码"""
        if len(data) % 5 != 0:
            return data

        decoded = ""
        for i in range(0, len(data), 5):
            quintuple = data[i : i + 5]
            ones = quintuple.count("1")
            decoded += "1" if ones >= 3 else "0"
        return decoded

    def get_prime_frequency_indices(
        self, start_freq: int, delta: int, num_bits: int
    ) -> List[int]:
        """生成质数分布的频率索引"""
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
            73,
            79,
            83,
            89,
            97,
        ]
        indices = []

        for i in range(num_bits):
            prime_offset = primes[i % len(primes)]
            indices.append(start_freq + i * delta + prime_offset)

        return indices

    def embed_watermark(
        self,
        input_path: str,
        output_path: str,
        username: str,
        code_length: int = 16,
        description: str = "",
    ) -> Dict[str, Any]:
        """嵌入水印"""
        try:
            # 获取文件信息
            file_size = os.path.getsize(input_path)
            file_info = f"size: {file_size} bytes"

            # 生成水印码
            watermark_code = self.db.add_watermark(
                username, code_length, description, file_info
            )

            # 读取音频
            with wave.open(input_path, "rb") as wav:
                params = wav.getparams()
                n_frames = wav.getnframes()
                audio = np.frombuffer(wav.readframes(n_frames), dtype=np.int16)
                if wav.getnchannels() == 2:
                    audio = audio[::2]

            # 转换为频域
            spectrum = fft(audio.astype(np.float64))

            # 准备水印数据
            watermark_bin = self.str_to_bin(watermark_code)
            if self.config.use_error_correction:
                watermark_bin = self.add_error_correction(watermark_bin)

            # 获取频率索引
            freq_indices = self.get_prime_frequency_indices(
                self.config.start_freq, self.config.delta, len(watermark_bin)
            )

            # 检查频率范围并自动调整
            max_freq = max(freq_indices)
            max_allowed = len(spectrum) // 2 - 100

            if max_freq > max_allowed:
                available_range = max_allowed - self.config.start_freq
                new_delta = available_range // len(watermark_bin)
                self.config.delta = max(new_delta, 20)
                freq_indices = self.get_prime_frequency_indices(
                    self.config.start_freq, self.config.delta, len(watermark_bin)
                )

            # 嵌入水印
            for i, (bit, freq_index) in enumerate(zip(watermark_bin, freq_indices)):
                original_complex = spectrum[freq_index]
                original_mag = abs(original_complex)
                phase = np.angle(original_complex)

                if bit == "1":
                    new_mag = original_mag * (1 + self.config.strength_factor)
                    new_mag += original_mag * self.config.boost_factor + 1200
                else:
                    new_mag = original_mag * (1 - self.config.strength_factor)
                    new_mag *= 1 - self.config.boost_factor
                    new_mag = max(new_mag, original_mag * 0.008, 8)

                spectrum[freq_index] = new_mag * np.exp(1j * phase)
                if freq_index < len(spectrum) - freq_index:
                    spectrum[-freq_index] = np.conj(spectrum[freq_index])

            # 逆FFT
            watermarked_audio = np.real(ifft(spectrum))

            # 归一化
            max_val = np.max(np.abs(watermarked_audio))
            if max_val > 32767:
                watermarked_audio = watermarked_audio * (29000 / max_val)

            watermarked_audio = watermarked_audio.astype(np.int16)

            # 保存立体声
            if params.nchannels == 2:
                stereo_audio = np.zeros(len(watermarked_audio) * 2, dtype=np.int16)
                stereo_audio[::2] = watermarked_audio
                stereo_audio[1::2] = watermarked_audio
                watermarked_audio = stereo_audio

            # 保存音频
            with wave.open(output_path, "wb") as out_wav:
                out_wav.setparams(params)
                out_wav.writeframes(watermarked_audio.tobytes())

            return {
                "success": True,
                "watermark_code": watermark_code,
                "code_length": code_length,
                "username": username,
                "embedded_bits": len(watermark_bin),
                "frequency_range": f"{min(freq_indices)}-{max(freq_indices)}",
                "description": description,
            }

        except Exception as e:
            logger.error(f"嵌入水印失败: {str(e)}")
            return {"success": False, "error": str(e)}

    def extract_watermark(
        self,
        audio_path: str,
        filename: str = "",
        ip_address: str = "",
        user_agent: str = "",
    ) -> Dict[str, Any]:
        """提取并验证水印"""
        try:
            # 读取音频
            with wave.open(audio_path, "rb") as wav:
                audio = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16)
                if wav.getnchannels() == 2:
                    audio = audio[::2]

            # 尝试不同长度的水印码
            possible_lengths = [8, 16, 32]
            best_result = None
            best_accuracy = 0

            for test_length in possible_lengths:
                result = self._extract_watermark_length(audio, test_length)
                if result and result["accuracy"] > best_accuracy:
                    best_accuracy = result["accuracy"]
                    best_result = result

            if best_result and best_result["accuracy"] > 0.7:
                # 查找用户信息
                user_info = self.db.get_user_by_watermark(best_result["watermark_code"])

                if user_info:
                    # 更新使用记录
                    self.db.update_usage(best_result["watermark_code"])

                    # 记录验证日志
                    self.db.log_verification(
                        best_result["watermark_code"],
                        filename,
                        best_result["accuracy"],
                        best_result["extracted_raw"],
                        True,
                        ip_address,
                        user_agent,
                    )

                    return {
                        "success": True,
                        "verification": "verified",
                        "username": user_info["username"],
                        "watermark_code": best_result["watermark_code"],
                        "code_length": best_result["code_length"],
                        "accuracy": best_result["accuracy"],
                        "confidence": best_result["confidence"],
                        "created_at": user_info["created_at"],
                        "usage_count": user_info["usage_count"] + 1,
                        "description": user_info["description"],
                    }
                else:
                    # 记录未找到用户的日志
                    self.db.log_verification(
                        best_result["watermark_code"],
                        filename,
                        best_result["accuracy"],
                        best_result["extracted_raw"],
                        False,
                        ip_address,
                        user_agent,
                    )

                    return {
                        "success": True,
                        "verification": "watermark_found_but_not_registered",
                        "extracted_code": best_result["watermark_code"],
                        "accuracy": best_result["accuracy"],
                        "message": "检测到水印但未在数据库中找到对应用户",
                    }
            else:
                return {
                    "success": False,
                    "verification": "no_watermark_detected",
                    "message": "未检测到有效水印",
                    "max_accuracy": best_accuracy,
                }

        except Exception as e:
            logger.error(f"提取水印失败: {str(e)}")
            return {"success": False, "error": str(e)}

    def _extract_watermark_length(
        self, audio: np.ndarray, code_length: int
    ) -> Optional[Dict]:
        """提取指定长度的水印码"""
        try:
            spectrum = fft(audio.astype(np.float64))
            spectrum_mag = np.abs(spectrum[: len(spectrum) // 2])

            expected_bits = code_length * 8
            if self.config.use_error_correction:
                expected_bits *= 5

            freq_indices = self.get_prime_frequency_indices(
                self.config.start_freq, self.config.delta, expected_bits
            )

            watermark_mags = []
            for freq_index in freq_indices:
                if freq_index < len(spectrum_mag):
                    watermark_mags.append(spectrum_mag[freq_index])

            if len(watermark_mags) < expected_bits * 0.9:
                return None

            # 四分位数分割
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

            for i in range(min(expected_bits, len(watermark_mags))):
                bit = "1" if i in high_mag_indices else "0"
                rank = next(j for j, (_, idx) in enumerate(mag_with_index) if idx == i)
                confidence = abs(rank - above_count) / len(watermark_mags)

                bits += bit
                confidences.append(confidence)

            if self.config.use_error_correction:
                bits = self.decode_error_correction(bits)

            watermark_str = self.bin_to_str(bits)
            avg_confidence = np.mean(confidences) if confidences else 0

            if watermark_str and len(watermark_str) >= code_length:
                extracted_code = watermark_str[:code_length]

                # 格式验证
                if code_length == 8 and extracted_code.isdigit():
                    accuracy = 0.9
                elif code_length == 16 and all(c.isalnum() for c in extracted_code):
                    accuracy = 0.85
                elif code_length == 32 and all(
                    c in "0123456789abcdef" for c in extracted_code.lower()
                ):
                    accuracy = 0.8
                else:
                    accuracy = 0.7

                return {
                    "watermark_code": extracted_code,
                    "extracted_raw": watermark_str,
                    "accuracy": accuracy,
                    "confidence": avg_confidence,
                    "code_length": code_length,
                }

            return None

        except Exception:
            return None


def allowed_file(filename):
    """检查文件类型"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# 初始化处理器
processor = AudioWatermarkProcessor()


@app.route("/api/health", methods=["GET"])
def health_check():
    """健康检查"""
    return jsonify(
        {
            "status": "healthy",
            "service": "audio_watermark_api",
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/api/watermark/embed", methods=["POST"])
def embed_watermark_api():
    """
    嵌入水印API

    参数:
    - file: 音频文件 (WAV格式)
    - username: 用户名 (必需)
    - code_length: 识别码长度 (8, 16, 32, 默认16)
    - description: 描述信息 (可选)

    返回:
    - 带水印的音频文件
    """
    try:
        # 检查文件
        if "file" not in request.files:
            return jsonify({"error": "未提供音频文件"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "未选择文件"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "只支持WAV格式文件"}), 400

        # 检查必需参数
        username = request.form.get("username")
        if not username:
            return jsonify({"error": "用户名不能为空"}), 400

        # 获取可选参数
        code_length = int(request.form.get("code_length", 16))
        if code_length not in [8, 16, 32]:
            return jsonify({"error": "识别码长度必须是8, 16, 或32"}), 400

        description = request.form.get("description", "")

        # 保存上传的文件
        filename = secure_filename(file.filename)
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        file.save(temp_input.name)

        # 创建输出文件
        temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_output.close()

        # 嵌入水印
        result = processor.embed_watermark(
            temp_input.name, temp_output.name, username, code_length, description
        )

        # 清理输入文件
        os.unlink(temp_input.name)

        if result["success"]:
            # 返回带水印的文件
            return send_file(
                temp_output.name,
                as_attachment=True,
                download_name=f"watermarked_{filename}",
                mimetype="audio/wav",
            )
        else:
            os.unlink(temp_output.name)
            return (
                jsonify(
                    {
                        "error": "水印嵌入失败",
                        "details": result.get("error", "未知错误"),
                    }
                ),
                500,
            )

    except Exception as e:
        logger.error(f"嵌入水印API错误: {str(e)}")
        return jsonify({"error": "服务器内部错误"}), 500


@app.route("/api/watermark/verify", methods=["POST"])
def verify_watermark_api():
    """
    验证水印API

    参数:
    - file: 音频文件 (WAV格式)

    返回:
    - 验证结果和用户信息
    """
    try:
        # 检查文件
        if "file" not in request.files:
            return jsonify({"error": "未提供音频文件"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "未选择文件"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "只支持WAV格式文件"}), 400

        # 获取客户端信息
        ip_address = request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr)
        user_agent = request.environ.get("HTTP_USER_AGENT", "")

        # 保存上传的文件
        filename = secure_filename(file.filename)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        file.save(temp_file.name)

        # 验证水印
        result = processor.extract_watermark(
            temp_file.name, filename, ip_address, user_agent
        )

        # 清理临时文件
        os.unlink(temp_file.name)

        if result["success"]:
            return jsonify(
                {
                    "status": "success",
                    "verification": result["verification"],
                    "data": {
                        "username": result.get("username"),
                        "watermark_code": result.get("watermark_code"),
                        "code_length": result.get("code_length"),
                        "accuracy": result.get("accuracy"),
                        "confidence": result.get("confidence"),
                        "created_at": result.get("created_at"),
                        "usage_count": result.get("usage_count"),
                        "description": result.get("description"),
                    },
                    "message": result.get("message", "验证成功"),
                }
            )
        else:
            return jsonify(
                {
                    "status": "failed",
                    "verification": result.get("verification", "failed"),
                    "message": result.get("message", "验证失败"),
                    "error": result.get("error"),
                }
            )

    except Exception as e:
        logger.error(f"验证水印API错误: {str(e)}")
        return jsonify({"error": "服务器内部错误"}), 500


@app.route("/api/watermark/info/<watermark_code>", methods=["GET"])
def get_watermark_info(watermark_code):
    """
    根据水印码获取信息
    """
    try:
        user_info = processor.db.get_user_by_watermark(watermark_code)

        if user_info:
            return jsonify({"status": "found", "data": user_info})
        else:
            return (
                jsonify({"status": "not_found", "message": "未找到对应的水印记录"}),
                404,
            )

    except Exception as e:
        logger.error(f"查询水印信息错误: {str(e)}")
        return jsonify({"error": "服务器内部错误"}), 500


@app.route("/api/user/<username>/watermarks", methods=["GET"])
def get_user_watermarks(username):
    """
    获取用户的所有水印
    """
    try:
        watermarks = processor.db.get_user_watermarks(username)

        return jsonify(
            {
                "status": "success",
                "username": username,
                "watermarks": watermarks,
                "count": len(watermarks),
            }
        )

    except Exception as e:
        logger.error(f"查询用户水印错误: {str(e)}")
        return jsonify({"error": "服务器内部错误"}), 500


@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "文件太大，最大支持50MB"}), 413


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "API端点不存在"}), 404


if __name__ == "__main__":
    print("🚀 启动音频水印API服务...")
    print("📋 可用的API端点:")
    print("  POST /api/watermark/embed    - 嵌入水印")
    print("  POST /api/watermark/verify   - 验证水印")
    print("  GET  /api/watermark/info/<code> - 查询水印信息")
    print("  GET  /api/user/<username>/watermarks - 查询用户水印")
    print("  GET  /api/health             - 健康检查")
    print("\n💡 使用方法:")
    print(
        "  curl -X POST -F 'file=@audio.wav' -F 'username=alice' -F 'code_length=16' http://localhost:5000/api/watermark/embed"
    )
    print(
        "  curl -X POST -F 'file=@watermarked.wav' http://localhost:5000/api/watermark/verify"
    )

    app.run(debug=True, host="0.0.0.0", port=5000)
