# GPT-SoVITS-APP

早期的语音克隆与文本转语音 Web 应用，包含 Vue 前端、Flask 业务后端，以及一份 GPT-SoVITS 引擎源码。业务功能涵盖注册登录、模型库、语音任务、模型审核和音频水印。

本文按当前仓库代码整理，主要用于恢复本地环境和开展软件功能测试。**现有实现混合了真实推理与模拟流程，不能保证完整业务链路直接运行成功。** 以下明确区分环境配置、已有功能和已知限制；本次文档整理未安装完整依赖、启动数据库或执行端到端测试。

## 1. 项目结构与服务关系

```text
GPT-SoVITS-APP/
├── gpt-sovits-frontend/          # Vue 3 + Vite 5 + Element Plus
│   ├── src/views/               # 用户页面与 admin 管理页面
│   ├── src/router/index.js      # 页面路由、登录与角色检查
│   ├── src/api/                 # API 封装
│   ├── src/utils/request.js     # 普通请求、JWT、错误处理
│   ├── src/utils/ttsRequest.js  # 合成音频请求（blob）
│   └── vite.config.js           # 5173 端口与开发代理
├── gpt-sovits-backend/           # Flask + SQLAlchemy + JWT
│   ├── run.py                  # HTTP 入口、建表及用户管理命令
│   ├── celery_worker.py        # 可选任务 worker 入口
│   ├── app/config.py           # 从环境变量读取配置
│   ├── app/auth/               # 注册、登录、认证和权限
│   ├── app/api/                # 用户、模型、TTS、克隆、水印、管理接口
│   ├── app/models/             # ORM 数据表，包括 emotion 参考音频表
│   ├── app/services/           # 业务处理、推理 HTTP 调用与模拟流程
│   ├── tests/                  # 已有 pytest 用例和夹具
│   └── migrations/             # 仅迁移框架，未附版本迁移脚本
├── GPT-SoVITS-main/             # 独立引擎环境，不是 Flask 后端
│   ├── api_v2.py               # 9880 推理 API，业务后端使用这个入口
│   ├── webui.py                # 引擎自带训练/推理界面
│   └── GPT_SoVITS/configs/tts_infer.yaml
└── 后端代码缺陷.md              # 历史分析，部分内容已过时，以当前代码为准
```

| 组件 | 本地地址 | 用途 |
| --- | --- | --- |
| Vite 前端 | `http://localhost:5173` | 浏览器访问入口 |
| Flask | `http://127.0.0.1:5000/api` | 登录、模型、任务、水印等业务 API |
| GPT-SoVITS | `http://127.0.0.1:9880` | 权重切换、实际语音推理 |
| MySQL | `localhost:3306` | 持久化业务数据 |
| Redis | `localhost:6379`（可选） | Celery broker / result backend、缓存 |

真实合成路径是：浏览器 → Flask `/api/tts/generate` → 引擎的 `/set_gpt_weights`、`/set_sovits_weights`、`/tts` → 后端保存音频并返回。当前 TTS 路由是同步调用服务函数，并非提交任务后立即返回。

## 2. 先恢复基础业务环境

以下命令使用 **Windows PowerShell**。首次从仓库根目录开始；每个服务用独立终端，并注意各步骤注明的工作目录。先完成本节即可查看和测试用户、模型管理等业务；真实语音还需要第 3 节。

### 2.1 安装后端依赖

准备 Python 3.10 或 3.11、Node.js、npm、MySQL，以及音频处理所需的 FFmpeg。前端锁文件中的 Vite 声明 Node.js 要求为 `^18.0.0 || >=20.0.0`。引擎使用独立 Python 环境，避免两套依赖冲突。

原 `gpt-sovits-backend/requirements.txt` 是旧环境导出文件，包含 `file:///home/conda/...`、`file:///D:/bld/...` 等本地路径，不能原样在新电脑安装。下面是按业务代码导入整理的安装起点，并非已验证的完整锁定环境：

```powershell
cd .\gpt-sovits-backend
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install Flask==3.1.1 Flask-SQLAlchemy==3.1.1 Flask-Migrate==4.1.0 Flask-JWT-Extended==4.7.1 flask-cors==6.0.1 Flask-Mail==0.10.0 flasgger==0.9.7.1 PyMySQL==1.1.1 python-dotenv==1.1.0 celery==5.5.3 redis==6.2.0 requests==2.32.4 numpy==1.26.4 scipy==1.13.1 librosa==0.11.0 soundfile==0.13.1 pydub==0.25.1 psutil
.\.venv\Scripts\python.exe -m pip install python-magic-bin==0.4.14
```

