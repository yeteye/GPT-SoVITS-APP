// ./gpt-sovits-frontend/src/utils/validators.js
// 常用的表单验证规则

// 邮箱验证
export const validateEmail = (rule, value, callback) => {
  const emailReg = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!value) {
    callback(new Error("请输入邮箱"));
  } else if (!emailReg.test(value)) {
    callback(new Error("请输入有效的邮箱地址"));
  } else {
    callback();
  }
};

// 密码验证
export const validatePassword = (rule, value, callback) => {
  if (!value) {
    callback(new Error("请输入密码"));
  } else if (value.length < 6) {
    callback(new Error("密码长度不能少于6位"));
  } else {
    callback();
  }
};

// 用户名验证
export const validateUsername = (rule, value, callback) => {
  const usernameReg = /^[a-zA-Z0-9_\u4e00-\u9fa5]{2,20}$/;
  if (!value) {
    callback(new Error("请输入用户名"));
  } else if (!usernameReg.test(value)) {
    callback(new Error("用户名只能包含字母、数字、下划线和中文，长度2-20位"));
  } else {
    callback();
  }
};

// 文件大小验证
export const validateFileSize = (file, maxSize = 50) => {
  const isLtMaxSize = file.size / 1024 / 1024 < maxSize;
  if (!isLtMaxSize) {
    return `文件大小不能超过 ${maxSize}MB`;
  }
  return true;
};

// 音频文件类型验证
export const validateAudioFile = (file) => {
  const allowedTypes = [
    "audio/wav",
    "audio/mp3",
    "audio/mpeg",
    "audio/m4a",
    "audio/aac",
  ];
  if (!allowedTypes.includes(file.type)) {
    return "只支持 WAV、MP3、M4A、AAC 格式的音频文件";
  }
  return true;
};

// 水印码验证
export const validateWatermarkCode = (rule, value, callback) => {
  const codeReg = /^[A-Z0-9]{16,64}$/;
  if (!value) {
    callback(new Error("请输入水印码"));
  } else if (!codeReg.test(value)) {
    callback(new Error("水印码格式不正确"));
  } else {
    callback();
  }
};

// 文本长度验证
export const validateTextLength = (minLength, maxLength) => {
  return (rule, value, callback) => {
    if (!value) {
      callback(new Error("请输入内容"));
    } else if (value.length < minLength) {
      callback(new Error(`内容长度不能少于${minLength}个字符`));
    } else if (value.length > maxLength) {
      callback(new Error(`内容长度不能超过${maxLength}个字符`));
    } else {
      callback();
    }
  };
};

// 数字范围验证
export const validateNumberRange = (min, max) => {
  return (rule, value, callback) => {
    if (value === undefined || value === null || value === "") {
      callback(new Error("请输入数字"));
    } else if (isNaN(value)) {
      callback(new Error("请输入有效的数字"));
    } else if (value < min || value > max) {
      callback(new Error(`数值应在 ${min} 到 ${max} 之间`));
    } else {
      callback();
    }
  };
};

// 格式化文件大小
export const formatFileSize = (bytes) => {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

// 格式化时长
export const formatDuration = (seconds) => {
  if (!seconds || seconds < 0) return "0秒";

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  if (hours > 0) {
    return `${hours}小时${minutes}分${secs}秒`;
  } else if (minutes > 0) {
    return `${minutes}分${secs}秒`;
  } else {
    return `${secs}秒`;
  }
};

// 格式化时间
export const formatTime = (timeStr) => {
  if (!timeStr) return "";
  return new Date(timeStr).toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
};

// 截断文本
export const truncateText = (text, maxLength = 50) => {
  if (!text) return "";
  return text.length > maxLength ? text.substring(0, maxLength) + "..." : text;
};
