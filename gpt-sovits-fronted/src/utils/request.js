// utils/request.js
import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: 'http://127.0.0.1:5000/api',
  timeout: 10000,
  withCredentials: true,
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // 忽略 login和register 接口，不加 token
    if (!config.url.includes('/auth/login') && !config.url.includes('/auth/register')) {
      const token = localStorage.getItem('token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const msg = error.response?.data?.message || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

export default request
