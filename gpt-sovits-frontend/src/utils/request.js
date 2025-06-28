// ./gpt-sovits-frontend/src/utils/request.js
import axios from "axios";
import { ElMessage, ElLoading, ElMessageBox } from "element-plus";
import router from "@/router";

let loadingInstance = null;
let requestCount = 0;

// 创建axios实例
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000/api",
  timeout: 30000,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

// 显示全局loading
const showLoading = () => {
  if (requestCount === 0 && !loadingInstance) {
    loadingInstance = ElLoading.service({
      text: "加载中...",
      background: "rgba(0, 0, 0, 0.7)",
      spinner: "el-icon-loading",
    });
  }
  requestCount++;
};

// 隐藏全局loading
const hideLoading = () => {
  requestCount--;
  if (requestCount <= 0 && loadingInstance) {
    loadingInstance.close();
    loadingInstance = null;
    requestCount = 0;
  }
};

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // 显示loading，除非指定不显示
    if (config.showLoading !== false) {
      showLoading();
    }

    // 添加认证token
    const token = localStorage.getItem("token");
    if (
      token &&
      !config.url.includes("/auth/login") &&
      !config.url.includes("/auth/register")
    ) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // 添加请求时间戳，防止缓存
    if (config.method === "get") {
      config.params = {
        ...config.params,
        _t: Date.now(),
      };
    }

    // 处理FormData
    if (config.data instanceof FormData) {
      delete config.headers["Content-Type"];
    }

    return config;
  },
  (error) => {
    hideLoading();
    ElMessage.error("请求配置错误");
    return Promise.reject(error);
  }
);

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    hideLoading();

    // 如果是文件下载，直接返回response
    if (response.config.responseType === "blob") {
      return response;
    }

    const { data } = response;

    // 处理成功响应
    if (data.success !== false) {
      return data;
    } else {
      // 后端返回的业务错误
      ElMessage.error(data.message || "操作失败");
      return Promise.reject(new Error(data.message || "操作失败"));
    }
  },
  (error) => {
    hideLoading();

    const { response } = error;

    if (response) {
      const { status, data } = response;

      switch (status) {
        case 400:
          ElMessage.error(data?.message || "请求参数错误");
          break;

        case 401:
          // token过期或无效
          handleTokenExpired();
          break;

        case 403:
          ElMessage.error("权限不足");
          break;

        case 404:
          ElMessage.error("请求的资源不存在");
          break;

        case 409:
          ElMessage.error(data?.message || "资源冲突");
          break;

        case 422:
          // 参数验证错误
          if (data && data.errors) {
            const errorMessages = Object.values(data.errors).flat();
            ElMessage.error(errorMessages.join(", "));
          } else {
            ElMessage.error(data?.message || "参数验证失败");
          }
          break;

        case 429:
          ElMessage.error("请求过于频繁，请稍后再试");
          break;

        case 500:
          ElMessage.error("服务器内部错误");
          break;

        case 502:
          ElMessage.error("网关错误");
          break;

        case 503:
          ElMessage.error("服务暂不可用");
          break;

        default:
          ElMessage.error(data?.message || `请求失败 (${status})`);
      }
    } else if (error.code === "ECONNABORTED") {
      ElMessage.error("请求超时，请检查网络连接");
    } else if (error.code === "ERR_NETWORK") {
      ElMessage.error("网络连接失败，请检查网络");
    } else {
      ElMessage.error("网络连接失败，请检查网络");
    }

    return Promise.reject(error);
  }
);

// 处理token过期
const handleTokenExpired = () => {
  const currentPath = router.currentRoute.value.path;

  // 避免在登录页面重复提示
  if (currentPath === "/login") {
    return;
  }

  localStorage.removeItem("token");
  localStorage.removeItem("user");

  ElMessageBox.confirm("登录状态已过期，请重新登录", "提示", {
    confirmButtonText: "重新登录",
    cancelButtonText: "取消",
    type: "warning",
  })
    .then(() => {
      router.push({
        name: "Login",
        query: { redirect: currentPath },
      });
    })
    .catch(() => {
      // 用户取消，跳转到首页
      router.push({ name: "Home" });
    });
};

