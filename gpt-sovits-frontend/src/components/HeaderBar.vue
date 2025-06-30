<!-- src/components/HeaderBar.vue - 修复版本 -->
<template>
  <header class="header">
    <div class="header-left" @click="goHome">
      <div class="logo">🎙️</div>
      <h1 class="title">GPT-SoVITS 在线语音克隆</h1>
    </div>

    <nav class="nav-menu">
      <el-menu mode="horizontal" :default-active="activeMenu" class="el-menu-demo" @select="onSelect" router>
        <el-menu-item index="/tts-playground">文本转语音</el-menu-item>
        <el-menu-item index="/voice-clone">音色克隆</el-menu-item>
        <el-menu-item index="/creator" v-if="isLoggedIn">创作者中心</el-menu-item>
        <el-menu-item index="/voice-library">音色库</el-menu-item>
        <el-menu-item v-if="isLoggedIn" index="/task-history">历史记录</el-menu-item>
        <el-menu-item index="/watermark">水印检查</el-menu-item>
        <el-menu-item index="/help">帮助中心</el-menu-item>
        <!-- 管理员后台入口 - 只有管理员可见 -->
        <el-menu-item v-if="isAdmin" index="/admin">管理员后台</el-menu-item>
      </el-menu>
    </nav>

    <!-- 用户操作区域 -->
    <div class="header-right">
      <!-- 未登录状态：显示登录和注册按钮 -->
      <div v-if="!isLoggedIn" class="auth-buttons">
        <el-button @click="goToLogin" size="default">登录</el-button>
        <el-button type="primary" @click="goToRegister" size="default">注册</el-button>
      </div>

      <!-- 已登录状态：显示用户信息和抽屉触发器 -->
      <div v-else class="user-section">
        <div class="user-info" @click="toggleUserDrawer">
          <el-avatar :size="32" :src="userInfo?.avatar_url">
            <el-icon>
              <User />
            </el-icon>
          </el-avatar>
          <span class="username">{{ userInfo?.username || userInfo?.email }}</span>
          <el-icon class="dropdown-icon">
            <ArrowDown />
          </el-icon>
        </div>
      </div>
    </div>

    <!-- 用户抽屉 -->
    <el-drawer v-model="userDrawerVisible" title="用户中心" direction="rtl" size="400px">
      <div class="user-drawer-content">
        <!-- 用户信息展示 -->
        <div class="user-profile">
          <div class="avatar-section">
            <el-avatar :size="80" :src="userInfo?.avatar_url">
              <el-icon>
                <User />
              </el-icon>
            </el-avatar>
            <div class="user-details">
              <h3>{{ userInfo?.username || userInfo?.email }}</h3>
              <p class="user-email">{{ userInfo?.email }}</p>
              <el-tag :type="getRoleTagType(userInfo?.role)" size="small">
                {{ getRoleText(userInfo?.role) }}
              </el-tag>
            </div>
          </div>
        </div>

        <el-divider />

        <!-- 快捷操作 -->
        <div class="quick-actions">
          <h4>快捷操作</h4>
          <div class="action-grid">
            <div class="action-item" @click="goToTaskHistory">
              <el-icon class="action-icon">
                <Clock />
              </el-icon>
              <span>任务历史</span>
            </div>
            <div class="action-item" @click="goToVoiceLibrary">
              <el-icon class="action-icon">
                <Mic />
              </el-icon>
              <span>我的音色</span>
            </div>
            <div class="action-item" @click="goToUserCenter">
              <el-icon class="action-icon">
                <Setting />
              </el-icon>
              <span>用户中心</span>
            </div>
            <!-- 管理员后台入口 -->
            <div v-if="isAdmin" class="action-item" @click="goToAdmin">
              <el-icon class="action-icon">
                <Tools />
              </el-icon>
              <span>管理后台</span>
            </div>
          </div>
        </div>

        <el-divider />

        <!-- 账户操作 -->
        <div class="account-actions">
          <h4>账户操作</h4>
          <el-button @click="showChangePasswordDialog" class="action-button">
            <el-icon>
              <Lock />
            </el-icon>
            修改密码
          </el-button>
          <el-button @click="handleLogout" type="danger" class="action-button">
            <el-icon>
              <SwitchButton />
            </el-icon>
            退出登录
          </el-button>
        </div>
      </div>
    </el-drawer>

    <!-- 修改密码弹窗 -->
    <el-dialog v-model="changePasswordVisible" title="修改密码" width="400px">
      <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="100px">
        <el-form-item label="当前密码" prop="currentPassword">
          <el-input v-model="passwordForm.currentPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="passwordForm.newPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="changePasswordVisible = false">取消</el-button>
          <el-button type="primary" @click="submitChangePassword" :loading="passwordLoading">
            确认修改
          </el-button>
        </span>
      </template>
    </el-dialog>
  </header>
