import axios from 'axios'

// GPT-SoVITS 服务（端口 9880）
const ttsRequest = axios.create({
  baseURL: '/api9880',
  timeout: 15000
})

// Flask 主服务（端口 5000）
const flaskRequest = axios.create({
  baseURL: '/api5000',
  timeout: 15000
})

/**
 * 调用 GPT-SoVITS 语音合成接口（转发到 9880）
 * @param {Object} payload 请求参数 JSON
 * @returns Promise
 */
export function synthesizeTTS(payload, config = {}) {
  return ttsRequest.post('/tts', payload, config)
}

/**
 * 示例：调用 Flask 的上传接口（转发到 5000）
 * @param {FormData} formData
 * @returns Promise
 */
export function uploadVoice(formData) {
  return flaskRequest.post('/upload', formData)
}
