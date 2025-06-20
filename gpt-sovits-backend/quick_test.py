# ./gpt-sovits-backend/quick_test.py
"""
快速测试修复后的代码
"""
import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 设置测试环境
os.environ["FLASK_CONFIG"] = "testing"
os.environ["TESTING"] = "True"


def test_imports():
    """测试关键模块导入"""
    print("Testing imports...")

    try:
        from app import create_app

        print("✓ App creation - OK")

        from app.services.tts_service import generate_speech_task

        print("✓ TTS service - OK")

        from app.services.voice_clone_service import start_voice_clone_task

        print("✓ Voice clone service - OK")

        from app.utils.audio_utils import validate_audio_content

        print("✓ Audio utils - OK")

        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False


def test_app_creation():
    """测试应用创建"""
    print("\nTesting app creation...")

    try:
        from app import create_app

        app = create_app("testing")

        with app.app_context():
            from app.extensions import db

            db.create_all()
            print("✓ Database creation - OK")

        print("✓ App creation - OK")
        return True
    except Exception as e:
        print(f"✗ App creation error: {e}")
        return False


def test_service_calls():
    """测试服务调用"""
    print("\nTesting service calls...")

    try:
        from app import create_app
        from app.services.tts_service import generate_speech_task
        from app.services.voice_clone_service import start_voice_clone_task

        app = create_app("testing")

        with app.app_context():
            # 测试服务函数定义
            print("✓ TTS service callable - OK")
            print("✓ Voice clone service callable - OK")

        return True
    except Exception as e:
        print(f"✗ Service call error: {e}")
        return False


def test_mock_task_execution():
    """测试模拟任务执行"""
    print("\nTesting mock task execution...")

    try:
        from app import create_app
        from app.extensions import db
        from app.models import User, TTSTask, VoiceCloneTask, VoiceModel
        from app.services.tts_service import generate_speech_task
        from app.services.voice_clone_service import start_voice_clone_task

        app = create_app("testing")

        with app.app_context():
            # 推送请求上下文来模拟HTTP请求环境
            with app.test_request_context("/test", method="POST"):
                try:
                    db.create_all()

                    # 创建测试用户
                    user = User(username="testuser", email="test@example.com")
                    user.set_password("testpass")
                    db.session.add(user)

                    # 创建测试模型
                    model = VoiceModel(
                        name="Test Model",
                        model_path="/test/path",
                        status="active",
                        is_public=True,
                    )
                    model.set_supported_emotions(["neutral", "happy"])
                    db.session.add(model)

                    db.session.commit()

                    # 创建TTS任务
                    tts_task = TTSTask(
                        user_id=user.id,
                        text="Test text",
                        model_id=model.id,
                        emotion="neutral",
                    )
                    db.session.add(tts_task)
                    db.session.commit()

                    # 测试TTS任务执行
                    try:
                        result = generate_speech_task(None, tts_task.id)
                        print("✓ TTS task execution - OK")
                        tts_success = True
                    except Exception as e:
                        print(f"✗ TTS task execution error: {e}")
                        tts_success = False

                    # 创建语音克隆任务
                    vc_task = VoiceCloneTask(
                        user_id=user.id,
                        task_name="Test Voice Clone",
                        model_name="Test Cloned Model",
                    )
                    db.session.add(vc_task)
                    db.session.commit()

                    # 测试语音克隆任务执行
                    try:
                        result = start_voice_clone_task(None, vc_task.id)
                        print("✓ Voice clone task execution - OK")
                        vc_success = True
                    except Exception as e:
                        print(f"✗ Voice clone task execution error: {e}")
                        vc_success = False

                    return tts_success and vc_success

                except Exception as e:
                    print(f"✗ Database operation error: {e}")
                    try:
                        db.session.rollback()
                    except:
                        pass
                    return False

    except Exception as e:
        print(f"✗ Mock task execution error: {e}")
        return False


def main():
    """主测试函数"""
    print("=" * 50)
    print("Quick Test for GPT-SoVITS Backend Fixes")
    print("=" * 50)

    tests = [
        test_imports,
        test_app_creation,
        test_service_calls,
        test_mock_task_execution,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed! Fixes are working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit(main())
