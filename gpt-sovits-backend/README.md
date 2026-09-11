# Flask 业务后端

完整的环境恢复、数据库配置、模型准备、已知限制和测试运行说明见[根目录 README](../README.md)。本目录负责用户、模型、任务、审核和水印业务，真实语音推理由独立的 `GPT-SoVITS-main/api_v2.py` 提供。

## 启动

完成根目录 README 的依赖安装和 `.env` 配置后，在本目录执行：

```powershell
.\.venv\Scripts\python.exe -m flask --app run init-db
.\.venv\Scripts\python.exe -m flask --app run create-admin
.\.venv\Scripts\python.exe run.py
```

- 业务地址：`http://127.0.0.1:5000/api`。
- 健康检查：`GET /api/health`；不检查推理引擎。
- Swagger：`http://127.0.0.1:5000/apidocs/`。
- 配置：`app/config.py`；`run.py` 在导入应用前加载 `.env`。
- 数据：MySQL 数据库与本目录默认 `uploads/`。
- 测试：安装 pytest 后使用 `.\.venv\Scripts\python.exe -m pytest tests -v`；覆盖率需安装 pytest-cov。

原 `requirements.txt` 含旧环境本地路径，不能直接作为可移植安装清单。`init-db` 不升级已有表，`--drop` 会删除数据。示例模型、克隆训练和部分 TTS 分支是模拟实现；真实推理还涉及 9880 服务、Celery 配置、权重路径及 `emotion` 参考记录，详见根目录 README。