</template>

<script setup>
import { ref, computed, watch, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User,
  Setting,
  Tools,
  SwitchButton,
  ArrowDown,
  Clock,
  Mic,
  Lock
} from '@element-plus/icons-vue'
import { userStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()

// 响应式数据
const userDrawerVisible = ref(false)
const changePasswordVisible = ref(false)
const passwordLoading = ref(false)
const passwordFormRef = ref()

const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordRules = {
  currentPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 计算属性
const activeMenu = computed(() => route.path)
const isLoggedIn = computed(() => {
  try {
    return userStore.isLoggedIn.value
  } catch {
    return !!localStorage.getItem('token')
  }
})
const isAdmin = computed(() => {
  try {
    return userStore.isAdmin.value
  } catch {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    return user.role === 2
  }
})
const userInfo = computed(() => {
  try {
    return userStore.user.value
  } catch {
    return JSON.parse(localStorage.getItem('user') || '{}')
  }
})

// 方法
const onSelect = (index) => {
  console.log('菜单点击:', index)

  // 检查需要登录的页面
  const authRequiredPages = ['/creator', '/task-history']

  if (authRequiredPages.includes(index) && !isLoggedIn.value) {
    ElMessage.warning('请先登录后再访问该功能')
    goToLogin()
    return
  }

  try {
    // 使用编程式导航确保跳转成功
    router.push(index).then(() => {
      console.log('路由跳转成功:', index)
    }).catch(error => {
      console.error('路由跳转失败:', error)
      ElMessage.error('页面跳转失败，请重试')
    })
  } catch (error) {
    console.error('路由跳转异常:', error)
    ElMessage.error('页面跳转失败，请重试')
  }
}

const goHome = () => {
  try {
    router.push({ name: 'Home' })
  } catch (error) {
    console.error('跳转首页失败:', error)
    router.push('/')
  }
}

const goToLogin = () => {
  try {
    router.push({
      name: 'Login',
      query: { redirect: route.fullPath }
    })
  } catch (error) {
    console.error('跳转登录页失败:', error)
    router.push('/login')
  }
}

const goToRegister = () => {
  try {
    router.push({ name: 'Register' })
  } catch (error) {
    console.error('跳转注册页失败:', error)
    router.push('/register')
  }
}

const goToAdmin = () => {
  if (isAdmin.value) {
    try {
      router.push({ name: 'AdminDashboard' })
      userDrawerVisible.value = false
    } catch (error) {
      router.push('/admin')
    }
  }
}

const goToTaskHistory = () => {
  router.push({ name: 'TaskHistory' })
  userDrawerVisible.value = false
}

const goToVoiceLibrary = () => {
  router.push({ name: 'VoiceLibrary' })
  userDrawerVisible.value = false
}

const goToUserCenter = () => {
  router.push({ name: 'UserCenter' })
  userDrawerVisible.value = false
}

const toggleUserDrawer = () => {
  userDrawerVisible.value = !userDrawerVisible.value
}

const showChangePasswordDialog = () => {
  changePasswordVisible.value = true
  passwordForm.currentPassword = ''
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
}

const submitChangePassword = async () => {
  if (!passwordFormRef.value) return

  passwordFormRef.value.validate(async (valid) => {
    if (!valid) return

    passwordLoading.value = true
    try {
      const result = await userStore.changePassword({
        current_password: passwordForm.currentPassword,
        new_password: passwordForm.newPassword
      })

      if (result.success) {
        changePasswordVisible.value = false
        userDrawerVisible.value = false
        // 修改密码成功后会自动登出
        router.push({ name: 'Login' })
      }
    } catch (error) {
      console.error('修改密码失败:', error)
    } finally {
      passwordLoading.value = false
    }
  })
}

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要退出登录吗？',
      '确认退出',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await userStore.logout()
    userDrawerVisible.value = false
    router.push({ name: 'Home' })

  } catch (error) {
    // 用户取消退出
    if (error !== 'cancel') {
      console.error('退出登录失败:', error)
    }
  }
}

const getRoleText = (role) => {
  const roleMap = {
    0: '普通用户',
    1: '审核员',
    2: '管理员'
  }
  return roleMap[role] || '未知角色'
}

