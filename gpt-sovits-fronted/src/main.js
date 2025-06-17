// src/main.js
import { createApp } from 'vue'
import App from './App.vue'

// 1. 引入路由
import router from './router'

import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

// 4. axios 配置：可全局使用 axios 进行 API 调用
import axios from 'axios'
// 可根据项目需要再引入拦截器文件，例如
// import './api/axiosInterceptors'

// 5. 状态管理（可选）：Pinia 或 Vuex
// 这里以 Pinia 为例
// import { createPinia } from 'pinia'

// 6. 国际化（可选），如果有 i18n，再引入
// import { createI18n } from 'vue-i18n'
// import messages from './locales'

// 7. 其它全局插件或自定义指令、全局组件等
// import MyGlobalComponent from '@/components/MyGlobalComponent.vue'
// import myDirective from '@/directives/myDirective'

const app = createApp(App)

// 4.1 axios 全局默认配置
axios.defaults.baseURL = import.meta.env.VITE_API_BASE || 'http://localhost:5000/api/v1/sovits'
// 根据需要设置请求超时、headers
axios.defaults.timeout = 10000
// 如果需要在请求中携带认证 token，可在拦截器中处理
// axios.interceptors.request.use(config => {
//   const token = localStorage.getItem('token')
//   if (token) {
//     config.headers.Authorization = `Bearer ${token}`
//   }
//   return config
// })

// 2.1 将 axios 挂载到全局属性，组件内可通过 this.$axios 或 app.config.globalProperties.$axios 访问
app.config.globalProperties.$axios = axios

// 5.1 使用 Pinia（如果需要状态管理）
// const pinia = createPinia()
// app.use(pinia)

// 1.1 使用路由
app.use(router)

// 2.2 使用 Element Plus
app.use(ElementPlus)

// 6.1 如果使用 i18n
// const i18n = createI18n({ locale: 'zh-CN', messages })
// app.use(i18n)

// 7.1 注册全局组件或指令（若有）
// app.component('MyGlobalComponent', MyGlobalComponent)
// app.directive('my-directive', myDirective)

app.mount('#app')
