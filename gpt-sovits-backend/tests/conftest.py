# ./gpt-sovits-backend/tests/conftest.py
import pytest
import tempfile
import os
import io
import struct
from datetime import datetime
from app import create_app
from app.extensions import db
from app.models import User, VoiceModel, Tag, VoiceCloneTask, TTSTask, UserUpload


@pytest.fixture(scope="session")
def app():
    """创建测试应用实例"""
    # 创建临时数据库
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    # 创建临时上传目录
    upload_dir = tempfile.mkdtemp()

    # 创建测试配置
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "WTF_CSRF_ENABLED": False,
        "JWT_SECRET_KEY": "test-jwt-secret",
        "SECRET_KEY": "test-secret-key",
        "UPLOAD_FOLDER": upload_dir,
        "MAX_CONTENT_LENGTH": 10 * 1024 * 1024,
        "ALLOWED_AUDIO_EXTENSIONS": {"wav", "mp3", "flac"},
        "CELERY_BROKER_URL": None,  # 禁用Celery
        "CELERY_RESULT_BACKEND": None,  # 禁用Celery
        "REDIS_URL": None,  # 禁用Redis
        "MAIL_SERVER": None,  # 禁用邮件
        "MAIL_USERNAME": None,
        "AUDIO_SAMPLE_RATE": 16000,
        "AUDIO_MIN_DURATION": 1,
        "AUDIO_MAX_DURATION": 60,
        "MAX_CONCURRENT_TASKS": 5,
        # 添加其他测试必需的配置
        "SOVITS_MODEL_PATH": upload_dir,
        "GPT_MODEL_PATH": upload_dir,
        "LOG_LEVEL": "WARNING",  # 减少测试期间的日志输出
    }

    # 创建应用
    app = create_app("testing")
    app.config.update(test_config)

    with app.app_context():
        # 创建数据库表
        db.create_all()

        # 创建上传目录结构
        upload_subdirs = ["audio_samples", "models", "generated", "temp"]
        for subdir in upload_subdirs:
            os.makedirs(os.path.join(upload_dir, subdir), exist_ok=True)

        yield app

        # 清理
        db.drop_all()

    # 删除临时文件
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """创建CLI测试运行器"""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """创建测试用户"""
    with app.app_context():
        user = User(
            username="testuser",
            email="test@example.com",
            is_active=True,
            is_verified=True,
            role=0,  # 普通用户
        )
        user.set_password("testpassword123")
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def admin_user(app):
    """创建管理员用户"""
    with app.app_context():
        admin = User(
            username="admin",
            email="admin@example.com",
            role=2,  # 管理员
            is_active=True,
            is_verified=True,
        )
        admin.set_password("adminpassword123")
        db.session.add(admin)
        db.session.commit()
        return admin


@pytest.fixture
def auditor_user(app):
    """创建审核员用户"""
    with app.app_context():
        auditor = User(
            username="auditor",
            email="auditor@example.com",
            role=1,  # 审核员
            is_active=True,
            is_verified=True,
        )
        auditor.set_password("auditorpassword123")
        db.session.add(auditor)
        db.session.commit()
        return auditor