// 封装常用请求方法
export const requestWithoutLoading = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000/api",
  timeout: 30000,
  withCredentials: true,
});

// 为无loading请求也添加token和错误处理
requestWithoutLoading.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

requestWithoutLoading.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      handleTokenExpired();
    }
    return Promise.reject(error);
  }
);

// 文件上传专用请求
export const uploadRequest = (url, formData, options = {}) => {
  const { onProgress, ...config } = options;

  return request.post(url, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const progress = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        onProgress(progress);
      }
    },
    timeout: 300000, // 5分钟超时
    ...config,
  });
};

// 文件下载专用请求
export const downloadRequest = (url, filename, options = {}) => {
  return request
    .get(url, {
      responseType: "blob",
      showLoading: false,
      ...options,
    })
    .then((response) => {
      // 创建下载链接
      const blob = new Blob([response.data]);
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;

      // 尝试从响应头获取文件名
      const disposition = response.headers["content-disposition"];
      let downloadFilename = filename;

      if (disposition) {
        const filenameMatch = disposition.match(
          /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/
        );
        if (filenameMatch && filenameMatch[1]) {
          downloadFilename = filenameMatch[1].replace(/['"]/g, "");
        }
      }

      link.download = downloadFilename || `download_${Date.now()}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);

      return response;
    });
};

// 请求重试函数
export const retryRequest = (fn, retries = 3, delay = 1000) => {
  return new Promise((resolve, reject) => {
    const attempt = (attemptNumber) => {
      fn()
        .then(resolve)
        .catch((error) => {
          if (attemptNumber < retries && error.response?.status >= 500) {
            setTimeout(() => attempt(attemptNumber + 1), delay * attemptNumber);
          } else {
            reject(error);
          }
        });
    };
    attempt(1);
  });
};

// 批量请求函数
export const batchRequest = (requests, options = {}) => {
  const { concurrency = 5, onProgress, stopOnError = false } = options;

  return new Promise((resolve, reject) => {
    const results = [];
    const errors = [];
    let completed = 0;
    let index = 0;

    const executeNext = () => {
      if (index >= requests.length) {
        if (completed === requests.length) {
          if (errors.length > 0 && stopOnError) {
            reject(errors);
          } else {
            resolve({ results, errors });
          }
        }
        return;
      }

      const currentIndex = index++;
      const request = requests[currentIndex];

      request()
        .then((result) => {
          results[currentIndex] = result;
        })
        .catch((error) => {
          errors[currentIndex] = error;
          if (stopOnError) {
            reject(error);
            return;
          }
        })
        .finally(() => {
          completed++;
          if (onProgress) {
            onProgress(completed, requests.length);
          }
          executeNext();
        });

      // 启动下一个并发请求
      if (index - completed < concurrency) {
        executeNext();
      }
    };

    // 启动初始并发请求
    for (let i = 0; i < Math.min(concurrency, requests.length); i++) {
      executeNext();
    }
  });
};

// 取消请求的控制器管理
const cancelTokens = new Map();

export const createCancelToken = (key) => {
  if (cancelTokens.has(key)) {
    cancelTokens.get(key).cancel("Operation canceled");
  }

  const source = axios.CancelToken.source();
  cancelTokens.set(key, source);
  return source.token;
};

export const cancelRequest = (key) => {
  if (cancelTokens.has(key)) {
    cancelTokens.get(key).cancel("Operation canceled by user");
    cancelTokens.delete(key);
  }
};

// 请求缓存
const cache = new Map();

export const cachedRequest = (url, config = {}, cacheTime = 5 * 60 * 1000) => {
  const cacheKey = `${url}?${JSON.stringify(config.params || {})}`;
  const cached = cache.get(cacheKey);

  if (cached && Date.now() - cached.timestamp < cacheTime) {
    return Promise.resolve(cached.data);
  }

  return request.get(url, config).then((data) => {
    cache.set(cacheKey, {
      data,
      timestamp: Date.now(),
    });
    return data;
  });
};

// 清除缓存
export const clearCache = (pattern) => {
  if (pattern) {
    for (const key of cache.keys()) {
      if (key.includes(pattern)) {
        cache.delete(key);
      }
    }
  } else {
    cache.clear();
  }
};

export default request;
