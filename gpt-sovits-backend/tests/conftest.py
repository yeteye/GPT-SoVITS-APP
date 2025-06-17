# ./gpt-sovits-backend/tests/conftest.py
import pytest
import tempfile
import os
import io
import struct
from datetime import datetime

# 设置环境变量，确保使用测试配置
os.environ["FLASK_CONFIG"] = "testing"
os.environ["TESTING"] = "True"

from app import create_app
from app.extensions import db
from app.models import User, VoiceModel, Tag, VoiceCloneTask, TTSTask, UserUpload


@pytest.fixture(scope="session")
def app():
    """创建测试应用实例"""
    # 创建临时数据库文件
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    # 创建临时上传目录
    upload_dir = tempfile.mkdtemp()

    # 创建测试配置
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "pool_pre_ping": True,
            "pool_recycle": -1,
            "echo": False,
        },
        "WTF_CSRF_ENABLED": False,
        "JWT_SECRET_KEY": "test-jwt-secret-key-for-testing",
        "SECRET_KEY": "test-secret-key-for-testing",
        "UPLOAD_FOLDER": upload_dir,
        "MAX_CONTENT_LENGTH": 10 * 1024 * 1024,  # 10MB
        "ALLOWED_AUDIO_EXTENSIONS": {"wav", "mp3", "flac", "m4a"},
        "ALLOWED_MODEL_EXTENSIONS": {"pth", "json", "index"},
        # 禁用外部服务以避免错误
        "CELERY_BROKER_URL": None,
        "CELERY_RESULT_BACKEND": None,
        "REDIS_URL": None,
        "MAIL_SERVER": None,
        "MAIL_USERNAME": None,
        "MAIL_PASSWORD": None,
        "MAIL_USE_TLS": False,
        "MAIL_DEFAULT_SENDER": None,
        # 音频处理配置
        "AUDIO_SAMPLE_RATE": 16000,
        "AUDIO_MIN_DURATION": 1,
        "AUDIO_MAX_DURATION": 60,
        "MAX_CONCURRENT_TASKS": 5,
        # 路径配置
        "SOVITS_MODEL_PATH": upload_dir,
        "GPT_MODEL_PATH": upload_dir,
        "LOG_LEVEL": "WARNING",
        # 分页配置
        "ITEMS_PER_PAGE": 20,
    }

    # 创建应用
    app = create_app("testing")
    app.config.update(test_config)

    with app.app_context():
        try:
            # 创建数据库表
            db.create_all()

            # 创建上传目录结构
            upload_subdirs = [
                "audio_samples",
                "models/official",
                "models/user_trained",
                "generated",
                "temp",
                "images",
                "documents",
            ]
            for subdir in upload_subdirs:
                os.makedirs(os.path.join(upload_dir, subdir), exist_ok=True)

            yield app

        finally:
            # 清理数据库
            try:
                db.drop_all()
            except:
                pass

    # 清理临时文件
    try:
        os.close(db_fd)
        os.unlink(db_path)
        import shutil

        shutil.rmtree(upload_dir, ignore_errors=True)
    except:
        pass


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """创建测试用户 - 返回对象而不是函数"""
    with app.app_context():
        user = User(
            username="testuser",
            email="test@example.com",
            is_active=True,
            is_verified=True,
            role=0,
        )
        user.set_password("testpassword123")
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user


@pytest.fixture
def admin_user(app):
    """创建管理员用户 - 返回对象而不是函数"""
    with app.app_context():
        admin = User(
            username="admin",
            email="admin@example.com",
            role=2,
            is_active=True,
            is_verified=True,
        )
        admin.set_password("adminpassword123")
        db.session.add(admin)
        db.session.commit()
        db.session.refresh(admin)
        return admin


@pytest.fixture
def sample_tags(app):
    """创建示例标签 - 返回对象列表"""
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

        for tag in tags:
            db.session.refresh(tag)

        return tags


@pytest.fixture
def sample_model(app, admin_user, sample_tags):
    """创建示例模型 - 返回对象而不是函数"""
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

        model.set_supported_emotions(["neutral", "happy", "sad", "calm"])
        model.set_supported_languages(["zh-CN", "en-US"])

        if sample_tags:
            model.tags.extend(sample_tags[:2])

        db.session.add(model)
        db.session.commit()
        db.session.refresh(model)
        return model


@pytest.fixture
def auth_headers(client, test_user):
    """获取认证头部"""
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


# Mock 邮件发送以避免错误
@pytest.fixture(autouse=True)
def mock_mail(monkeypatch):
    """Mock邮件服务以避免测试时发送真实邮件"""

    def mock_send_mail(*args, **kwargs):
        return True

    # Mock Flask-Mail的send方法
    try:
        from flask_mail import Mail

        monkeypatch.setattr("flask_mail.Mail.send", mock_send_mail)
    except ImportError:
        pass

    # Mock我们自己的邮件发送函数
    monkeypatch.setattr("app.auth.utils.send_verification_email", lambda *args: True)
    monkeypatch.setattr("app.auth.utils.send_password_reset_email", lambda *args: True)
    monkeypatch.setattr("app.auth.utils.send_welcome_email", lambda *args: True)