已安装 Python 3.11 时可将 `py -3.10` 换成 `py -3.11`。直接调用虚拟环境中的 Python，不需要修改 PowerShell 激活脚本策略。

`app/services/file_service.py` 会导入 `magic`。上例的 `python-magic-bin` 用于 Windows 的 libmagic 支持；Linux 使用 `python-magic` 与系统 `libmagic`。不要在同一环境同时安装两种 magic 包。FFmpeg 和 ffprobe 必须能被后端进程找到，可用 `ffmpeg -version`、`ffprobe -version` 检查；只放在引擎目录未必能供后端使用。

### 2.2 创建独立的本地数据库

在 MySQL 客户端中执行下列 SQL，将示例密码替换为自己的本地密码。此处创建专用于恢复/测试的库，不复用原有业务数据：

```sql
CREATE DATABASE gpt_sovits_local CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'gpt_sovits_local'@'localhost' IDENTIFIED BY 'replace-with-local-password';
GRANT ALL PRIVILEGES ON gpt_sovits_local.* TO 'gpt_sovits_local'@'localhost';
```

### 2.3 创建后端 `.env`

在 `gpt-sovits-backend/.env` 保存以下内容，数据库密码与上一步一致，两项密钥换成不同的随机字符串：

```dotenv
FLASK_CONFIG=development
SECRET_KEY=replace-with-a-random-local-secret
JWT_SECRET_KEY=replace-with-another-random-local-secret
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=gpt_sovits_local
MYSQL_PASSWORD=replace-with-local-password
MYSQL_DATABASE=gpt_sovits_local

# 基础业务模式暂不启用队列、缓存和邮件
CELERY_BROKER_URL=
CELERY_RESULT_BACKEND=
REDIS_URL=
MAIL_SERVER=
MAIL_USERNAME=
WATERMARK_ENABLED=false
```

`run.py` 和 `celery_worker.py` 会先加载 `.env`。`create_app()` 本身不会加载；直接写 Python 脚本导入 app 时需要先加载环境变量。已经存在的进程环境变量也可能覆盖 `.env`，修改后需重启后端。

| 配置 | 行为 / 默认值 |
| --- | --- |
| `DATABASE_URL` | 可替代 `MYSQL_*`，且优先级更高；格式为 `mysql+pymysql://用户:URL编码后的密码@主机:3306/库名?charset=utf8mb4` |
| `MYSQL_PASSWORD` | 使用分离变量时，代码会自动对密码做 URL 编码 |
| `FLASK_CONFIG` | `development`、`production`、`testing`、`default`；普通浏览器测试用 `development` |
| `UPLOAD_FOLDER` | 默认当前工作目录下 `uploads` 的绝对路径，建议始终从后端目录启动；真实 TTS 保存函数另有固定 `./uploads\generated` 路径，暂勿仅改此变量迁移音频目录 |
| `GPT_MODEL_PATH` / `SOVITS_MODEL_PATH` | 默认 `./models/gpt`、`./models/sovits`；真实 TTS 实际读取数据库模型记录中的文件路径 |
| `MAX_CONTENT_LENGTH` | 默认总请求大小上限 1 GiB；上传接口还有各自校验 |
| `AUDIO_MIN_DURATION` / `AUDIO_MAX_DURATION` | 默认 3 / 120 秒，具体接口和前端还可能限制时长 |
| `WATERMARK_ENABLED` | 默认 true；初次恢复可关闭合成过程水印，再单独启用核查 |
| `MAIL_*` | 邮件服务器、端口、TLS、用户名、密码、发件人；收邮件相关流程需要另行配置 |

完整配置见 `app/config.py`。不要仅把开发配置的 `DATABASE_URL` 改为 SQLite：它仍包含 MySQL 专用连接参数；现有 `testing` 配置才清空这些参数。测试配置使用内存库，不适合持久化浏览器演示。

### 2.4 初始化表、账户和演示数据

在 `gpt-sovits-backend` 中执行：

```powershell
.\.venv\Scripts\python.exe -m flask --app run init-db
.\.venv\Scripts\python.exe -m flask --app run create-admin
# 可选：创建用于浏览模型库的示例记录与占位文件
.\.venv\Scripts\python.exe -m flask --app run create-sample-models
.\.venv\Scripts\python.exe -m flask --app run list-users
```

管理员用户名、邮箱和密码会交互输入，没有预置通用密码。普通用户从网页注册。角色为 `0=普通用户`、`1=审核员`、`2=管理员`，不是“创作者等级”。已有账户可用：

