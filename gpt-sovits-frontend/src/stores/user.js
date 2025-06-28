// ./gpt-sovits-frontend/src/stores/user.js
import { reactive, computed, readonly } from "vue";
import { ElMessage } from "element-plus";

// 创建全局用户状态
const state = reactive({
  user: {
    id: "",
    username: "",
    email: "",
    avatar_url: "",
    role: 0,
    is_active: true,
    is_verified: false,
    created_at: "",
    last_login_at: "",
  },
  token: "",
  refreshToken: "",
  isLoading: false,
  isInitialized: false,
});

// 计算属性
export const useUserStore = () => {
  const isLoggedIn = computed(() => {
    return !!(state.token && state.user.id);
  });

  const isAdmin = computed(() => {
    return state.user.role === 2;
  });

  const isModerator = computed(() => {
    return state.user.role >= 1;
  });

  // 从localStorage加载用户信息
  const loadFromStorage = () => {
    try {
      const token = localStorage.getItem("token");
      const refreshToken = localStorage.getItem("refreshToken");
      const userStr = localStorage.getItem("user");

      if (token && userStr) {
        state.token = token;
        state.refreshToken = refreshToken || "";

        const userData = JSON.parse(userStr);
        Object.assign(state.user, userData);

        console.log(
          "用户信息加载成功:",
          state.user.username || state.user.email
        );
        return true;
      }
    } catch (error) {
      console.error("加载用户信息失败:", error);
      clearUserData();
    }
    return false;
  };

  // 保存用户信息到localStorage
  const saveToStorage = () => {
    try {
      if (state.token) {
        localStorage.setItem("token", state.token);
        localStorage.setItem("user", JSON.stringify(state.user));

        if (state.refreshToken) {
          localStorage.setItem("refreshToken", state.refreshToken);
        }
      }
    } catch (error) {
      console.error("保存用户信息失败:", error);
    }
  };

  // 清除用户数据
  const clearUserData = () => {
    state.user = {
      id: "",
      username: "",
      email: "",
      avatar_url: "",
      role: 0,
      is_active: true,
      is_verified: false,
      created_at: "",
      last_login_at: "",
    };
    state.token = "";
    state.refreshToken = "";

    // 清除localStorage
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("refreshToken");
  };

  // 登录
  const login = async (credentials) => {
    state.isLoading = true;
    try {
      // 模拟API调用
      const mockResponse = {
        success: true,
        data: {
          access_token: "mock_token_" + Date.now(),
          refresh_token: "mock_refresh_" + Date.now(),
          user: {
            id: "user_" + Date.now(),
            username: credentials.identifier,
            email: credentials.identifier.includes("@")
              ? credentials.identifier
              : credentials.identifier + "@example.com",
            avatar_url: "",
            role: credentials.identifier === "admin" ? 2 : 0,
            is_active: true,
            is_verified: true,
            created_at: new Date().toISOString(),
            last_login_at: new Date().toISOString(),
          },
        },
      };

      if (mockResponse.success && mockResponse.data) {
        const { access_token, refresh_token, user } = mockResponse.data;

        // 更新状态
        state.token = access_token;
        state.refreshToken = refresh_token || "";
        Object.assign(state.user, user);

        // 保存到localStorage
        saveToStorage();

        ElMessage.success("登录成功");
        return { success: true, data: mockResponse.data };
      } else {
        throw new Error(mockResponse.message || "登录失败");
      }
    } catch (error) {
      const errorMessage =
        error?.response?.data?.message || error.message || "登录失败";
      ElMessage.error(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      state.isLoading = false;
    }
  };

  // 注册
  const register = async (userData) => {
    state.isLoading = true;
    try {
      // 模拟API调用
      const mockResponse = {
        success: true,
        message: "注册成功",
      };

      if (mockResponse.success) {
        ElMessage.success("注册成功！请查收邮箱验证邮件");
        return { success: true, data: mockResponse.data };
      } else {
        throw new Error(mockResponse.message || "注册失败");
      }
    } catch (error) {
      const errorMessage =
        error?.response?.data?.message || error.message || "注册失败";
      ElMessage.error(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      state.isLoading = false;
    }
  };

  // 登出
  const logout = async (showMessage = true) => {
    try {
      // 模拟API调用
      console.log("执行登出操作");
    } catch (error) {
      console.warn("后端登出失败:", error);
    }

    // 清除本地数据
    clearUserData();

    if (showMessage) {
      ElMessage.success("已退出登录");
    }
  };

  // 修改密码
  const changePassword = async (passwordData) => {
    state.isLoading = true;
    try {
      // 模拟API调用
      const mockResponse = { success: true };

      if (mockResponse.success) {
        ElMessage.success("密码修改成功，请重新登录");
        // 修改密码后需要重新登录
        await logout(false);
        return { success: true };
      } else {
        throw new Error(mockResponse.message || "密码修改失败");
      }
    } catch (error) {
      const errorMessage =
        error?.response?.data?.message || error.message || "密码修改失败";
      ElMessage.error(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      state.isLoading = false;
    }
  };

  // 初始化用户状态
  const initializeUser = async () => {
    if (state.isInitialized) {
      return;
    }

    console.log("初始化用户状态...");

    // 从localStorage加载
    loadFromStorage();

    state.isInitialized = true;
    console.log("用户状态初始化完成:", {
      isLoggedIn: isLoggedIn.value,
      user: state.user.username || state.user.email,
    });
  };

  // 检查权限
  const hasPermission = (requiredRole = 0) => {
    if (!isLoggedIn.value) {
      return false;
    }
    return state.user.role >= requiredRole;
  };

  return {
    // 状态
    state: readonly(state),

    // 计算属性
    isLoggedIn,
    isAdmin,
    isModerator,

    // 方法
    login,
    register,
    logout,
    changePassword,
    initializeUser,
    loadFromStorage,
    clearUserData,
    hasPermission,

    // 直接访问用户数据
    user: computed(() => state.user),
    token: computed(() => state.token),
    isLoading: computed(() => state.isLoading),
  };
};

// 创建全局实例
export const userStore = useUserStore();

// 监听localStorage变化，实现多标签页同步
if (typeof window !== "undefined") {
  window.addEventListener("storage", (e) => {
    if (e.key === "token" || e.key === "user") {
      console.log("检测到localStorage变化，重新加载用户状态");
      userStore.loadFromStorage();
    }
  });
}

export default userStore;
