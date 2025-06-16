# ./gpt-sovits-backend/tests/test_voice_clone.py
import pytest
import io
import os
from app.models import VoiceCloneTask, UserUpload
from app.extensions import db


class TestVoiceClone:
    """语音克隆API测试"""

    def test_upload_audio_sample_success(self, client, auth_headers, sample_audio_file):
        """测试成功上传音频样本"""
        with open(sample_audio_file, "rb") as f:
            response = client.post(
                "/api/voice-clone/upload-sample",
                headers=auth_headers,
                data={"audio_file": (f, "test.wav")},
                content_type="multipart/form-data",
            )

        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert "upload_id" in data["data"]
        assert "duration" in data["data"]

    def test_upload_audio_sample_no_file(self, client, auth_headers):
        """测试上传时没有文件"""
        response = client.post(
            "/api/voice-clone/upload-sample",
            headers=auth_headers,
            data={},
            content_type="multipart/form-data",
        )

        assert response.status_code == 422
        data = response.get_json()
        assert data["success"] is False

    def test_upload_audio_sample_invalid_format(self, client, auth_headers):
        """测试上传无效格式文件"""
        # 创建一个文本文件伪装成音频文件
        fake_audio = io.BytesIO(b"This is not audio data")

        response = client.post(
            "/api/voice-clone/upload-sample",
            headers=auth_headers,
            data={"audio_file": (fake_audio, "test.txt")},
            content_type="multipart/form-data",
        )

        assert response.status_code == 422

    def test_start_training_success(self, client, auth_headers, app):
        """测试成功启动训练"""
        with app.app_context():
            # 先创建一些音频上传记录
            from app.models import User

            user = User.query.filter_by(username="testuser").first()

            # 创建模拟的音频上传记录
            uploads = []
            for i in range(3):
                upload = UserUpload(
                    user_id=user.id,
                    filename=f"sample_{i}.wav",
                    original_filename=f"sample_{i}.wav",
                    file_path=f"/test/path/sample_{i}.wav",
                    file_size=1024,
                    file_type="audio",
                    mime_type="audio/wav",
                )
                upload.set_metadata({"duration": 5.0, "sample_rate": 16000})
                db.session.add(upload)
                uploads.append(upload)

            db.session.commit()

            sample_ids = [upload.id for upload in uploads]

        response = client.post(
            "/api/voice-clone/start-training",
            headers=auth_headers,
            json={"model_name": "Test Voice Model", "sample_ids": sample_ids},
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert "task_id" in data["data"]

    def test_start_training_insufficient_samples(self, client, auth_headers):
        """测试样本不足时启动训练"""
        response = client.post(
            "/api/voice-clone/start-training",
            headers=auth_headers,
            json={"model_name": "Test Model", "sample_ids": ["sample1"]},  # 少于3个样本
        )

        assert response.status_code == 422
        data = response.get_json()
        assert data["success"] is False

    def test_start_training_invalid_model_name(self, client, auth_headers):
        """测试无效模型名称"""
        response = client.post(
            "/api/voice-clone/start-training",
            headers=auth_headers,
            json={"model_name": "", "sample_ids": ["1", "2", "3"]},  # 空名称
        )

        assert response.status_code == 422

    def test_get_user_tasks(self, client, auth_headers, app):
        """测试获取用户任务列表"""
        with app.app_context():
            from app.models import User

            user = User.query.filter_by(username="testuser").first()

            # 创建一些测试任务
            for i in range(3):
                task = VoiceCloneTask(
                    user_id=user.id,
                    task_name=f"Task {i}",
                    status="completed" if i == 0 else "pending",
                )
                db.session.add(task)
            db.session.commit()

        response = client.get("/api/voice-clone/tasks", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert len(data["data"]["tasks"]) == 3

    def test_get_task_detail(self, client, auth_headers, app):
        """测试获取任务详情"""
        with app.app_context():
            from app.models import User

            user = User.query.filter_by(username="testuser").first()

            task = VoiceCloneTask(
                user_id=user.id, task_name="Test Task", status="completed"
            )
            db.session.add(task)
            db.session.commit()
            task_id = task.id

        response = client.get(f"/api/voice-clone/tasks/{task_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["task"]["task_name"] == "Test Task"

    def test_get_task_detail_not_found(self, client, auth_headers):
        """测试获取不存在的任务详情"""
        response = client.get(
            "/api/voice-clone/tasks/nonexistent", headers=auth_headers
        )

        assert response.status_code == 404

    def test_cancel_task(self, client, auth_headers, app):
        """测试取消任务"""
        with app.app_context():
            from app.models import User

            user = User.query.filter_by(username="testuser").first()

            task = VoiceCloneTask(
                user_id=user.id, task_name="Cancellable Task", status="processing"
            )
            db.session.add(task)
            db.session.commit()
            task_id = task.id

        response = client.post(
            f"/api/voice-clone/tasks/{task_id}/cancel", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    def test_cancel_completed_task(self, client, auth_headers, app):
        """测试取消已完成的任务"""
        with app.app_context():
            from app.models import User

            user = User.query.filter_by(username="testuser").first()

            task = VoiceCloneTask(
                user_id=user.id, task_name="Completed Task", status="completed"
            )
            db.session.add(task)
            db.session.commit()
            task_id = task.id

        response = client.post(
            f"/api/voice-clone/tasks/{task_id}/cancel", headers=auth_headers
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_get_user_samples(self, client, auth_headers, app):
        """测试获取用户音频样本"""
        with app.app_context():
            from app.models import User

            user = User.query.filter_by(username="testuser").first()

            # 创建一些音频上传记录
            for i in range(2):
                upload = UserUpload(
                    user_id=user.id,
                    filename=f"sample_{i}.wav",
                    original_filename=f"sample_{i}.wav",
                    file_path=f"/test/sample_{i}.wav",
                    file_size=1024,
                    file_type="audio",
                )
                db.session.add(upload)
            db.session.commit()

        response = client.get("/api/voice-clone/samples", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert len(data["data"]["samples"]) == 2

    def test_delete_sample(self, client, auth_headers, app):
        """测试删除音频样本"""
        with app.app_context():
            from app.models import User

            user = User.query.filter_by(username="testuser").first()

            upload = UserUpload(
                user_id=user.id,
                filename="sample.wav",
                original_filename="sample.wav",
                file_path="/test/sample.wav",
                file_size=1024,
                file_type="audio",
            )
            db.session.add(upload)
            db.session.commit()
            sample_id = upload.id

        response = client.delete(
            f"/api/voice-clone/samples/{sample_id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    def test_retry_failed_task(self, client, auth_headers, app):
        """测试重试失败的任务"""
        with app.app_context():
            from app.models import User

            user = User.query.filter_by(username="testuser").first()

            task = VoiceCloneTask(
                user_id=user.id,
                task_name="Failed Task",
                status="failed",
                error_message="Test error",
            )
            db.session.add(task)
            db.session.commit()
            task_id = task.id

        response = client.post(
            f"/api/voice-clone/tasks/{task_id}/retry", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    def test_unauthorized_access(self, client):
        """测试未授权访问"""
        endpoints = [
            "/api/voice-clone/tasks",
            "/api/voice-clone/samples",
            "/api/voice-clone/upload-sample",
            "/api/voice-clone/start-training",
        ]

        for endpoint in endpoints:
            if endpoint in [
                "/api/voice-clone/upload-sample",
                "/api/voice-clone/start-training",
            ]:
                response = client.post(endpoint)
            else:
                response = client.get(endpoint)

            assert response.status_code == 401
