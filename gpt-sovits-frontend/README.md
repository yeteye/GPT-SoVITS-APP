# gpt-sovits-frontend

This template should help get you started developing with Vue 3 in Vite.

## Recommended IDE Setup

[VSCode](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Compile and Minify for Production

```sh
npm run build
```

## 前端项目结构

```sh
├─public
│      banner.png
│      favicon.ico
│
└─src
    │  App.vue
    │  main.js
    │
    ├─api
    │      index.js
    │      tts.js
    │
    ├─assets
    │      banner.jpg
    │      base.css
    │      logo.svg
    │      main.css
    │      music.svg
    │      voice.png
    │
    ├─components
    │      AudioPlayer.vue          # 新增：音频播放器组件
    │      FloatingCart.vue
    │      HeaderBar.vue
    │      TaskStatusCard.vue       # 新增：任务状态卡片组件
    │      WatermarkForm.vue        # 新增：水印表单组件
    │
    ├─router
    │      index.js
    │
    ├─utils
    │      request.js
    │      validators.js            # 新增：表单验证工具
    │
    └─views
        │  AdminDashboard.vue
        │  Generate.vue
        │  HelpCenter.vue
        │  History.vue
        │  Home.vue
        │  Login.vue
        │  Model.vue                # 新增：模型详情页
        │  Register.vue
        │  Settings.vue
        │  Status.vue
        │  UserCenter.vue
        │
        ├─admin
        │      ModelAudit.vue
        │      SystemLog.vue
        │      UserManage.vue
        │      WatermarkAdmin.vue    # 新增：水印管理页面
        │
        ├─creator
        │      CloneWizard.vue
        │      CreatorCenter.vue
        │      ModelAnalytics.vue
        │      MyVoices.vue
        │      PublishVoice.vue
        │
        └─user
                MyVoices.vue
                TaskHistory.vue
                TTSPlayground.vue
                VoiceClone.vue
                VoiceLibrary.vue
                WatermarkManagement.vue
```
