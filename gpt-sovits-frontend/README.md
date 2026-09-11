# Vue 前端

Vue 3、Vite 5、Element Plus 构建的业务界面。完整环境恢复与功能限制见[根目录 README](../README.md)。

## 启动

先按根目录文档配置并启动 Flask，再在本目录执行：

```powershell
npm ci
npm run dev -- --port 5173 --strictPort
```

浏览器使用 **`http://localhost:5173`**，与后端固定 CORS 来源一致。

## 配置与结构

- `src/views/`：用户、模型库、合成、克隆、水印、任务等页面。
- `src/views/admin/`：用户管理、模型审核、日志和水印管理。
- `src/router/index.js`：页面路由与权限检查。
- `src/utils/request.js`：常规 API，支持 `VITE_API_BASE_URL`，默认 `http://127.0.0.1:5000/api`。
- `src/utils/ttsRequest.js`：音频 blob 请求，地址固定为 `http://127.0.0.1:5000/api`，超时 60 秒。
- `src/api/tts.js`：保留的 `/api9880`、`/api5000` 请求封装。
- `vite.config.js`：端口和开发代理；`/api` 前缀位于其他两个代理前，使用旧封装时需核查匹配顺序。

修改 `VITE_API_BASE_URL` 无法改变所有请求地址，迁移到其他端口或主机需同时检查固定 URL 与后端 CORS。真实合成依赖后端配置、9880 引擎及模型情感参考记录，仅启动前端不会生成语音。

## 构建

```powershell
npm run build
npm run preview
```

构建输出为 `dist/`。预览不是完整部署验证，仍需核查 API 地址、跨域与代理。项目未配置前端自动化测试框架；`npm run lint` 使用 `--fix`，会自动修改源码。
