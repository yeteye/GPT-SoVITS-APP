# ./gpt-sovits-backend/tests/conftest.py
import pytest
import tempfile
import os
from app import create_app
from app.extensions import db
from app.models import User, VoiceModel, Tag


@pytest.fixture(scope="session")
def app():
    """创建测试应用"""
    # 创建临时数据库
    db_fd, db_path = tempfile.mkstemp()

    # 创建临时上传目录
    upload_dir = tempfile.mkdtemp()

    app = create_app("testing")
    app.config.update(
        {
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
            "UPLOAD_FOLDER": upload_dir,
            "WTF_CSRF_ENABLED": False,
            "TESTING": True,
        }
    )

    with app.app_context():
        db.create_all()
        yield app

    # 清理
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """测试客户端"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def auth_headers(app, client):
    """认证头部"""
    with app.app_context():
        # 创建测试用户
        user = User(
            username="testuser",
            email="test@example.com",
            is_active=True,
            is_verified=True,
        )
        user.set_password("testpassword")
        db.session.add(user)
        db.session.commit()

        # 登录获取token
        response = client.post(
            "/api/auth/login",
            json={"identifier": "testuser", "password": "testpassword"},
        )

        data = response.get_json()
        token = data["data"]["access_token"]

        return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_user(app):
    """管理员用户"""
    with app.app_context():
        admin = User(
            username="admin",
            email="admin@example.com",
            role=2,  # 管理员
            is_active=True,
            is_verified=True,
        )
        admin.set_password("adminpassword")
        db.session.add(admin)
        db.session.commit()
        return admin


@pytest.fixture
def sample_model(app, admin_user):
    """示例模型"""
    with app.app_context():
        model = VoiceModel(
            name="Test Voice Model",
            description="A test voice model",
            model_type="official",
            model_path="/test/path/model.pth",
            status="active",
            is_public=True,
            quality_score=8.5,
        )
        model.set_supported_emotions(["neutral", "happy"])
        model.set_supported_languages(["zh-CN"])

        db.session.add(model)
        db.session.commit()
        return model


@pytest.fixture
def sample_audio_file():
    """示例音频文件"""
    # 创建一个小的测试音频文件
    import numpy as np
    import soundfile as sf
    import tempfile

    # 生成1秒的正弦波
    sample_rate = 16000
    duration = 1.0
    frequency = 440

    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = 0.3 * np.sin(2 * np.pi * frequency * t)

    # 保存到临时文件
    fd, path = tempfile.mkstemp(suffix=".wav")
    sf.write(path, audio, sample_rate)

    yield path

    # 清理
    os.close(fd)
    os.unlink(path)


@pytest.fixture(autouse=True)
def clean_db(app):
    """每个测试后清理数据库"""
    yield
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()
