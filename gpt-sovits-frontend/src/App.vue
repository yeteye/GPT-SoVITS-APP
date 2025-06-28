<!-- ./gpt-sovits-frontend/src/App.vue -->
<template>
  <div id="app" class="app-container">
    <!-- 头部导航 -->
    <HeaderBar v-if="!route.meta.hideHeader" />

    <!-- 主要内容区域 -->
    <main class="main-content" :class="{ 'without-header': route.meta.hideHeader }">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- 全局浮动提示 -->
    <FloatingCart :message="floatingMessage" />

    <!-- 全局加载遮罩 -->
    <transition name="fade">
      <div v-if="globalLoading" class="global-loading">
        <div class="loading-content">
          <el-icon class="is-loading loading-icon">
            <Loading />
          </el-icon>
          <p class="loading-text">{{ loadingText }}</p>
        </div>
      </div>
    </transition>

    <!-- 返回顶部按钮 -->
    <transition name="slide-up">
      <el-backtop v-if="showBackTop" :right="30" :bottom="30" />
    </transition>
  </div>
</template>


<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElNotification } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import HeaderBar from '@/components/HeaderBar.vue'
import FloatingCart from '@/components/FloatingCart.vue'
import { userStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()

const floatingMessage = ref('')
const globalLoading = ref(false)
const loadingText = ref('加载中...')
const showBackTop = ref(false)

// 获取页面标题 - 移动到watch之前
const getPageTitle = (routeName) => {
  const titleMap = {
    'Home': 'GPT-SoVITS - 在线语音克隆平台',
    'TTSPlayground': '文本转语音 - GPT-SoVITS',
    'VoiceClone': '音色克隆 - GPT-SoVITS',
    'VoiceLibrary': '音色库 - GPT-SoVITS',
    'WatermarkManagement': '水印检查 - GPT-SoVITS',
    'TaskHistory': '历史记录 - GPT-SoVITS',
    'CreatorCenter': '创作者中心 - GPT-SoVITS',
    'UserCenter': '用户中心 - GPT-SoVITS',
    'AdminDashboard': '管理后台 - GPT-SoVITS',
    'Login': '登录 - GPT-SoVITS',
    'Register': '注册 - GPT-SoVITS',
    'HelpCenter': '帮助中心 - GPT-SoVITS',
    'Settings': '设置 - GPT-SoVITS'
  }
  return titleMap[routeName] || 'GPT-SoVITS'
}

// 全局错误处理
const handleGlobalError = (error) => {
  // 过滤掉 null 或空错误
  if (!error) {
    console.warn('捕获到空错误，忽略处理')
    return
  }

  console.error('Global error:', error)

  // 处理网络错误
  if (error.response?.status === 401) {
    userStore.clearUserData()
    router.push({ name: 'Login' })
    ElMessage.error('登录已过期，请重新登录')
    return
  }

  // 处理其他类型的错误
  if (error.message) {
    console.error('错误信息:', error.message)
  }
}

// 监听路由变化
watch(route, async (to, from) => {
  // 页面切换时隐藏浮动消息
  floatingMessage.value = ''

  // 设置页面标题 - 添加安全检查
  if (to && to.name) {
    document.title = getPageTitle(to.name)
  }

  // 页面切换动效 - 添加安全检查
  if (from && from.name && to && to.name && to.name !== from.name) {
    globalLoading.value = true
    loadingText.value = '页面加载中...'

    await nextTick()
    setTimeout(() => {
      globalLoading.value = false
    }, 300)
  }

  // 重置滚动位置 - 添加安全检查
  if (to) {
    if (to.hash) {
      document.querySelector(to.hash)?.scrollIntoView({ behavior: 'smooth' })
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }
}, { immediate: true })

// 显示浮动消息
const showFloatingMessage = (message) => {
  floatingMessage.value = message
}

// 设置全局加载状态
const setGlobalLoading = (loading, text = '加载中...') => {
  globalLoading.value = loading
  loadingText.value = text
}

// 显示成功通知
const showSuccessNotification = (title, message) => {
  ElNotification({
    title,
    message,
    type: 'success',
    duration: 3000,
    position: 'top-right'
  })

  // 监听滚动事件
  window.addEventListener('scroll', handleScroll, { passive: true })
}

// 显示错误通知
const showErrorNotification = (title, message) => {
  ElNotification({
    title,
    message,
    type: 'error',
    duration: 5000,
    position: 'top-right'
  })
}

// 监听滚动事件，控制返回顶部按钮显示
const handleScroll = () => {
  showBackTop.value = window.scrollY > 300
}

// 暴露方法给全局使用
window.app = {
  showFloatingMessage,
  setGlobalLoading,
  showSuccessNotification,
  showErrorNotification
}

onMounted(async () => {
  console.log('App组件挂载，初始化应用...')

  // 隐藏加载页面
  const loadingElement = document.getElementById('loading')
  if (loadingElement) {
    setTimeout(() => {
      loadingElement.style.opacity = '0'
      loadingElement.style.transition = 'opacity 0.5s ease'
      setTimeout(() => {
        loadingElement.style.display = 'none'
      }, 500)
    }, 1000)
  }

  // 初始化用户状态
  try {
    await userStore.initializeUser()
    console.log('用户状态初始化完成')
  } catch (error) {
    console.error('用户状态初始化失败:', error)
  }

  // 设置全局错误处理
  window.addEventListener('unhandledrejection', (event) => {
    // 阻止默认的控制台错误输出
    event.preventDefault()
    handleGlobalError(event.reason)
  })

  // 捕获全局 JavaScript 错误
  window.addEventListener('error', (event) => {
    console.error('JavaScript 错误:', event.error)
    handleGlobalError(event.error)
  })

  // 监听滚动事件
  window.addEventListener('scroll', handleScroll, { passive: true })

  // 设置全局主题
  document.documentElement.setAttribute('data-theme', 'light')

  console.log('应用初始化完成')
})
</script>

<style>
/* 全局基础样式 */
* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

html,
body {
  margin: 0;
  padding: 0;
  font-family: 'Inter', 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  background-color: var(--bg-color);
  color: var(--text-color);
  line-height: 1.6;
  font-size: 14px;
  overflow-x: hidden;
}

/* CSS变量定义 */
:root {
  /* 颜色变量 */
  --primary-color: #667eea;
  --primary-light: #8693f3;
  --primary-dark: #4c63d2;
  --secondary-color: #764ba2;
  --success-color: #67c23a;
  --warning-color: #e6a23c;
  --danger-color: #f56c6c;
  --info-color: #909399;

  /* 文本颜色 */
  --text-color: #303133;
  --text-secondary: #606266;
  --text-placeholder: #c0c4cc;
  --text-disabled: #c0c4cc;

  /* 背景颜色 */
  --bg-color: #ffffff;
  --bg-secondary: #f8f9fb;
  --bg-disabled: #f5f7fa;

  /* 边框颜色 */
  --border-color: #dcdfe6;
  --border-light: #e4e7ed;
  --border-lighter: #ebeef5;

  /* 阴影 */
  --shadow-light: 0 2px 8px rgba(0, 0, 0, 0.1);
  --shadow-medium: 0 4px 16px rgba(0, 0, 0, 0.15);
  --shadow-heavy: 0 8px 32px rgba(0, 0, 0, 0.2);

  /* 圆角 */
  --radius-small: 4px;
  --radius-medium: 8px;
  --radius-large: 12px;
  --radius-xlarge: 16px;

  /* 间距 */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  --spacing-xxl: 48px;

  /* 动画 */
  --transition-fast: 0.2s ease;
  --transition-normal: 0.3s ease;
  --transition-slow: 0.5s ease;

  /* 布局 */
  --header-height: 64px;
  --sidebar-width: 280px;
  --container-max-width: 1200px;
}

/* 应用容器 */
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
}

/* 主内容区域 */
.main-content {
  flex: 1;
  min-height: calc(100vh - var(--header-height));
  transition: var(--transition-normal);
}

.main-content.without-header {
  min-height: 100vh;
}

/* 全局加载遮罩 */
.global-loading {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}

.loading-content {
  text-align: center;
  color: white;
}

.loading-icon {
  font-size: 32px;
  margin-bottom: var(--spacing-md);
}

.loading-text {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
}

/* 动画效果 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--transition-normal);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all var(--transition-normal);
}

.slide-up-enter-from {
  transform: translateY(20px);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translateY(-20px);
  opacity: 0;
}

/* 全局滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg-disabled);
  border-radius: var(--radius-small);
}

::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: var(--radius-small);
  transition: var(--transition-fast);
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-placeholder);
}

/* Element Plus 全局样式覆盖 */
.el-button {
  border-radius: var(--radius-medium);
  font-weight: 500;
  transition: var(--transition-fast);
  border: 1px solid transparent;
}

.el-button--primary {
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.el-button--primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}

.el-card {
  border-radius: var(--radius-large);
  border: 1px solid var(--border-lighter);
  box-shadow: var(--shadow-light);
  transition: var(--transition-normal);
  overflow: hidden;
}

.el-dialog {
  border-radius: var(--radius-xlarge);
  overflow: hidden;
}

/* 响应式设计 */
@media (max-width: 768px) {
  :root {
    --header-height: 56px;
    --spacing-md: 12px;
    --spacing-lg: 16px;
    --spacing-xl: 24px;
    --spacing-xxl: 32px;
  }

  .main-content {
    min-height: calc(100vh - 56px);
  }
}
</style>