const getRoleTagType = (role) => {
  const typeMap = {
    0: '',
    1: 'warning',
    2: 'danger'
  }
  return typeMap[role] || ''
}

// 监听路由变化，更新激活的菜单项
watch(route, () => {
  console.log('当前路由:', route.path, route.name)
}, { immediate: true })

// 组件挂载时初始化用户状态
onMounted(async () => {
  try {
    await userStore.initializeUser()
  } catch (error) {
    console.warn('初始化用户状态失败:', error)
  }
})

// 暴露方法供外部调用（如果需要）
defineExpose({
  isLoggedIn,
  userInfo
})
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: rgba(106, 90, 205, 0.08);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  position: relative;
  z-index: 1000;
}

.header-left {
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.header-left:hover {
  transform: scale(1.02);
}

.logo {
  font-size: 32px;
  margin-right: 16px;
  transition: transform 0.3s ease;
}

.logo:hover {
  transform: rotate(5deg);
}

.title {
  font-size: 20px;
  font-weight: 600;
  color: #4b3f88;
  margin: 0;
}

.nav-menu {
  flex-grow: 1;
  margin: 0 20px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.auth-buttons {
  display: flex;
  gap: 12px;
  align-items: center;
}

.auth-buttons .el-button {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.auth-buttons .el-button:not(.el-button--primary) {
  background: transparent;
  border-color: #4b3f88;
  color: #4b3f88;
}

.auth-buttons .el-button:not(.el-button--primary):hover {
  background: rgba(106, 90, 205, 0.1);
  border-color: #6A5ACD;
  color: #6A5ACD;
}

.auth-buttons .el-button--primary {
  background: linear-gradient(135deg, #6A5ACD, #8A2BE2);
  border: none;
  box-shadow: 0 2px 8px rgba(106, 90, 205, 0.3);
}

.auth-buttons .el-button--primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(106, 90, 205, 0.4);
}

.user-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.admin-btn {
  border-radius: 6px;
  font-weight: 500;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #4b3f88;
}

.user-info:hover {
  background: rgba(106, 90, 205, 0.1);
}

.username {
  font-weight: 500;
  font-size: 14px;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-icon {
  font-size: 12px;
  color: #4b3f88;
  transition: transform 0.3s ease;
}

/* 用户抽屉样式 */
.user-drawer-content {
  padding: 20px;
}

.user-profile {
  margin-bottom: 20px;
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 16px;
}

.user-details h3 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.user-email {
  margin: 4px 0 8px 0;
  color: #666;
  font-size: 14px;
}

.quick-actions h4,
.account-actions h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #333;
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 12px;
  background: #f8f9fb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
}

.action-item:hover {
  background: #e8f2ff;
  transform: translateY(-2px);
}

.action-icon {
  font-size: 24px;
  color: #6A5ACD;
  margin-bottom: 8px;
}

.action-item span {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.account-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-button {
  width: 100%;
  justify-content: flex-start;
  padding: 12px 16px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.action-button:hover {
  transform: translateY(-1px);
}

/* 覆盖 el-menu 样式 */
:deep(.el-menu-demo) {
  background-color: transparent;
  border-bottom: none;
}

:deep(.el-menu-demo .el-menu-item) {
  color: #4b3f88;
  transition: all 0.3s ease;
  border-radius: 6px;
  margin: 0 2px;
}

:deep(.el-menu-demo .el-menu-item:hover) {
  background-color: rgba(106, 90, 205, 0.1);
  color: #6A5ACD;
}

:deep(.el-menu-demo .el-menu-item.is-active) {
  background-color: rgba(106, 90, 205, 0.15);
  color: #6A5ACD;
  font-weight: 600;
}

:deep(.el-menu-demo .el-menu-item.is-active):after {
  background-color: rgba(106, 90, 205, 0.4);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .title {
    font-size: 20px;
  }

  .nav-menu {
    margin: 0 15px;
  }
}

@media (max-width: 992px) {
  .title {
    font-size: 18px;
  }

  .username {
    display: none;
  }

  .nav-menu {
    margin: 0 10px;
  }
}

@media (max-width: 768px) {
  .header {
    padding: 12px 16px;
  }

  .title {
    font-size: 16px;
  }

  .logo {
    font-size: 24px;
  }

  .auth-buttons {
    gap: 8px;
  }

  .auth-buttons .el-button {
    padding: 8px 12px;
    font-size: 14px;
  }

  .action-grid {
    grid-template-columns: 1fr;
  }
}
</style>