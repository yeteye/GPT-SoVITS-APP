// src/router/index.js - 修复版本
import { createRouter, createWebHistory } from "vue-router";
import Home from "@/views/Home.vue";
import Login from "@/views/Login.vue";
import Register from "@/views/Register.vue";

const routes = [
  {
    path: "/",
    name: "Home",
    component: Home,
  },
  {
    path: "/login",
    name: "Login",
    component: Login,
    meta: { hideHeader: true, guest: true },
  },
  {
    path: "/register",
    name: "Register",
    component: Register,
    meta: { hideHeader: true, guest: true },
  },
  // 用户中心
  {
    path: "/user",
    name: "UserCenter",
    component: () => import("@/views/UserCenter.vue"),
    meta: { requiresAuth: true },
  },
  // TTS功能 - 修复路由名称
  {
    path: "/tts-playground",
    name: "TTSPlayground",
    component: () => import("@/views/TTSPlayground.vue"),
    meta: { requiresAuth: false }, // 允许游客访问但功能受限
  },
  // 音色克隆
  {
    path: "/voice-clone",
    name: "VoiceClone",
    component: () => import("@/views/VoiceClone.vue"),
    meta: { requiresAuth: false }, // 允许游客浏览
  },
  // 音色库 - 修复路由名称
  {
    path: "/voice-library",
    name: "VoiceLibrary",
    component: () => import("@/views/VoiceLibrary.vue"),
    meta: { requiresAuth: false }, // 允许游客浏览
  },
  // 水印管理 - 修复路由名称
  {
    path: "/watermark",
    name: "WatermarkManagement", 
    component: () => import("@/views/WatermarkManagement.vue"),
    meta: { requiresAuth: false }, // 允许游客浏览
  },
  // 任务历史
  {
    path: "/task-history",
    name: "TaskHistory",
    component: () => import("@/views/TaskHistory.vue"),
    meta: { requiresAuth: true },
  },
  // 创作者中心
  {
    path: "/creator",
    name: "CreatorCenter",
    component: () => import("@/views/CreatorCenter.vue"),
    meta: { requiresAuth: true },
  },
  // 模型详情
  {
    path: "/model/:id",
    name: "ModelDetail",
    component: () => import("@/views/Model.vue"),
    props: true,
  },
  // 任务状态页面
  {
    path: "/status/:taskId",
    name: "Status",
    component: () => import("@/views/Status.vue"),
    props: true,
  },
  // 帮助中心
  {
    path: "/help",
    name: "HelpCenter",
    component: () => import("@/views/HelpCenter.vue"),
  },
  // 管理员路由
  {
    path: "/admin",
    name: "AdminDashboard",
    component: () => import("@/views/AdminDashboard.vue"),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: "/admin/users",
    name: "UserManage",
    component: () => import("@/views/admin/UserManage.vue"),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: "/admin/models",
    name: "ModelAudit",
    component: () => import("@/views/admin/ModelAudit.vue"),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: "/admin/logs",
    name: "SystemLog",
    component: () => import("@/views/admin/SystemLog.vue"),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: "/admin/watermark",
    name: "WatermarkAdmin",
    component: () => import("@/views/admin/WatermarkAdmin.vue"),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  // 404页面
  {
    path: "/:pathMatch(.*)*",
    name: "NotFound",
    component: () => import("@/views/NotFound.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// 路由守卫
router.beforeEach(async (to, from, next) => {
  console.log("路由守卫检查:", { to: to.name, from: from.name });

  try {
    // 动态导入userStore避免循环依赖
    const { userStore } = await import("@/stores/user");

    // 确保用户状态已初始化
    if (!userStore.state.isInitialized) {
      await userStore.initializeUser();
    }

    const isAuthenticated = userStore.isLoggedIn.value;
    const user = userStore.user.value;
    const isAdmin = userStore.isAdmin.value;

    console.log("用户状态:", {
      isAuthenticated,
      role: user?.role, // 添加安全访问
      isAdmin,
      username: user?.username || user?.email, // 添加安全访问
    });

    // 检查是否需要登录
    if (to.meta?.requiresAuth && !isAuthenticated) {
      console.log("需要登录，跳转到登录页");
      next({
        name: "Login",
        query: { redirect: to.fullPath },
      });
      return;
    }

    // 检查是否需要管理员权限
    if (to.meta?.requiresAdmin && !isAdmin) {
      console.log("需要管理员权限，跳转到首页");
      next({ name: "Home" });
      return;
    }

    // 如果已登录用户访问登录/注册页面，重定向到首页
    if (to.meta?.guest && isAuthenticated) {
      console.log("已登录用户访问登录页，跳转到首页");
      next({ name: "Home" });
      return;
    }

    console.log("路由检查通过，继续导航");
    next();
  } catch (error) {
    console.error("路由守卫错误:", error);
    
    // 如果是空错误，静默处理
    if (!error) {
      console.warn("路由守卫捕获到空错误，继续导航");
      next();
      return;
    }
    
    // 如果出错，允许继续导航但清除可能的错误状态
    if (to.meta?.requiresAuth) {
      next({ name: "Login" });
    } else {
      next();
    }
  }
});

export default router;