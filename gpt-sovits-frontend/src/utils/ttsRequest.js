// gpt-sovits-frontend/src/utils/ttsRequest.js
import axios from 'axios'
import { handleTokenExpired } from './request'  // 如果需要和主 request 一致的拦截逻辑

export const ttsRequest = axios.create({
  baseURL: 'http://127.0.0.1:5000/api',
  timeout: 60000,
  responseType: 'blob',   // ← 全局 blob
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 可选：跟主 request 一样加上拦截器
ttsRequest.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
ttsRequest.interceptors.response.use(
  res => res.data,
  err => {
    if (err.response?.status === 401) handleTokenExpired()
    return Promise.reject(err)
  }
)
