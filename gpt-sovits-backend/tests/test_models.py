import pytest
from datetime import datetime
from app.models import User, VoiceModel, Tag, VoiceCloneTask, TTSTask
from app.extensions import db


class TestUserModel:
    """用户模型测试"""

    def test_user_creation(self, app):
        """测试用户创建"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.set_password("password123")

            db.session.add(user)
            db.session.commit()

            assert user.id is not None
            assert user.username == "testuser"
            assert user.email == "test@example.com"
            assert user.role == 0  # 默认普通用户
            assert user.is_active is True

    def test_password_hashing(self, app):
        """测试密码哈希"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.set_password("password123")

            # 密码应该被哈希
            assert user.password_hash != "password123"
            assert user.check_password("password123") is True
            assert user.check_password("wrongpassword") is False

    def test_user_roles(self, app):
        """测试用户角色"""
        with app.app_context():
            # 普通用户
            user = User(username="user", email="user@example.com", role=0)
            assert user.is_admin() is False
            assert user.is_auditor() is False

            # 审核员
            auditor = User(username="auditor", email="auditor@example.com", role=1)
            assert auditor.is_admin() is False
            assert auditor.is_auditor() is True

            # 管理员
            admin = User(username="admin", email="admin@example.com", role=2)
            assert admin.is_admin() is True
            assert admin.is_auditor() is True

    def test_user_to_dict(self, app):
        """测试用户字典转换"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.set_password("password123")
            db.session.add(user)
            db.session.commit()

            # 不包含敏感信息
            data = user.to_dict()
            assert "password_hash" not in data
            assert "email" not in data or data["email"] is None
            assert data["username"] == "testuser"

            # 包含敏感信息
            sensitive_data = user.to_dict(include_sensitive=True)
            assert sensitive_data["email"] == "test@example.com"


class TestVoiceModel:
    """语音模型测试"""

    def test_voice_model_creation(self, app):
        """测试语音模型创建"""
        with app.app_context():
            model = VoiceModel(
                name="Test Model",
                description="A test model",
                model_path="/test/path",
                model_type="user_trained",
            )

            db.session.add(model)
            db.session.commit()

            assert model.id is not None
            assert model.name == "Test Model"
            assert model.status == "active"
            assert model.is_public is False

    def test_supported_emotions(self, app):
        """测试支持的情感"""
        with app.app_context():
            model = VoiceModel(name="Test", model_path="/test")

            # 设置支持的情感
            emotions = ["happy", "sad", "neutral"]
            model.set_supported_emotions(emotions)

            # 获取支持的情感
            assert model.get_supported_emotions() == emotions

    def test_supported_languages(self, app):
        """测试支持的语言"""
        with app.app_context():
            model = VoiceModel(name="Test", model_path="/test")

            # 设置支持的语言
            languages = ["zh-CN", "en-US"]
            model.set_supported_languages(languages)

            # 获取支持的语言
            assert model.get_supported_languages() == languages

    def test_usage_increment(self, app):
        """测试使用次数增加"""
        with app.app_context():
            model = VoiceModel(name="Test", model_path="/test")
            db.session.add(model)
            db.session.commit()

            initial_count = model.usage_count
            model.increment_usage()

            assert model.usage_count == initial_count + 1

    def test_model_to_dict(self, app):
        """测试模型字典转换"""
        with app.app_context():
            # 创建带时间戳的模型
            model = VoiceModel(
                name="Test Model",
                model_path="/test/path",
                config_path="/test/config",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            model.set_supported_emotions(["happy", "sad"])

            db.session.add(model)
            db.session.commit()

            # 不包含路径
            data = model.to_dict(include_paths=False)
            assert "model_path" not in data
            assert data["supported_emotions"] == ["happy", "sad"]
            assert "created_at" in data
            assert "updated_at" in data

            # 包含路径
            path_data = model.to_dict(include_paths=True)
            assert path_data["model_path"] == "/test/path"


class TestTag:
    """标签测试"""

    def test_tag_creation(self, app):
        """测试标签创建"""
        with app.app_context():
            tag = Tag(name="女声", description="女性声音")
            db.session.add(tag)
            db.session.commit()

            assert tag.id is not None
            assert tag.name == "女声"
            assert tag.usage_count == 0

    def test_tag_get_or_create(self, app):
        """测试获取或创建标签"""
        with app.app_context():
            # 第一次调用，创建新标签
            tag1 = Tag.get_or_create("测试标签")
            assert tag1.name == "测试标签"

            # 第二次调用，获取已存在的标签
            tag2 = Tag.get_or_create("测试标签")
            assert tag1.id == tag2.id

    def test_tag_usage_increment(self, app):
        """测试标签使用次数增加"""
        with app.app_context():
            tag = Tag(name="测试")
            db.session.add(tag)
            db.session.commit()

            initial_count = tag.usage_count
            tag.increment_usage()

            assert tag.usage_count == initial_count + 1


class TestVoiceCloneTask:
    """语音克隆任务测试"""

    def test_task_creation(self, app, test_user):
        """测试任务创建"""
        with app.app_context():
            user = test_user

            task = VoiceCloneTask(
                user_id=user.id, task_name="Test Task", sample_count=5
            )
            db.session.add(task)
            db.session.commit()

            assert task.id is not None
            assert task.status == "pending"
            assert task.progress == 0

    def test_task_audio_samples(self, app):
        """测试音频样本设置"""
        with app.app_context():
            task = VoiceCloneTask(task_name="Test")

            samples = ["/path/1.wav", "/path/2.wav"]
            task.set_audio_samples(samples)

            assert task.get_audio_samples() == samples

    def test_task_config(self, app):
        """测试任务配置"""
        with app.app_context():
            task = VoiceCloneTask(task_name="Test")

            config = {"epochs": 100, "batch_size": 32}
            task.set_config(config)

            assert task.get_config() == config

    def test_task_status_update(self, app, test_user):
        """测试任务状态更新"""
        with app.app_context():
            user = test_user

            task = VoiceCloneTask(task_name="Test", user_id=user.id)
            db.session.add(task)
            db.session.commit()

            # 更新为处理中
            task.update_status("processing", progress=50)
            assert task.status == "processing"
            assert task.progress == 50
            assert task.started_at is not None

            # 更新为完成
            task.update_status("completed", progress=100)
            assert task.status == "completed"
            assert task.completed_at is not None

    def test_task_can_be_cancelled(self, app):
        """测试任务是否可以取消"""
        with app.app_context():
            task = VoiceCloneTask(task_name="Test")

            # 待处理状态可以取消
            task.status = "pending"
            assert task.can_be_cancelled() is True

            # 处理中状态可以取消
            task.status = "processing"
            assert task.can_be_cancelled() is True

            # 完成状态不能取消
            task.status = "completed"
            assert task.can_be_cancelled() is False

    def test_task_can_be_retried(self, app):
        """测试任务是否可以重试"""
        with app.app_context():
            task = VoiceCloneTask(task_name="Test")

            # 失败状态可以重试
            task.status = "failed"
            assert task.can_be_retried() is True

            # 完成状态不能重试
            task.status = "completed"
            assert task.can_be_retried() is False


class TestTTSTask:
    """TTS任务测试"""

    def test_tts_task_creation(self, app, test_user, sample_model):
        """测试TTS任务创建"""
        with app.app_context():
            user = test_user
            model = sample_model

            task = TTSTask(
                user_id=user.id,
                text="Hello world",
                model_id=model.id,
                emotion="happy",
            )
            db.session.add(task)
            db.session.commit()

            assert task.id is not None
            assert task.text == "Hello world"
            assert task.emotion == "happy"
            assert task.speed == 1.0

    def test_tts_task_set_result(self, app, test_user):
        """测试设置TTS结果"""
        with app.app_context():
            user = test_user

            task = TTSTask(text="Test", user_id=user.id, model_id="test_model")
            db.session.add(task)
            db.session.commit()

            task.set_result(
                audio_path="/test/audio.wav",
                audio_url="/api/download/test.wav",
                duration=5.2,
            )

            assert task.audio_path == "/test/audio.wav"
            assert task.audio_url == "/api/download/test.wav"
            assert task.audio_duration == 5.2
            assert task.status == "completed"

    def test_estimated_audio_duration(self, app):
        """测试预估音频时长"""
        with app.app_context():
            task = TTSTask(text="这是一个测试文本", speed=1.0)

            estimated = task.get_estimated_audio_duration()
            assert estimated > 0

            # 语速加快，时长应该减少
            task.speed = 2.0
            faster_estimated = task.get_estimated_audio_duration()
            assert faster_estimated < estimated
