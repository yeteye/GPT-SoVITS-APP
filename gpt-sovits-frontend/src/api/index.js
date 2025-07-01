// src/api/index.js - 统一API管理 (修复版)
import request from "@/utils/request";
import { ttsRequest } from "@/utils/ttsRequest";

// 认证相关API
export const authAPI = {
  // 用户登录
  login(data) {
    return request.post("/auth/login", data);
  },

  // 用户注册
  register(data) {
    return request.post("/auth/register", data);
  },

  // 刷新token
  refreshToken() {
    return request.post("/auth/refresh");
  },

  // 用户登出
  logout() {
    return request.post("/auth/logout");
  },

  // 修改密码
  changePassword(data) {
    return request.post("/auth/change-password", data);
  },

  // 忘记密码
  forgotPassword(data) {
    return request.post("/auth/forgot-password", data);
  },

  // 重置密码
  resetPassword(token, data) {
    return request.post(`/auth/reset-password/${token}`, data);
  },

  // 验证邮箱
  verifyEmail(token) {
    return request.get(`/auth/verify-email/${token}`);
  },
};

// 用户相关API
export const userAPI = {
  // 获取用户资料
  getProfile() {
    return request.get("/user/profile");
  },

  // 更新用户资料
  updateProfile(data) {
    return request.put("/user/profile", data);
  },

  // 获取用户统计信息
  getStatistics() {
    return request.get("/user/statistics");
  },

  // 获取任务历史
  getTaskHistory(params) {
    return request.get("/user/tasks/history", { params });
  },

  // 获取用户上传文件
  getUserUploads(params) {
    return request.get("/user/uploads", { params });
  },

  // 删除上传文件
  deleteUpload(uploadId) {
    return request.delete(`/user/uploads/${uploadId}`);
  },

  // 删除账户
  deleteAccount(data) {
    return request.delete("/user/delete-account", { data });
  },
};

// TTS相关API
export const ttsAPI = {
  // 获取可用模型列表 - 修复per_page限制
  getAvailableModels(params = {}) {
    // 确保per_page不超过后端限制
    if (params.per_page && params.per_page > 100) {
      params.per_page = 100;
    }
    return request.get("/tts/models", { params });
  },

  // 获取模型详情
  getModelDetail(modelId) {
    return request.get(`/tts/models/${modelId}`);
  },

  // 生成语音
  generateSpeech(data) {
    return request.post("/tts/generate", data);
  },

  // 获取支持的情感列表
  getSupportedEmotions() {
    return request.get("/tts/emotions");
  },

  // 获取TTS任务列表
  getTTSTasks(params) {
    return request.get("/tts/tasks", { params });
  },

  // 获取TTS任务详情
  getTTSTaskDetail(taskId) {
    return request.get(`/tts/tasks/${taskId}`);
  },

  // 下载生成的音频
  downloadAudio(taskId) {
    return request.get(`/tts/tasks/${taskId}/download`, {
      responseType: "blob",
    });
  },
};

// 模型相关API
export const modelsAPI = {
  // 获取用户模型列表
  getMyModels(params = {}) {
    // 确保per_page不超过后端限制
    if (params.per_page && params.per_page > 100) {
      params.per_page = 100;
    }
    return request.get("/models/my-models", { params });
  },

  // 获取模型详情
  getModelDetail(modelId) {
    return request.get(`/models/${modelId}`);
  },

  // 更新模型信息
  updateModel(modelId, data) {
    return request.put(`/models/${modelId}`, data);
  },

  // 删除模型
  deleteModel(modelId) {
    return request.delete(`/models/${modelId}`);
  },

  // 切换模型公开状态
  toggleModelPublic(modelId) {
    return request.post(`/models/${modelId}/toggle-public`);
  },

  // 获取模型统计信息
  getModelStats() {
    return request.get("/models/stats");
  },

  // 获取可用标签
  getTags() {
    return request.get("/models/tags");
  },
};