# Mock Redis 以避免速率限制警告
@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    """Mock Redis以避免速率限制相关错误"""

    class MockRedis:
        def get(self, key):
            return None

        def setex(self, key, timeout, value):
            return True

        def incr(self, key):
            return 1

        def delete(self, key):
            return True

        def ping(self):
            return True

    # Mock redis_client
    monkeypatch.setattr("app.extensions.redis_client", MockRedis())


# Mock Celery 任务 - 修复调用方式
@pytest.fixture(autouse=True)
def mock_celery(monkeypatch):
    """Mock Celery任务以避免异步处理错误"""

    class MockCeleryTask:
        def __init__(self, task_id="mock-task-id"):
            self.id = task_id

        def delay(self, task_id):  # 修复：只接受task_id参数
            return self

        def apply_async(self, task_id):  # 修复：只接受task_id参数
            return self

    # Mock Celery任务
    mock_task = MockCeleryTask()
    monkeypatch.setattr(
        "app.services.voice_clone_service.start_voice_clone_task.delay",
        lambda task_id: mock_task,
    )
    monkeypatch.setattr(
        "app.services.tts_service.generate_speech_task.delay",
        lambda task_id: mock_task,
    )


# 其余 fixtures 保持不变...
def create_wav_file(duration=1.0, sample_rate=16000, frequency=440):
    """创建WAV格式的音频文件"""
    import numpy as np

    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = (np.sin(2 * np.pi * frequency * t) * 0.3 * 32767).astype(np.int16)

    wav_file = io.BytesIO()

    wav_file.write(b"RIFF")
    wav_file.write(struct.pack("<I", 36 + len(audio_data) * 2))
    wav_file.write(b"WAVE")
    wav_file.write(b"fmt ")
    wav_file.write(struct.pack("<I", 16))
    wav_file.write(struct.pack("<H", 1))
    wav_file.write(struct.pack("<H", 1))
    wav_file.write(struct.pack("<I", sample_rate))
    wav_file.write(struct.pack("<I", sample_rate * 2))
    wav_file.write(struct.pack("<H", 2))
    wav_file.write(struct.pack("<H", 16))
    wav_file.write(b"data")
    wav_file.write(struct.pack("<I", len(audio_data) * 2))

    wav_file.write(audio_data.tobytes())
    wav_file.seek(0)

    return wav_file


@pytest.fixture
def sample_audio_file(app):
    """创建示例音频文件 - 返回临时文件路径"""
    with app.app_context():
        # 创建临时文件
        fd, temp_path = tempfile.mkstemp(suffix=".wav")

        # 创建音频数据
        audio_data = create_wav_file()

        # 写入临时文件
        with os.fdopen(fd, "wb") as f:
            f.write(audio_data.getvalue())

        yield temp_path

        # 清理临时文件
        try:
            os.unlink(temp_path)
        except:
            pass


@pytest.fixture
def sample_audio_bytesio():
    """创建BytesIO音频文件对象"""
    return create_wav_file()


@pytest.fixture
def sample_upload(app, test_user, sample_audio_bytesio):
    """创建示例上传记录"""
    with app.app_context():
        upload = UserUpload(
            user_id=test_user.id,
            filename="test_sample.wav",
            original_filename="test_sample.wav",
            file_path="/test/path/test_sample.wav",
            file_size=len(sample_audio_bytesio.getvalue()),
            file_type="audio",
            mime_type="audio/wav",
        )

        upload.set_metadata({"duration": 1.0, "sample_rate": 16000, "channels": 1})

        db.session.add(upload)
        db.session.commit()
        db.session.refresh(upload)
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

        task.set_audio_samples([sample_upload.file_path])
        task.set_config(
            {"model_name": "Test Cloned Voice", "training_params": {"epochs": 100}}
        )

        db.session.add(task)
        db.session.commit()
        db.session.refresh(task)
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
        db.session.refresh(task)
        return task


@pytest.fixture(autouse=True)
def setup_db(app):
    """每个测试前后设置数据库"""
    with app.app_context():
        db.create_all()
        yield

        try:
            # 清理数据但保留表结构
            for table in reversed(db.metadata.sorted_tables):
                db.session.execute(table.delete())
            db.session.commit()
        except Exception:
            try:
                db.session.rollback()
            except:
                pass


@pytest.fixture
def test_data_factory():
    """测试数据工厂"""

    class TestDataFactory:
        @staticmethod
        def create_user_data(username="testuser", email="test@example.com"):
            return {
                "username": username,
                "email": email,
                "password": "TestPassword123!",
            }

        @staticmethod
        def create_model_data(name="Test Model"):
            return {
                "name": name,
                "description": "A test model",
                "voice_characteristics": "Clear and natural voice",
                "supported_emotions": ["neutral", "happy"],
                "supported_languages": ["zh-CN"],
            }

        @staticmethod
        def create_tts_data(text="测试文本", model_id=None):
            return {
                "text": text,
                "model_id": model_id,
                "emotion": "neutral",
                "speed": 1.0,
            }

    return TestDataFactory
