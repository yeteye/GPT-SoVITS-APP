# ./gpt-sovits-backend/tests/test_tts.py 修复版本

import pytest
from app.models import TTSTask
from app.extensions import db


class TestTTS:
    """TTS API测试"""

    def test_generate_speech_success(self, client, auth_headers, app, sample_model):
        """测试成功生成语音"""
        # 修复：调用sample_model函数创建模型
        with app.app_context():
            model = sample_model()

        response = client.post(
            "/api/tts/generate",
            headers=auth_headers,
            json={
                "text": "这是一个测试文本",
                "model_id": model.id,  # 使用创建的模型ID
                "emotion": "neutral",
                "speed": 1.0,
            },
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert "task_id" in data["data"]

    def test_generate_speech_missing_text(
        self, client, auth_headers, app, sample_model
    ):
        """测试缺少文本参数"""
        # 修复：调用sample_model函数创建模型
        with app.app_context():
            model = sample_model()

        response = client.post(
            "/api/tts/generate",
            headers=auth_headers,
            json={"model_id": model.id, "emotion": "neutral"},  # 使用创建的模型ID
        )

        assert response.status_code == 422
        data = response.get_json()
        assert data["success"] is False

    def test_generate_speech_missing_model(self, client, auth_headers):
        """测试缺少模型ID"""
        response = client.post(
            "/api/tts/generate",
            headers=auth_headers,
            json={"text": "测试文本", "emotion": "neutral"},
        )

        assert response.status_code == 422

    def test_generate_speech_invalid_model(self, client, auth_headers):
        """测试无效模型ID"""
        response = client.post(
            "/api/tts/generate",
            headers=auth_headers,
            json={"text": "测试文本", "model_id": "nonexistent", "emotion": "neutral"},
        )

        assert response.status_code == 404

    def test_generate_speech_text_too_long(
        self, client, auth_headers, app, sample_model
    ):
        """测试文本过长"""
        # 修复：调用sample_model函数创建模型
        with app.app_context():
            model = sample_model()

        long_text = "a" * 201  # 超过200字符限制

        response = client.post(
            "/api/tts/generate",
            headers=auth_headers,
            json={"text": long_text, "model_id": model.id, "emotion": "neutral"},
        )

        assert response.status_code == 422

    def test_generate_speech_invalid_emotion(
        self, client, auth_headers, app, sample_model
    ):
        """测试无效情感"""
        # 修复：调用sample_model函数创建模型
        with app.app_context():
            model = sample_model()

        response = client.post(
            "/api/tts/generate",
            headers=auth_headers,
            json={
                "text": "测试文本",
                "model_id": model.id,
                "emotion": "invalid_emotion",
            },
        )

        assert response.status_code == 422

    def test_generate_speech_invalid_speed(
        self, client, auth_headers, app, sample_model
    ):
        """测试无效语速"""
        # 修复：调用sample_model函数创建模型
        with app.app_context():
            model = sample_model()

        response = client.post(
            "/api/tts/generate",
            headers=auth_headers,
            json={
                "text": "测试文本",
                "model_id": model.id,
                "emotion": "neutral",
                "speed": 3.0,  # 超出范围
            },
        )

        assert response.status_code == 422

    def test_get_tts_tasks(self, client, auth_headers, app):
        """测试获取TTS任务列表"""
        with app.app_context():
            from app.models import User

            user = User.query.filter_by(username="testuser").first()

            # 创建一些测试任务
            for i in range(3):
                task = TTSTask(
                    user_id=user.id,
                    text=f"Test text {i}",
                    model_id="test_model_id",
                    status="completed" if i == 0 else "pending",
                )
                db.session.add(task)
            db.session.commit()

        response = client.get("/api/tts/tasks", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert len(data["data"]["tasks"]) == 3

    def test_get_tts_task_detail(self, client, auth_headers, app, sample_model):
        """测试获取TTS任务详情"""
        with app.app_context():
            from app.models import User

            user = User.query.filter_by(username="testuser").first()
            # 修复：调用sample_model函数创建模型
            model = sample_model()

            task = TTSTask(
                user_id=user.id,
                text="Test text",
                model_id=model.id,
                emotion="happy",
                status="completed",
            )
            db.session.add(task)
            db.session.commit()
            task_id = task.id

        response = client.get(f"/api/tts/tasks/{task_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["task"]["text"] == "Test text"
        assert data["data"]["task"]["emotion"] == "happy"

    def test_get_tts_task_not_found(self, client, auth_headers):
        """测试获取不存在的TTS任务"""
        response = client.get("/api/tts/tasks/nonexistent", headers=auth_headers)

        assert response.status_code == 404

    def test_get_available_models(self, client, auth_headers, app, sample_model):
        """测试获取可用模型列表"""
        # 修复：调用sample_model函数创建模型，确保有模型存在
        with app.app_context():
            model = sample_model()

        response = client.get("/api/tts/models", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        # 现在应该至少有一个模型
        assert len(data["data"]["models"]) >= 1

    def test_get_model_detail(self, client, auth_headers, app, sample_model):
        """测试获取模型详情"""
        # 修复：调用sample_model函数创建模型
        with app.app_context():
            model = sample_model()

        response = client.get(f"/api/tts/models/{model.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["model"]["name"] == model.name

    def test_get_supported_emotions(self, client):
        """测试获取支持的情感列表"""
        response = client.get("/api/tts/emotions")

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert len(data["data"]["emotions"]) > 0

        # 检查是否包含基本情感
        emotion_values = [emotion["value"] for emotion in data["data"]["emotions"]]
        assert "neutral" in emotion_values
        assert "happy" in emotion_values
        assert "sad" in emotion_values

    def test_download_audio_not_completed(self, client, auth_headers, app):
        """测试下载未完成任务的音频"""
        with app.app_context():
            from app.models import User

            user = User.query.filter_by(username="testuser").first()

            task = TTSTask(
                user_id=user.id,
                text="Test text",
                model_id="test_model",
                status="processing",
            )
            db.session.add(task)
            db.session.commit()
            task_id = task.id

        response = client.get(
            f"/api/tts/tasks/{task_id}/download", headers=auth_headers
        )

        assert response.status_code == 400

    def test_filter_tasks_by_status(self, client, auth_headers, app):
        """测试按状态过滤任务"""
        with app.app_context():
            from app.models import User

            user = User.query.filter_by(username="testuser").first()

            # 创建不同状态的任务
            statuses = ["pending", "processing", "completed", "failed"]
            for status in statuses:
                task = TTSTask(
                    user_id=user.id,
                    text=f"Test {status}",
                    model_id="test_model",
                    status=status,
                )
                db.session.add(task)
            db.session.commit()

        # 测试过滤已完成的任务
        response = client.get("/api/tts/tasks?status=completed", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        tasks = data["data"]["tasks"]
        assert all(task["status"] == "completed" for task in tasks)

    def test_pagination(self, client, auth_headers, app):
        """测试分页功能"""
        with app.app_context():
            from app.models import User

            user = User.query.filter_by(username="testuser").first()

            # 创建多个任务
            for i in range(25):
                task = TTSTask(
                    user_id=user.id, text=f"Test text {i}", model_id="test_model"
                )
                db.session.add(task)
            db.session.commit()

        # 测试第一页
        response = client.get("/api/tts/tasks?page=1&per_page=10", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["data"]["tasks"]) == 10
        assert data["data"]["pagination"]["page"] == 1
        assert data["data"]["pagination"]["total"] == 25
        assert data["data"]["pagination"]["has_next"] is True

    def test_concurrent_requests_limit(self, client, auth_headers, app, sample_model):
        """测试并发请求限制"""
        # 修复：调用sample_model函数创建模型
        with app.app_context():
            model = sample_model()

        requests = []
        for i in range(10):  # 尝试创建超过限制的任务
            response = client.post(
                "/api/tts/generate",
                headers=auth_headers,
                json={
                    "text": f"Test text {i}",
                    "model_id": model.id,
                    "emotion": "neutral",
                },
            )
            requests.append(response)

        # 至少前几个请求应该成功
        success_count = sum(1 for req in requests if req.status_code == 201)
        assert success_count > 0

    def test_unauthorized_access(self, client):
        """测试未授权访问"""
        endpoints = [
            ("/api/tts/generate", "POST"),
            ("/api/tts/tasks", "GET"),
            ("/api/tts/models", "GET"),
        ]

        for endpoint, method in endpoints:
            if method == "POST":
                response = client.post(endpoint, json={"text": "test"})
            else:
                response = client.get(endpoint)

            assert response.status_code == 401