```powershell
.\.venv\Scripts\python.exe -m flask --app run reset-password your_username
.\.venv\Scripts\python.exe -m flask --app run set-user-role your_username 1
```

`init-db` 使用 `db.create_all()`，创建表但不会升级已有表结构。仓库没有可重放的迁移版本，不能把 `flask db upgrade` 当作完整初始化步骤。不要对已有数据使用 `init-db --drop`；它会删除全部表。初始化日志会打印数据库连接串，分享日志前去除密码。

**`create-sample-models` 只生成文本占位文件，不会下载或训练可用权重，也不会创建情感参考音频记录。** 它适合模型列表展示，不适合验证音频合成质量。

### 2.5 启动后端与前端

终端 A，位于 `gpt-sovits-backend`：

```powershell
.\.venv\Scripts\python.exe run.py
```

终端 B，从仓库根目录进入前端：

```powershell
cd .\gpt-sovits-frontend
npm ci
npm run dev -- --port 5173 --strictPort
```

打开 **`http://localhost:5173`**。后端跨域响应固定允许这个来源，请保持 `localhost` 和端口一致；不要改成 `127.0.0.1:5173`。`--strictPort` 可避免 5173 被占用后 Vite 自动换端口。

基础检查：

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/health
```

使用 MySQL 且可连接时，预期 `services.database` 为 `healthy`；未配置 Redis/Celery 时 `unavailable` 是当前支持的状态。健康接口不检查 9880 推理服务，并使用 MySQL 的 `SELECT NOW()`，SQLite 下可能报错。Swagger 入口为 `http://127.0.0.1:5000/apidocs/`，静态 `GPT-SoVITS.openapi.json` 仅供辅助参考，以路由实现为准。

前端普通请求支持 `VITE_API_BASE_URL`，但 `src/utils/ttsRequest.js` 的合成地址硬编码为 `http://127.0.0.1:5000/api`。更改一个环境变量不能迁移全部 API。`vite.config.js` 的 `/api` 代理在 `/api9880`、`/api5000` 之前，存在前缀覆盖问题；旧封装 `src/api/tts.js` 的代理路径需单独核查。

## 3. 恢复真实语音推理

这一部分需要真实模型和参考音频；仓库未携带完整可用权重集。先恢复单独的引擎，再接通业务链路。

### 3.1 配置独立 GPT-SoVITS 环境

依据仓库内 `GPT-SoVITS-main/docs/cn/README.md` 的安装说明准备匹配的 Python、PyTorch/torchaudio 和设备环境。业务后端的 requirements 不能代替引擎 requirements。本地引擎文档提供 Python 3.10 的 Conda 安装路径；依赖安装入口为：

```powershell
# 在已准备好 PyTorch/torchaudio 的独立引擎环境中执行
cd .\GPT-SoVITS-main
python -m pip install -r extra-req.txt --no-deps
python -m pip install -r requirements.txt
```

模型获取位置见引擎自带中文 README 的“预训练模型”说明。先用 v1/v2 对应资源恢复旧模型，版本应与自己的权重相匹配；不要将其他版本文件直接替换旧文件。

修改 `GPT_SoVITS/configs/tts_infer.yaml` 的 **`custom` 段**。此段优先使用，当前保存着旧电脑 `D:\Code\From_Pycharm\...` 的绝对路径。以下是 CPU / v1 的配置结构示例，路径所指文件必须实际存在：

```yaml
custom:
  device: cpu
  is_half: false
  version: v1
  bert_base_path: GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large
  cnhuhbert_base_path: GPT_SoVITS/pretrained_models/chinese-hubert-base
  t2s_weights_path: GPT_SoVITS/pretrained_models/s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt
  vits_weights_path: GPT_SoVITS/pretrained_models/s2G488k.pth
```

使用自训练权重时改成实际文件路径，并匹配 `version`。CUDA 环境就绪后才改 `device: cuda` 和适用的精度设置。BERT/Hubert 目录需要完整模型与配置，只有空目录不够。

终端 C，位于 `GPT-SoVITS-main` 且使用引擎 Python：

```powershell
python api_v2.py -a 127.0.0.1 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml
```

启动后查看 `http://127.0.0.1:9880/docs`。`go-webui.bat` / `webui.py` 是引擎的另一套界面，不是本项目 Vue 应用，也不能替代 9880 API。

### 3.2 准备业务模型和情感参考记录

真实 TTS 会读取 `voice_models.gpt_model_path`、`sovits_model_path`。两项路径应使用 Flask 和推理服务都能访问的**绝对路径**，因为两个服务的工作目录不同。`emotion.ref_path` 也应指向推理进程可读的实际音频文件；它不是浏览器上传控件中的临时路径。

