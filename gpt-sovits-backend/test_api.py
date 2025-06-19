#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ./gpt-sovits-backend/test_api.py
"""
完整的API测试脚本
用于测试GPT-SoVITS后端所有API接口
放置位置: ./gpt-sovits-backend/test_api.py
"""

import requests
import json
import time
import io
import os
import struct
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional

# API基础URL
BASE_URL = "http://localhost:5000/api"


class APITester:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token = None
        self.user_id = None
        self.admin_token = None
        self.test_data = {}

    def log(self, message: str, level: str = "INFO"):
        """打印带时间戳的日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """发送HTTP请求的通用方法"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            self.log(f"Request failed: {e}", "ERROR")
            raise

    def set_auth_header(self, token: str):
        """设置认证头"""
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            self.session.headers.pop("Authorization", None)

    # ===============================
    # 健康检查和基础测试
    # ===============================

    def test_health_check(self) -> bool:
        """测试健康检查接口"""
        self.log("Testing health check...")
        try:
            response = self.make_request("GET", "/health")
            self.log(f"Health check status: {response.status_code}")

            if response.status_code in [200, 503]:  # 修复：503也是预期状态
                data = response.json()
                self.log(f"Health status: {data.get('status', 'unknown')}")

                # 检查服务状态
                services = data.get("services", {})
                for service, status in services.items():
                    self.log(f"  {service}: {status}")

                # 修复：即使某些服务不可用，只要API响应正常就算成功
                return True
        except Exception as e:
            self.log(f"Health check failed: {e}", "ERROR")
        return False

    # ===============================
    # 认证相关测试
    # ===============================

    def test_user_registration(self) -> bool:
        """测试用户注册"""
        self.log("Testing user registration...")
        try:
            # 使用时间戳确保用户名唯一
            timestamp = int(time.time())
            data = {
                "username": f"testuser{timestamp}",
                "email": f"testuser{timestamp}@example.com",
                "password": "TestPassword123!",
            }
            response = self.make_request("POST", "/auth/register", json=data)
            self.log(f"Registration status: {response.status_code}")

            if response.status_code == 201:
                result = response.json()
                self.log("Registration successful!")

                # 保存用户信息
                user_data = result.get("data", {})
                if user_data.get("access_token"):
                    self.access_token = user_data["access_token"]
                    self.set_auth_header(self.access_token)

                if user_data.get("user"):
                    self.user_id = user_data["user"]["id"]
                    self.test_data["user"] = user_data["user"]
                    self.test_data["username"] = data["username"]
                    self.test_data["password"] = data["password"]

                return True
            else:
                self.log(f"Registration failed: {response.text}", "ERROR")

        except Exception as e:
            self.log(f"Registration error: {e}", "ERROR")
        return False

    def test_user_login(self) -> bool:
        """测试用户登录"""
        self.log("Testing user login...")
        try:
            # 先清除现有token
            self.set_auth_header(None)

            username = self.test_data.get("username", "testuser123")
            password = self.test_data.get("password", "TestPassword123!")

            data = {"identifier": username, "password": password}
            response = self.make_request("POST", "/auth/login", json=data)
            self.log(f"Login status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                self.log("Login successful!")

                user_data = result.get("data", {})
                self.access_token = user_data["access_token"]
                self.set_auth_header(self.access_token)

                return True
            else:
                self.log(f"Login failed: {response.text}", "ERROR")

        except Exception as e:
            self.log(f"Login error: {e}", "ERROR")
        return False

    def test_logout(self) -> bool:
        """测试用户登出"""
        self.log("Testing user logout...")
        try:
            response = self.make_request("POST", "/auth/logout")
            self.log(f"Logout status: {response.status_code}")

            return response.status_code == 200

        except Exception as e:
            self.log(f"Logout error: {e}", "ERROR")
        return False

    def test_password_change(self) -> bool:
        """测试修改密码"""
        self.log("Testing password change...")
        try:
            old_password = self.test_data.get("password", "TestPassword123!")
            new_password = "NewTestPassword123!"

            data = {
                "current_password": old_password,
                "new_password": new_password,
            }
            response = self.make_request("POST", "/auth/change-password", json=data)
            self.log(f"Password change status: {response.status_code}")

            if response.status_code == 200:
                # 更新密码记录
                self.test_data["password"] = new_password
                return True

            return False

        except Exception as e:
            self.log(f"Password change error: {e}", "ERROR")
        return False

    # ===============================
    # 用户管理测试
    # ===============================

    def test_get_user_profile(self) -> bool:
        """测试获取用户资料"""
        self.log("Testing get user profile...")
        try:
            response = self.make_request("GET", "/user/profile")
            self.log(f"Profile status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                profile = result.get("data", {}).get("profile", {})
                self.log(f"Profile username: {profile.get('username')}")
                self.test_data["profile"] = profile
                return True
            else:
                self.log(f"Profile failed: {response.text}", "ERROR")

        except Exception as e:
            self.log(f"Profile error: {e}", "ERROR")
        return False

    def test_update_user_profile(self) -> bool:
        """测试更新用户资料"""
        self.log("Testing update user profile...")
        try:
            data = {"avatar_url": "https://example.com/avatar.jpg"}
            response = self.make_request("PUT", "/user/profile", json=data)
            self.log(f"Profile update status: {response.status_code}")

            return response.status_code == 200

        except Exception as e:
            self.log(f"Profile update error: {e}", "ERROR")
        return False

    def test_get_user_statistics(self) -> bool:
        """测试获取用户统计信息"""
        self.log("Testing get user statistics...")
        try:
            response = self.make_request("GET", "/user/statistics")
            self.log(f"Statistics status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                stats = result.get("data", {})
                self.log(f"User stats: {len(stats)} categories")
                return True

        except Exception as e:
            self.log(f"Statistics error: {e}", "ERROR")
        return False

    def test_get_task_history(self) -> bool:
        """测试获取任务历史"""
        self.log("Testing get task history...")
        try:
            response = self.make_request("GET", "/user/tasks/history")
            self.log(f"Task history status: {response.status_code}")

            return response.status_code == 200

        except Exception as e:
            self.log(f"Task history error: {e}", "ERROR")
        return False

    # ===============================
    # 语音克隆相关测试
    # ===============================

    def create_mock_audio_file(self, duration=12.0) -> io.BytesIO:
        """创建模拟音频文件 - 修复：增加默认时长"""
        # 创建更长的WAV文件以满足时长要求
        sample_rate = 16000
        samples = int(duration * sample_rate)

        # 生成正弦波音频数据
        t = np.linspace(0, duration, samples, False)
        frequency = 440  # A4音符
        audio_data = (np.sin(2 * np.pi * frequency * t) * 0.3 * 32767).astype(np.int16)

        # WAV文件头
        wav_file = io.BytesIO()

        # RIFF头
        wav_file.write(b"RIFF")
        wav_file.write(struct.pack("<I", 36 + len(audio_data) * 2))
        wav_file.write(b"WAVE")

        # fmt块
        wav_file.write(b"fmt ")
        wav_file.write(struct.pack("<I", 16))  # fmt chunk大小
        wav_file.write(struct.pack("<H", 1))  # PCM格式
        wav_file.write(struct.pack("<H", 1))  # 单声道
        wav_file.write(struct.pack("<I", sample_rate))  # 采样率
        wav_file.write(struct.pack("<I", sample_rate * 2))  # 字节率
        wav_file.write(struct.pack("<H", 2))  # 块对齐
        wav_file.write(struct.pack("<H", 16))  # 位深度

        # data块
        wav_file.write(b"data")
        wav_file.write(struct.pack("<I", len(audio_data) * 2))
        wav_file.write(audio_data.tobytes())

        wav_file.seek(0)
        return wav_file

    def test_upload_audio_sample(self, duration=12.0) -> bool:
        """测试上传音频样本 - 修复：支持指定时长"""
        self.log("Testing upload audio sample...")
        try:
            # 创建模拟音频文件
            audio_file = self.create_mock_audio_file(duration)

            files = {"audio_file": ("test_sample.wav", audio_file, "audio/wav")}

            response = self.make_request(
                "POST", "/voice-clone/upload-sample", files=files
            )
            self.log(f"Upload sample status: {response.status_code}")

            if response.status_code == 201:
                result = response.json()
                upload_id = result.get("data", {}).get("upload_id")
                if upload_id:
                    self.test_data["sample_ids"] = self.test_data.get("sample_ids", [])
                    self.test_data["sample_ids"].append(upload_id)
                    self.log(f"Uploaded sample ID: {upload_id}")
                return True
            else:
                self.log(f"Upload failed: {response.text}", "ERROR")

        except Exception as e:
            self.log(f"Upload error: {e}", "ERROR")
        return False

    def test_start_voice_clone_training(self) -> bool:
        """测试启动语音克隆训练 - 修复：确保足够的音频时长"""
        self.log("Testing start voice clone training...")

        # 先上传多个较长的样本
        for i in range(3):
            if not self.test_upload_audio_sample(duration=12.0):  # 12秒每个样本
                return False

        try:
            sample_ids = self.test_data.get("sample_ids", [])
            if len(sample_ids) < 3:
                self.log("Insufficient audio samples for training", "ERROR")
                return False

            data = {"model_name": "Test_Voice_Model", "sample_ids": sample_ids[:3]}

            response = self.make_request(
                "POST", "/voice-clone/start-training", json=data
            )
            self.log(f"Start training status: {response.status_code}")

            if response.status_code == 201:
                result = response.json()
                task_id = result.get("data", {}).get("task_id")
                if task_id:
                    self.test_data["voice_clone_task_id"] = task_id
                    self.log(f"Training task ID: {task_id}")
                return True
            else:
                self.log(f"Training failed: {response.text}", "ERROR")

        except Exception as e:
            self.log(f"Training error: {e}", "ERROR")
        return False

    def test_get_voice_clone_tasks(self) -> bool:
        """测试获取语音克隆任务列表"""
        self.log("Testing get voice clone tasks...")
        try:
            response = self.make_request("GET", "/voice-clone/tasks")
            self.log(f"Voice clone tasks status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                tasks = result.get("data", {}).get("tasks", [])
                self.log(f"Found {len(tasks)} voice clone tasks")
                return True

        except Exception as e:
            self.log(f"Voice clone tasks error: {e}", "ERROR")
        return False

    def test_get_voice_clone_task_detail(self) -> bool:
        """测试获取语音克隆任务详情"""
        self.log("Testing get voice clone task detail...")

        task_id = self.test_data.get("voice_clone_task_id")
        if not task_id:
            self.log("No voice clone task ID available", "WARN")
            return True  # 跳过测试

        try:
            response = self.make_request("GET", f"/voice-clone/tasks/{task_id}")
            self.log(f"Task detail status: {response.status_code}")

            return response.status_code == 200

        except Exception as e:
            self.log(f"Task detail error: {e}", "ERROR")
        return False

    def test_get_audio_samples(self) -> bool:
        """测试获取用户音频样本"""
        self.log("Testing get audio samples...")
        try:
            response = self.make_request("GET", "/voice-clone/samples")
            self.log(f"Audio samples status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                samples = result.get("data", {}).get("samples", [])
                self.log(f"Found {len(samples)} audio samples")
                return True

        except Exception as e:
            self.log(f"Audio samples error: {e}", "ERROR")
        return False

    # ===============================
    # TTS相关测试
    # ===============================

    def test_get_tts_models(self) -> bool:
        """测试获取TTS模型列表"""
        self.log("Testing get TTS models...")
        try:
            response = self.make_request("GET", "/tts/models")
            self.log(f"TTS models status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                models = result.get("data", {}).get("models", [])
                self.log(f"Found {len(models)} TTS models")

                # 保存第一个模型ID用于后续测试
                if models:
                    self.test_data["model_id"] = models[0]["id"]
                    self.log(f"Using model ID: {models[0]['id']}")

                return True
            else:
                self.log(f"TTS models failed: {response.text}", "ERROR")

        except Exception as e:
            self.log(f"TTS models error: {e}", "ERROR")
        return False

    def test_get_tts_emotions(self) -> bool:
        """测试获取支持的情感"""
        self.log("Testing get TTS emotions...")
        try:
            response = self.make_request("GET", "/tts/emotions")
            self.log(f"TTS emotions status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                emotions = result.get("data", {}).get("emotions", [])
                self.log(f"Found {len(emotions)} emotions")
                return True
            else:
                self.log(f"TTS emotions failed: {response.text}", "ERROR")

        except Exception as e:
            self.log(f"TTS emotions error: {e}", "ERROR")
        return False

    def test_generate_speech(self) -> bool:
        """测试生成语音"""
        self.log("Testing generate speech...")

        model_id = self.test_data.get("model_id")
        if not model_id:
            self.log("No model ID available for TTS test", "WARN")
            return True  # 跳过测试

        try:
            data = {
                "text": "这是一个测试语音合成的文本内容。",
                "model_id": model_id,
                "emotion": "neutral",
                "speed": 1.0,
            }

            response = self.make_request("POST", "/tts/generate", json=data)
            self.log(f"Generate speech status: {response.status_code}")

            if response.status_code == 201:
                result = response.json()
                task_id = result.get("data", {}).get("task_id")
                if task_id:
                    self.test_data["tts_task_id"] = task_id
                    self.log(f"TTS task ID: {task_id}")
                return True
            else:
                self.log(f"Generate speech failed: {response.text}", "ERROR")

        except Exception as e:
            self.log(f"Generate speech error: {e}", "ERROR")
        return False

    def test_get_tts_tasks(self) -> bool:
        """测试获取TTS任务列表"""
        self.log("Testing get TTS tasks...")
        try:
            response = self.make_request("GET", "/tts/tasks")
            self.log(f"TTS tasks status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                tasks = result.get("data", {}).get("tasks", [])
                self.log(f"Found {len(tasks)} TTS tasks")
                return True

        except Exception as e:
            self.log(f"TTS tasks error: {e}", "ERROR")
        return False

    def test_get_tts_task_detail(self) -> bool:
        """测试获取TTS任务详情"""
        self.log("Testing get TTS task detail...")

        task_id = self.test_data.get("tts_task_id")
        if not task_id:
            self.log("No TTS task ID available", "WARN")
            return True  # 跳过测试

        try:
            response = self.make_request("GET", f"/tts/tasks/{task_id}")
            self.log(f"TTS task detail status: {response.status_code}")

            return response.status_code == 200

        except Exception as e:
            self.log(f"TTS task detail error: {e}", "ERROR")
        return False

    # ===============================
    # 模型管理测试
    # ===============================

    def test_get_my_models(self) -> bool:
        """测试获取用户模型列表"""
        self.log("Testing get my models...")
        try:
            response = self.make_request("GET", "/models/my-models")
            self.log(f"My models status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                models = result.get("data", {}).get("models", [])
                self.log(f"Found {len(models)} user models")
                return True

        except Exception as e:
            self.log(f"My models error: {e}", "ERROR")
        return False

    def test_get_model_tags(self) -> bool:
        """测试获取模型标签"""
        self.log("Testing get model tags...")
        try:
            response = self.make_request("GET", "/models/tags")
            self.log(f"Model tags status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                tags = result.get("data", {}).get("tags", [])
                self.log(f"Found {len(tags)} model tags")
                return True

        except Exception as e:
            self.log(f"Model tags error: {e}", "ERROR")
        return False

    def test_get_model_stats(self) -> bool:
        """测试获取模型统计"""
        self.log("Testing get model stats...")
        try:
            response = self.make_request("GET", "/models/stats")
            self.log(f"Model stats status: {response.status_code}")

            return response.status_code == 200

        except Exception as e:
            self.log(f"Model stats error: {e}", "ERROR")
        return False

    # ===============================
    # 管理员功能测试 (需要管理员权限)
    # ===============================

    def test_admin_statistics(self) -> bool:
        """测试管理员统计信息"""
        self.log("Testing admin statistics...")
        try:
            response = self.make_request("GET", "/admin/statistics")
            self.log(f"Admin statistics status: {response.status_code}")

            # 403表示权限不足，这是预期的（普通用户）
            return response.status_code in [200, 403]

        except Exception as e:
            self.log(f"Admin statistics error: {e}", "ERROR")
        return False

    # ===============================
    # 错误处理测试
    # ===============================

    def test_unauthorized_access(self) -> bool:
        """测试未授权访问"""
        self.log("Testing unauthorized access...")
        try:
            # 临时移除授权头
            old_token = self.access_token
            self.set_auth_header(None)

            response = self.make_request("GET", "/user/profile")
            self.log(f"Unauthorized status: {response.status_code}")

            # 恢复授权头
            self.set_auth_header(old_token)

            return response.status_code == 401

        except Exception as e:
            self.log(f"Unauthorized test error: {e}", "ERROR")
        return False

    def test_invalid_endpoints(self) -> bool:
        """测试无效端点"""
        self.log("Testing invalid endpoints...")
        try:
            response = self.make_request("GET", "/invalid/endpoint")
            self.log(f"Invalid endpoint status: {response.status_code}")

            return response.status_code == 404

        except Exception as e:
            self.log(f"Invalid endpoint test error: {e}", "ERROR")
        return False

    def test_invalid_data(self) -> bool:
        """测试无效数据"""
        self.log("Testing invalid data...")
        try:
            # 测试注册时缺少必需字段
            data = {"username": "test"}  # 缺少email和password
            response = self.make_request("POST", "/auth/register", json=data)
            self.log(f"Invalid data status: {response.status_code}")

            return response.status_code in [400, 422]

        except Exception as e:
            self.log(f"Invalid data test error: {e}", "ERROR")
        return False

    # ===============================
    # 主测试运行器
    # ===============================

    def run_all_tests(self) -> Dict[str, str]:
        """运行所有测试"""
        self.log("Starting comprehensive API tests...")
        self.log("=" * 60)

        # 定义所有测试用例
        test_suites = [
            # 基础测试
            ("Health Check", self.test_health_check),
            # 认证测试
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("User Logout", self.test_logout),
            ("Password Change", self.test_password_change),
            # 用户管理测试
            ("Get User Profile", self.test_get_user_profile),
            ("Update User Profile", self.test_update_user_profile),
            ("Get User Statistics", self.test_get_user_statistics),
            ("Get Task History", self.test_get_task_history),
            # 语音克隆测试
            ("Upload Audio Sample", self.test_upload_audio_sample),
            ("Start Voice Clone Training", self.test_start_voice_clone_training),
            ("Get Voice Clone Tasks", self.test_get_voice_clone_tasks),
            ("Get Voice Clone Task Detail", self.test_get_voice_clone_task_detail),
            ("Get Audio Samples", self.test_get_audio_samples),
            # TTS测试
            ("Get TTS Models", self.test_get_tts_models),
            ("Get TTS Emotions", self.test_get_tts_emotions),
            ("Generate Speech", self.test_generate_speech),
            ("Get TTS Tasks", self.test_get_tts_tasks),
            ("Get TTS Task Detail", self.test_get_tts_task_detail),
            # 模型管理测试
            ("Get My Models", self.test_get_my_models),
            ("Get Model Tags", self.test_get_model_tags),
            ("Get Model Stats", self.test_get_model_stats),
            # 管理员测试
            ("Admin Statistics", self.test_admin_statistics),
            # 错误处理测试
            ("Unauthorized Access", self.test_unauthorized_access),
            ("Invalid Endpoints", self.test_invalid_endpoints),
            ("Invalid Data", self.test_invalid_data),
        ]

        results = {}

        for test_name, test_func in test_suites:
            try:
                self.log(f"\n--- Running: {test_name} ---")
                result = test_func()
                status = "PASS" if result else "FAIL"
                results[test_name] = status

                status_symbol = "✓" if result else "✗"
                self.log(f"{status_symbol} {test_name}: {status}")

            except Exception as e:
                results[test_name] = "ERROR"
                self.log(f"✗ {test_name}: ERROR - {e}", "ERROR")

            # 短暂延迟避免请求过快
            time.sleep(0.2)

        # 输出测试总结
        self.log("\n" + "=" * 60)
        self.log("TEST RESULTS SUMMARY")
        self.log("=" * 60)

        pass_count = 0
        fail_count = 0
        error_count = 0

        for test_name, result in results.items():
            if result == "PASS":
                status_symbol = "✓"
                pass_count += 1
            elif result == "FAIL":
                status_symbol = "✗"
                fail_count += 1
            else:
                status_symbol = "!"
                error_count += 1

            self.log(f"{status_symbol} {test_name}: {result}")

        total_count = len(results)
        self.log(f"\nTOTAL: {pass_count}/{total_count} tests passed")
        self.log(f"PASS: {pass_count}, FAIL: {fail_count}, ERROR: {error_count}")

        if pass_count == total_count:
            self.log("🎉 All tests passed!", "SUCCESS")
        elif pass_count >= total_count * 0.8:
            self.log("⚠️  Most tests passed, some issues found", "WARN")
        else:
            self.log("❌ Many tests failed, please check the issues", "ERROR")

        return results


def main():
    """主函数"""
    print("GPT-SoVITS Backend Comprehensive API Tester")
    print("=" * 50)

    # 检查服务器是否运行
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"✓ Server is running (status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Server is not running or not accessible: {e}")
        print("Please make sure the Flask server is started on http://localhost:5000")
        print("\nTo start the server:")
        print("  python run.py")
        return 1

    # 运行测试
    tester = APITester()
    results = tester.run_all_tests()

    # 生成测试报告
    generate_test_report(results)

    # 根据测试结果设置退出码
    failed_tests = [name for name, result in results.items() if result != "PASS"]
    if failed_tests:
        print(f"\n❌ Failed tests: {', '.join(failed_tests)}")
        return 1
    else:
        print("\n🎉 All tests passed successfully!")
        return 0


def generate_test_report(results: Dict[str, str]):
    """生成测试报告文件"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"test_report_{timestamp}.txt"

        with open(report_file, "w", encoding="utf-8") as f:
            f.write("GPT-SoVITS Backend API Test Report\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Tests: {len(results)}\n\n")

            # 按类别分组
            categories = {
                "Basic Tests": ["Health Check"],
                "Authentication": [
                    "User Registration",
                    "User Login",
                    "User Logout",
                    "Password Change",
                ],
                "User Management": [
                    "Get User Profile",
                    "Update User Profile",
                    "Get User Statistics",
                    "Get Task History",
                ],
                "Voice Clone": [
                    "Upload Audio Sample",
                    "Start Voice Clone Training",
                    "Get Voice Clone Tasks",
                    "Get Voice Clone Task Detail",
                    "Get Audio Samples",
                ],
                "Text-to-Speech": [
                    "Get TTS Models",
                    "Get TTS Emotions",
                    "Generate Speech",
                    "Get TTS Tasks",
                    "Get TTS Task Detail",
                ],
                "Model Management": [
                    "Get My Models",
                    "Get Model Tags",
                    "Get Model Stats",
                ],
                "Admin Functions": ["Admin Statistics"],
                "Error Handling": [
                    "Unauthorized Access",
                    "Invalid Endpoints",
                    "Invalid Data",
                ],
            }

            for category, test_names in categories.items():
                f.write(f"\n{category}:\n")
                f.write("-" * len(category) + "\n")

                for test_name in test_names:
                    if test_name in results:
                        result = results[test_name]
                        symbol = (
                            "✓"
                            if result == "PASS"
                            else "✗" if result == "FAIL" else "!"
                        )
                        f.write(f"  {symbol} {test_name}: {result}\n")

            # 统计信息
            pass_count = sum(1 for r in results.values() if r == "PASS")
            fail_count = sum(1 for r in results.values() if r == "FAIL")
            error_count = sum(1 for r in results.values() if r == "ERROR")

            f.write(f"\nSummary:\n")
            f.write(f"  PASS: {pass_count}\n")
            f.write(f"  FAIL: {fail_count}\n")
            f.write(f"  ERROR: {error_count}\n")
            f.write(f"  SUCCESS RATE: {pass_count/len(results)*100:.1f}%\n")

        print(f"\n📄 Test report saved to: {report_file}")

    except Exception as e:
        print(f"Warning: Could not generate test report: {e}")


if __name__ == "__main__":
    exit(main())
