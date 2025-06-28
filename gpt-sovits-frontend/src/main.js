// ./gpt-sovits-frontend/src/main.js
import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import zhCn from "element-plus/dist/locale/zh-cn.mjs";

// 创建Vue应用
const app = createApp(App);

// 全局错误处理
app.config.errorHandler = (err, vm, info) => {
  console.error("Vue全局错误:", err, info);
};

// 使用 Element Plus （添加中文本地化）
app.use(ElementPlus, {
  locale: zhCn,
});

// 使用路由
app.use(router);

// 全局属性
app.config.globalProperties.$ELEMENT = {
  size: "default",
  zIndex: 3000,
};

// 挂载应用
console.log("应用启动...");
app.mount("#app");