当前上传校验把 **GPT 限定为 `.pth`、SoVITS 限定为 `.ckpt`**，而本仓库引擎配置使用 **GPT `.ckpt`、SoVITS `.pth`**。这是代码不一致，不能通过把文件改名就认定模型有效。初次联调可通过 Flask shell 创建独立的本地模型记录，绕开错误的上传校验；上传功能本身仍需后续修复。

在后端目录执行 `.\.venv\Scripts\python.exe -m flask --app run shell`，然后输入以下 Python。先替换三处路径与参考音频的准确转录文本；此操作向本地数据库新增记录：

```python
from pathlib import Path
from app.models.emotion import Emotion

gpt_path = "E:/models/my_voice.ckpt"
sovits_path = "E:/models/my_voice.pth"
ref_path = "E:/models/reference.wav"
assert all(Path(p).is_file() for p in (gpt_path, sovits_path, ref_path))

model = VoiceModel(name="本地真实语音", model_type="official",
    gpt_model_path=gpt_path, sovits_model_path=sovits_path,
    status="active", review_status="approved", is_public=True)
model.set_supported_emotions(["neutral"])
model.set_supported_languages(["zh"])
db.session.add(model)
db.session.flush()
db.session.add(Emotion(model_id=model.id, type="neutral", ref_path=ref_path,
    ref_lang="zh", ref_text="这里填写参考音频实际说出的内容"))
db.session.commit()
print(model.id)
```

前端会先查询 `/api/models/<model_id>/emotions` 和 `/api/models/<model_id>/emotions/<emotion_type>`。只有 `supported_emotions` 列表，没有 `emotion` 表记录，仍无法正常选择情感并合成。参考音频可先准备清晰的 3–10 秒 WAV，语言和转录与音频一致。

### 3.3 Celery 配置与当前实现限制

当前 `generate_speech_task()` 只有在 `TESTING` 为 false、后端 Celery 实例存在且传入 self 非空时才进入真实推理分支；没有配置 Celery 时会生成模拟文件。因此，**只启动 9880 不足以让业务后端执行真实推理**。

启动可访问的 Redis 后，在后端 `.env` 中设置并重启 Flask：

```dotenv
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
REDIS_URL=redis://localhost:6379/2
```

现有 worker 入口如下，订阅 `celery,voice_clone,tts` 队列：

```powershell
.\.venv\Scripts\python.exe celery_worker.py
```

该脚本默认 `concurrency=4`，Windows 下进程池需单独处理。若在 Windows 联调 worker，可将该脚本 `worker_main` 参数改用 `--pool=solo`、`--concurrency=1`。这属于后续代码调整，本次文档没有修改启动脚本，也没有验证 worker 能正常消费任务。

此外，任务装饰器在没有 Flask 应用上下文时会降级成 mock，`.delay()` 只返回模拟结果而不执行任务。启动 worker 并不证明任务已经正确注册。TTS 当前是同步处理；克隆任务可能一直 pending。异步链路应视为待核查功能。

## 4. 常用页面与操作入口

| 页面 | 路径 | 前置条件 / 用途 |
| --- | --- | --- |
| 注册、登录 | `/register`、`/login` | 普通用户注册，管理员使用 CLI 创建的账户 |
| 用户中心 | `/user` | 个人信息 |
| 模型库 | `/voice-library`、`/model/:id` | 查看模型和详情 |
| 语音合成 | `/tts-playground` | 登录、可用模型、情感记录；真实合成还需引擎与上述配置 |
| 语音克隆 | `/voice-clone` | 上传音频并创建任务；训练核心仍为模拟实现 |
| 历史与任务状态 | `/task-history`、`/status/:taskId` | 查询任务与结果 |
| 水印 | `/watermark` | 水印管理、嵌入和验证；准备可解码音频 |
| 管理后台 | `/admin`、`/admin/users`、`/admin/models`、`/admin/logs`、`/admin/watermark` | 依照前端路由及后端接口要求使用对应角色 |

角色修改后重新登录，必要时清理浏览器 localStorage 中的 `token` 和 `user`。接口权限最终由后端判定。

## 5. 已有测试的运行方式

以下说明仓库已有脚本的入口，不代表这些脚本与当前 API 完全一致或已经通过。运行前记录当前 Git 提交、依赖版本和所用数据库。

在 `gpt-sovits-backend` 中安装测试工具并运行已有用例：

