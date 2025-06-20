# ./gpt-sovits-backend/tests/__init__.py
"""
GPT-SoVITS Backend Test Suite
测试包初始化文件
"""

import os
import sys

# 添加项目根目录到Python路径，确保能导入app模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 测试配置
TEST_CONFIG = {
    "TESTING": True,
    "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    "WTF_CSRF_ENABLED": False,
    "JWT_SECRET_KEY": "test-secret-key",
    "SECRET_KEY": "test-secret-key",
}

# 导出测试相关的工具函数
__all__ = ["TEST_CONFIG"]
