# GPT-SoVITS 语音克隆及合成系统后端

基于 Flask 的 GPT-SoVITS 语音克隆与文本转语音系统后端 API 服务。

## 功能特性

### 核心功能

- **语音克隆**: 用户上传音频样本，训练个性化语音模型
- **文本转语音**: 支持多种情感和语速的语音合成
- **模型管理**: 用户模型库管理，支持公开/私有模型
- **用户系统**: 完整的用户注册、登录、权限管理
- **管理后台**: 管理员审核、系统监控、数据统计

### 技术特性

- RESTful API 设计
- JWT 身份认证
- 异步任务处理（Celery）
- 文件上传与管理
- 数据库迁移支持
- 完善的错误处理
- 审计日志记录
- 分页查询支持

## 系统架构

```python
app/
├── __init__.py              # Flask应用工厂
├── config.py               # 配置文件
├── extensions.py           # Flask扩展初始化
├── models/                 # 数据模型
│   ├── user.py            # 用户模型
│   ├── task.py            # 任务模型
│   ├── model.py           # 语音模型
│   └── audit.py           # 审计日志模型
├── auth/                   # 认证模块
│   ├── routes.py          # 认证路由
│   ├── decorators.py      # 认证装饰器
│   └── utils.py           # 认证工具函数
├── api/                    # API模块
│   ├── voice_clone.py     # 语音克隆API
│   ├── tts.py             # 文本转语音API
│   ├── model_management.py # 模型管理API
│   ├── admin.py           # 管理员API
│   └── user.py            # 用户管理API
├── services/               # 业务逻辑服务
│   ├── voice_clone_service.py  # 语音克隆服务
│   ├── tts_service.py          # TTS服务
│   ├── model_service.py        # 模型服务
│   └── file_service.py         # 文件服务
└── utils/                  # 工具模块
    ├── audio_utils.py     # 音频处理工具
    ├── validators.py      # 验证器
    ├── exceptions.py      # 自定义异常
    └── helpers.py         # 辅助函数
```

## 快速开始

### 环境要求

- Python 3.8+
- MySQL 5.7+ 或 MariaDB 10.3+
- Redis 6.0+
- FFmpeg（音频处理）

### 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd gpt-sovits-backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate
```