```powershell
.\.venv\Scripts\python.exe -m pip install pytest==8.4.0 pytest-cov
.\.venv\Scripts\python.exe -m pytest tests -v --tb=short
# 仅运行已有认证模块测试
.\.venv\Scripts\python.exe -m pytest tests/test_auth.py -v
# 显式生成覆盖率和 JUnit 结果
.\.venv\Scripts\python.exe -m pytest tests --cov=app --cov-report=term-missing --cov-report=html:htmlcov --junitxml=test-results.xml
```

`tests/conftest.py` 强制使用 `testing`，初始化 SQLite 和临时上传目录，禁用外部 Redis/Celery/邮件。它在 `create_app()` 之后才覆盖数据库 URI；SQLAlchemy 已经初始化，不能假定后设置的临时文件路径就是实际连接的数据库。

现有 `pytest.ini` 写成了 `[tool:pytest]`，而 pytest.ini 应使用 `[pytest]`，因此上述命令显式指定 `tests` 和报告参数。原依赖文件也未列入 `pytest-cov`。直接在后端根目录运行未限定路径的 pytest，可能收集到 `test_mysql.py` 这类会在导入时连接真实数据库的脚本。

其他历史入口：

| 命令（使用后端 Python） | 用途 / 注意事项 |
| --- | --- |
| `python quick_test.py` | 历史导入和基础行为检查，使用测试配置 |
| `python test_api.py` | 向 `http://localhost:5000/api` 发真实 HTTP 请求；需要运行 Flask，会创建业务测试数据，限独立测试库 |
| `python test_mysql.py` | 旧连接诊断脚本，主要解析 `DATABASE_URL`，会输出连接信息；分离式 `MYSQL_*` 配置请优先通过 Flask 检查 |

已知用例漂移：`tests/test_tts.py` 仍发送旧的 `speed` 字段并期待 JSON/201；当前路由要求参考音频、提示文本等字段，使用 `speed_factor` 并返回音频。不能将此类失败直接归因为环境没有安装好，也不能以模拟任务通过证明真实语音可用。

前端现有脚本只有开发、构建、预览和 lint，没有配置前端自动化测试框架。构建检查入口为 `npm run build`；`npm run lint` 带 `--fix`，会修改源码。构建产物在 `dist/`，不能假定静态部署自动拥有 Vite 开发代理。

## 6. 常见问题与当前功能边界

| 现象 | 原因 / 定位方向 |
| --- | --- |
| pip 报旧磁盘路径不存在 | 原 requirements 含本地构建路径，参照第 2.1 节准备业务依赖 |
| 导入 `magic` 失败 | Windows 缺 libmagic DLL 或混装 magic 包 |
| 数据库 Access denied / Unknown database | 检查建库、账号密码、`DATABASE_URL` 优先级；进程需重启 |
| 页面正常但 API 跨域失败 | 浏览器必须使用 `http://localhost:5173`，检查固定 API URL 和 CORS |
| 模型库为空 | 新数据库没有模型，按需初始化演示记录或配置真实模型 |
| 无情感选项 / 情感详情 404 | `emotion` 表没有对应模型的参考记录 |
| 9880 启动即找不到文件 | `custom` 仍是旧路径，或 BERT/Hubert/权重不完整 |
| 上传真实权重遭拒 | 业务端 GPT/SoVITS 后缀校验与引擎相反，见第 3.2 节 |
| 返回 `.wav` 却无法播放 | 无 Celery 或测试模式走 mock：写入的是文本；mock 水印还可能返回不存在的 `_watermarked` 路径 |
| 合成慢或超时 | 前端合成请求超时为 60 秒，后端引擎请求可等 120 秒；同步推理可能超过前端时限 |
| 合成返回的音频 URL 404 | 保存函数生成 `/static/audio/<文件名>`，未见配套静态目录映射；应核查 `/api/tts/tasks/<task_id>/download` 下载接口 |
| 克隆任务一直 pending | mock `.delay()` 不执行任务；检查装饰器、注册任务及 worker 队列 |
| 克隆“训练完成”但权重无法推理 | `extract_audio_features`、`train_gpt_model`、`train_sovits_model` 仍创建模拟数据/文本文件 |
| 健康接口正常但 worker 状态异常 | 当前空闲 worker 也可能显示 `no_workers`；健康结果不等于推理和队列全链路可用 |

本地启动时优先保留 Flask、Vite、引擎三个终端的错误信息。结束时对各服务使用 Ctrl+C；数据库、上传文件和模型不会随退出删除。上述限制来自代码核对，仍需在恢复环境后区分并记录实际复现结果。
