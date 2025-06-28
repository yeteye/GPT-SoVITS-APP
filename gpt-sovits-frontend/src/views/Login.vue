<!-- ./gpt-sovits-frontend/src/views/Login.vue -->
<template>
  <div class="login-bg">
    <div class="login-wrapper">
      <div class="login-logo">
        <img src="/favicon.ico" alt="logo" />
        <span>GPT-SoVITS 登录</span>
      </div>

      <el-form :model="form" :rules="rules" ref="formRef" class="login-form" label-position="top"
        @submit.native.prevent>
        <el-form-item label="用户名或邮箱" prop="identifier">
          <el-input v-model="form.identifier" placeholder="请输入用户名或邮箱" clearable size="large" @keyup.enter="onSubmit">
            <template #prefix>
              <el-icon>
                <User />
              </el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" clearable size="large" show-password
            @keyup.enter="onSubmit">
            <template #prefix>
              <el-icon>
                <Lock />
              </el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item>
          <div class="form-actions">
            <el-checkbox v-model="rememberMe">记住我</el-checkbox>
            <el-button type="text" @click="showForgotPassword">忘记密码？</el-button>
          </div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" class="login-btn" @click="onSubmit" size="large" :loading="loading">
            {{ loading ? '登录中...' : '登录' }}
          </el-button>

          <div class="register-section">
            <span>还没有账号？</span>
            <el-button type="text" class="register-link" @click="goToRegister">
              立即注册
            </el-button>
          </div>
        </el-form-item>
      </el-form>
    </div>

    <!-- 忘记密码弹窗 -->
    <el-dialog v-model="forgotPasswordVisible" title="重置密码" width="400px" :before-close="closeForgotPassword">
      <el-form :model="forgotForm" :rules="forgotRules" ref="forgotFormRef" label-width="80px">
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="forgotForm.email" placeholder="请输入注册邮箱" clearable />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="forgotPasswordVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForgotPassword" :loading="forgotLoading">
            发送重置邮件
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { authAPI } from '@/api'

const router = useRouter()
const route = useRoute()

const formRef = ref(null)
const forgotFormRef = ref(null)
const loading = ref(false)
const forgotLoading = ref(false)
const rememberMe = ref(false)
const forgotPasswordVisible = ref(false)

const form = reactive({
  identifier: '',
  password: ''
})

const forgotForm = reactive({
  email: ''
})

const rules = {
  identifier: [
    { required: true, message: '请输入用户名或邮箱', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
}

const forgotRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ]
}

// 登录提交
const onSubmit = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      const res = await authAPI.login({
        identifier: form.identifier,
        password: form.password
      })

      if (res && res.data.access_token) {
        // 保存登录信息
        localStorage.setItem('token', res.data.access_token)
        if (res.data.refresh_token) {
          localStorage.setItem('refreshToken', res.data.refresh_token)
        }
        localStorage.setItem('user', JSON.stringify(res.data.user))

        // 记住我功能
        if (rememberMe.value) {
          localStorage.setItem('rememberedUser', form.identifier)
        } else {
          localStorage.removeItem('rememberedUser')
        }

        ElMessage.success('登录成功')

        // 根据用户角色跳转
        const userRole = res.data.user.role
        const redirect = route.query.redirect || '/'

        if (userRole === 2) {
          // 管理员跳转到管理面板
          router.push('/admin')
        } else {
          // 普通用户跳转到原来要访问的页面或首页
          router.push(redirect)
        }
      } else {
        throw new Error('登录响应格式错误')
      }
    } catch (error) {
      console.error('登录失败:', error)
      ElMessage.error(error?.response?.data?.message || '登录失败，请检查用户名和密码')
    } finally {
      loading.value = false
    }
  })
}

// 跳转注册
const goToRegister = () => {
  router.push({ name: 'Register' })
}

// 显示忘记密码弹窗
const showForgotPassword = () => {
  forgotPasswordVisible.value = true
  forgotForm.email = ''
}

// 关闭忘记密码弹窗
const closeForgotPassword = () => {
  forgotPasswordVisible.value = false
  forgotForm.email = ''
}

// 提交忘记密码
const submitForgotPassword = () => {
  forgotFormRef.value.validate(async (valid) => {
    if (!valid) return

    forgotLoading.value = true
    try {
      await authAPI.forgotPassword({ email: forgotForm.email })
      ElMessage.success('重置邮件已发送，请查收邮箱')
      forgotPasswordVisible.value = false
    } catch (error) {
      ElMessage.error(error?.response?.data?.message || '发送失败，请稍后重试')
    } finally {
      forgotLoading.value = false
    }
  })
}

// 页面加载时恢复记住的用户名
onMounted(() => {
  const rememberedUser = localStorage.getItem('rememberedUser')
  if (rememberedUser) {
    form.identifier = rememberedUser
    rememberMe.value = true
  }
})
</script>

<style scoped>
.login-bg {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.login-bg::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('@/assets/banner.jpg') center/cover;
  opacity: 0.1;
  z-index: 0;
}

.login-wrapper {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  padding: 48px 40px;
  width: 420px;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  z-index: 1;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.login-logo {
  display: flex;
  align-items: center;
  margin-bottom: 40px;
}

.login-logo img {
  width: 48px;
  height: 48px;
  margin-right: 16px;
}

.login-logo span {
  font-size: 24px;
  font-weight: 700;
  color: #333;
  letter-spacing: 1px;
}

.login-form {
  width: 100%;
}

.el-form-item {
  margin-bottom: 24px;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.login-btn {
  width: 100%;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 2px;
  border-radius: 12px;
  height: 48px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: #fff;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

.login-btn:active {
  transform: translateY(0);
}

.register-section {
  width: 100%;
  text-align: center;
  margin-top: 20px;
  color: #666;
  font-size: 14px;
}

.register-link {
  color: #667eea;
  font-weight: 600;
  margin-left: 8px;
}

.register-link:hover {
  color: #764ba2;
  text-decoration: underline;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .login-wrapper {
    width: 90%;
    padding: 32px 24px;
    margin: 20px;
  }

  .login-logo span {
    font-size: 20px;
  }
}

/* Element Plus 样式覆盖 */
:deep(.el-input__inner) {
  border-radius: 8px;
  border: 2px solid #f0f0f0;
  transition: all 0.3s ease;
}

:deep(.el-input__inner:focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

:deep(.el-checkbox__label) {
  color: #666;
  font-size: 14px;
}

:deep(.el-dialog) {
  border-radius: 16px;
}

:deep(.el-dialog__header) {
  padding: 24px 24px 0;
}

:deep(.el-dialog__body) {
  padding: 20px 24px;
}

:deep(.el-dialog__footer) {
  padding: 0 24px 24px;
}
</style>