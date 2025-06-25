// src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

import axios from 'axios'


const app = createApp(App)

// 4.1 axios 全局默认配置
axios.defaults.baseURL = import.meta.env.VITE_API_BASE || 'http://localhost:5000/api/v1/sovits'
// 根据需要设置请求超时、headers
axios.defaults.timeout = 10000

app.config.globalProperties.$axios = axios


// 1.1 使用路由
app.use(router)

// 2.2 使用 Element Plus
app.use(ElementPlus)

app.mount('#app')