// 音色克隆相关API - 修复版
export const voiceCloneAPI = {
  // 上传音频样本
  uploadSample(formData, config = {}) {
    return request.post("/voice-clone/upload-sample", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      ...config,
    });
  },

  // 获取用户音频样本列表
  getUserSamples(params = {}) {
    // 确保per_page不超过后端限制
    if (params.per_page && params.per_page > 100) {
      params.per_page = 100;
    }
    return request.get("/voice-clone/samples", { params });
  },

  // 删除音频样本
  deleteSample(sampleId) {
    return request.delete(`/voice-clone/samples/${sampleId}`);
  },

  // 开始训练
  startTraining(data) {
    return request.post("/voice-clone/start-training", data);
  },

  // 获取用户任务列表
  getUserTasks(params = {}) {
    // 确保per_page不超过后端限制
    if (params.per_page && params.per_page > 100) {
      params.per_page = 100;
    }
    return request.get("/voice-clone/tasks", { params });
  },

  // 获取任务详情 - 添加参数验证
  getTaskDetail(taskId) {
    if (!taskId || taskId === "undefined" || taskId === null) {
      return Promise.reject(new Error("Invalid task ID"));
    }
    return request.get(`/voice-clone/tasks/${taskId}`);
  },

  // 取消任务
  cancelTask(taskId) {
    return request.post(`/voice-clone/tasks/${taskId}/cancel`);
  },

  // 重试任务
  retryTask(taskId) {
    return request.post(`/voice-clone/tasks/${taskId}/retry`);
  },

  // 获取训练结果
  getTaskResult(taskId) {
    return request.get(`/voice-clone/tasks/${taskId}/result`);
  },

  // 上传模型文件
  uploadModel(formData) {
    return request.post("/voice-clone/upload-model", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

// 水印相关API
export const watermarkAPI = {
  // 手动嵌入水印
  embedWatermark(formData) {
    return request.post("/watermark/embed", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  // 验证水印
  verifyWatermark(formData) {
    return request.post("/watermark/verify", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  // 获取我的水印列表
  getMyWatermarks(params) {
    return request.get("/watermark/my-watermarks", { params });
  },

  // 获取水印详情
  getWatermarkDetail(watermarkId) {
    return request.get(`/watermark/my-watermarks/${watermarkId}`);
  },

  // 更新水印信息
  updateWatermark(watermarkId, data) {
    return request.put(`/watermark/my-watermarks/${watermarkId}`, data);
  },

  // 停用水印
  deactivateWatermark(watermarkId) {
    return request.delete(`/watermark/my-watermarks/${watermarkId}`);
  },

  // 获取水印统计
  getWatermarkStatistics() {
    return request.get("/watermark/statistics");
  },

  // 获取验证日志
  getVerificationLogs(params) {
    return request.get("/watermark/verification-logs", { params });
  },

  // 根据水印码获取公开信息
  getWatermarkInfo(watermarkCode) {
    return request.get(`/watermark/info/${watermarkCode}`);
  },
};

// 管理员相关API
export const adminAPI = {
  // 获取系统统计信息
  getSystemStatistics() {
    return request.get("/admin/statistics");
  },

  // 获取所有用户列表
  getAllUsers(params) {
    return request.get("/admin/users", { params });
  },

  // 更新用户角色
  updateUserRole(userId, data) {
    return request.put(`/admin/users/${userId}/role`, data);
  },

  // 更新用户状态
  updateUserStatus(userId, data) {
    return request.put(`/admin/users/${userId}/status`, data);
  },

  // 获取所有模型列表
  getAllModels(params) {
    return request.get("/admin/models", { params });
  },

  // 审核模型
  reviewModel(modelId, data) {
    return request.post(`/admin/models/${modelId}/review`, data);
  },

  // 上传官方模型
  uploadOfficialModel(formData) {
    return request.post("/admin/upload-official-model", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  // 获取审计日志
  getAuditLogs(params) {
    return request.get("/admin/audit-logs", { params });
  },

  // 系统清理
  systemCleanup() {
    return request.post("/admin/cleanup");
  },

  // 创建新标签
  createTag(data) {
    return request.post("/admin/tags", data);
  },

  // 删除标签
  deleteTag(tagId) {
    return request.delete(`/admin/tags/${tagId}`);
  },

  // 水印管理
  getAllWatermarks(params) {
    return request.get("/watermark/admin/all-watermarks", { params });
  },

  getWatermarkStatistics() {
    return request.get("/watermark/admin/statistics");
  },

  getAllVerificationLogs(params) {
    return request.get("/watermark/admin/verification-logs", { params });
  },
};

export const healthAPI = {
  healthCheck() {
    return request.get("/health");
  },
};

// —— TTS 相关 API，全部走 9880 端口的 ttsRequest ——
export const tts2API = {

  /** 生成语音 */
  generateSpeech2(data) {
    return ttsRequest.post("/tts", data);
  },

  generateSpeech(data) {
    return ttsRequest.post("/tts/generate", data);
  },


  /** 切换 GPT 权重 */
  setGPTWeights(weights_path) {
    return ttsRequest.get("/set_gpt_weights", {
      params: { weights_path },
    });
  },

  /** 切换 Sovits 权重 */
  setSovitsWeights(weights_path) {
    return ttsRequest.get("/set_sovits_weights", {
      params: { weights_path },
    });
  },

  /** 控制命令（restart / exit） */
  control(command) {
    return ttsRequest.get("/control", { params: { command } });
  }
  // endpoint: `/control`
  //
  // command:
  // "restart": 重新运行
  // "exit": 结束运行
  //   GET:
  // ```
  // http://127.0.0.1:9880/control?command=restart
  // ```
  // POST:
  // ```json
  // {
  //     "command": "restart"
  // }
  // ```
};
export const emotionAPI = {
  /**
   * 获取某模型支持的所有情感类型
   * @param {string} modelId 模型 UUID
   * @returns {Promise} 返回 { success, message, data: { emotions: [...] } }
   */
  getEmotions(modelId) {
    return request.get(`/models/${modelId}/emotions`);
  },

  /**
   * 获取指定模型某种情感的参考音频参数
   * @param {string} modelId 模型 UUID
   * @param {string} emotionType 情感类型，如 'neutral', 'happy' 等
   * @returns {Promise} 返回 { success, message, data: { model_id, type, ref_path, ref_lang, ref_text, description } }
   */
  getEmotionDetail(modelId, emotionType) {
    return request.get(`/models/${modelId}/emotions/${emotionType}`);
  }
};