@pytest.fixture
def auth_headers(client, test_user):
    """获取认证头部"""
    # 登录获取token
    response = client.post(
        "/api/auth/login",
        json={"identifier": test_user.username, "password": "testpassword123"},
    )

    assert response.status_code == 200
    data = response.get_json()
    token = data["data"]["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client, admin_user):
    """获取管理员认证头部"""
    response = client.post(
        "/api/auth/login",
        json={"identifier": admin_user.username, "password": "adminpassword123"},
    )

    assert response.status_code == 200
    data = response.get_json()
    token = data["data"]["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_tags(app):
    """创建示例标签"""
    with app.app_context():
        tags_data = [
            {"name": "女声", "description": "女性声音", "color": "#ff69b4"},
            {"name": "男声", "description": "男性声音", "color": "#4169e1"},
            {"name": "温柔", "description": "温柔的声音", "color": "#ffc0cb"},
            {"name": "官方", "description": "官方模型", "color": "#ffd700"},
        ]

        tags = []
        for tag_data in tags_data:
            tag = Tag(**tag_data)
            db.session.add(tag)
            tags.append(tag)

        db.session.commit()
        return tags


@pytest.fixture
def sample_model(app, admin_user, sample_tags):
    """创建示例模型"""
    with app.app_context():
        model = VoiceModel(
            name="Test Voice Model",
            description="A test voice model for testing purposes",
            model_type="official",
            model_path="/test/path/model.pth",
            config_path="/test/path/config.json",
            status="active",
            is_public=True,
            is_featured=True,
            quality_score=8.5,
            review_status="approved",
            reviewed_by=admin_user.id,
            reviewed_at=datetime.utcnow(),
        )

        # 设置支持的情感和语言
        model.set_supported_emotions(["neutral", "happy", "sad", "calm"])
        model.set_supported_languages(["zh-CN", "en-US"])

        # 添加标签
        if sample_tags:
            model.tags.extend(sample_tags[:2])

        db.session.add(model)
        db.session.commit()
        return model


@pytest.fixture
def user_model(app, test_user):
    """创建用户模型"""
    with app.app_context():
        model = VoiceModel(
            name="User Test Model",
            description="A user's test model",
            model_type="user_trained",
            model_path="/test/user/model.pth",
            owner_id=test_user.id,
            status="active",
            is_public=False,
            quality_score=7.0,
        )

        model.set_supported_emotions(["neutral", "happy"])
        model.set_supported_languages(["zh-CN"])

        db.session.add(model)
        db.session.commit()
        return model


@pytest.fixture
def sample_audio_file():
    """创建示例音频文件"""

    def create_wav_file(duration=1.0, sample_rate=16000, frequency=440):
        """创建WAV格式的音频文件"""
        import numpy as np

        # 生成音频数据
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = (np.sin(2 * np.pi * frequency * t) * 0.3 * 32767).astype(np.int16)

        # 创建WAV文件
        wav_file = io.BytesIO()

        # WAV文件头
        wav_file.write(b"RIFF")
        wav_file.write(struct.pack("<I", 36 + len(audio_data) * 2))
        wav_file.write(b"WAVE")
        wav_file.write(b"fmt ")
        wav_file.write(struct.pack("<I", 16))  # fmt chunk大小
        wav_file.write(struct.pack("<H", 1))  # PCM格式
        wav_file.write(struct.pack("<H", 1))  # 单声道
        wav_file.write(struct.pack("<I", sample_rate))
        wav_file.write(struct.pack("<I", sample_rate * 2))  # 字节率
        wav_file.write(struct.pack("<H", 2))  # 块对齐
        wav_file.write(struct.pack("<H", 16))  # 位深度
        wav_file.write(b"data")
        wav_file.write(struct.pack("<I", len(audio_data) * 2))

        # 音频数据
        wav_file.write(audio_data.tobytes())
        wav_file.seek(0)

        return wav_file

    return create_wav_file


@pytest.fixture
def sample_upload(app, test_user, sample_audio_file):
    """创建示例上传记录"""
    with app.app_context():
        # 创建音频文件
        audio_file = sample_audio_file()

        upload = UserUpload(
            user_id=test_user.id,
            filename="test_sample.wav",
            original_filename="test_sample.wav",
            file_path="/test/path/test_sample.wav",
            file_size=len(audio_file.getvalue()),
            file_type="audio",
            mime_type="audio/wav",
        )

        # 设置音频元数据
        upload.set_metadata({"duration": 1.0, "sample_rate": 16000, "channels": 1})

        db.session.add(upload)
        db.session.commit()
        return upload


@pytest.fixture
def sample_voice_clone_task(app, test_user, sample_upload):
    """创建示例语音克隆任务"""
    with app.app_context():
        task = VoiceCloneTask(
            user_id=test_user.id,
            task_name="Test Voice Clone",
            status="completed",
            progress=100,
            sample_count=3,
            total_duration=15.0,
            model_name="Test Cloned Voice",
        )

        # 设置音频样本路径
        task.set_audio_samples([sample_upload.file_path])
        task.set_config(
            {"model_name": "Test Cloned Voice", "training_params": {"epochs": 100}}
        )

        db.session.add(task)
        db.session.commit()
        return task


@pytest.fixture
def sample_tts_task(app, test_user, sample_model):
    """创建示例TTS任务"""
    with app.app_context():
        task = TTSTask(
            user_id=test_user.id,
            text="这是一个测试文本",
            model_id=sample_model.id,
            emotion="neutral",
            speed=1.0,
            status="completed",
            audio_path="/test/generated/audio.wav",
            audio_url="/api/download/audio.wav",
            audio_duration=3.5,
        )

        db.session.add(task)
        db.session.commit()
        return task


@pytest.fixture(autouse=True)
def clean_db(app):
    """每个测试后清理数据库"""
    yield
    with app.app_context():
        # 清理所有表数据，但保留表结构
        db.session.remove()
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()


@pytest.fixture
def mock_celery_task():
    """模拟Celery任务"""

    class MockTask:
        def __init__(self, task_id="mock-task-id"):
            self.id = task_id

        def delay(self, *args, **kwargs):
            return self

        def apply_async(self, *args, **kwargs):
            return self

    return MockTask


# 测试数据生成器
class TestDataFactory:
    """测试数据工厂"""

    @staticmethod
    def create_user_data(username="testuser", email="test@example.com"):
        """创建用户数据"""
        return {"username": username, "email": email, "password": "TestPassword123!"}

    @staticmethod
    def create_model_data(name="Test Model"):
        """创建模型数据"""
        return {
            "name": name,
            "description": "A test model",
            "voice_characteristics": "Clear and natural voice",
            "supported_emotions": ["neutral", "happy"],
            "supported_languages": ["zh-CN"],
        }

    @staticmethod
    def create_tts_data(text="测试文本", model_id=None):
        """创建TTS请求数据"""
        return {"text": text, "model_id": model_id, "emotion": "neutral", "speed": 1.0}


@pytest.fixture
def test_data_factory():
    """提供测试数据工厂"""
    return TestDataFactory
