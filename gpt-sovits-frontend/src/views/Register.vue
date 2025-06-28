<!-- ./gpt-sovits-frontend/src/views/Register.vue -->
<template>
  <div class="register-bg">
    <div class="register-wrapper">
      <div class="register-logo">
        <img src="/favicon.ico" alt="logo" />
        <span>GPT-SoVITS 注册</span>
      </div>

      <el-form :model="form" :rules="rules" ref="formRef" class="register-form" label-position="top"
        @submit.native.prevent>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" clearable size="large" @keyup.enter="onSubmit">
            <template #prefix>
              <el-icon>
                <User />
              </el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱地址" clearable size="large" @keyup.enter="onSubmit">
            <template #prefix>
              <el-icon>
                <Message />
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
          <div class="password-tips">
            <span>密码长度至少6位，建议包含字母和数字</span>
          </div>
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="form.confirmPassword" type="password" placeholder="请再次输入密码" clearable size="large"
            show-password @keyup.enter="onSubmit">
            <template #prefix>
              <el-icon>
                <Lock />
              </el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item prop="agreement">
          <el-checkbox v-model="form.agreement">
            我已阅读并同意
            <el-button type="text" @click="showUserAgreement">《用户协议》</el-button>
            和
            <el-button type="text" @click="showPrivacyPolicy">《隐私政策》</el-button>
          </el-checkbox>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" class="register-btn" @click="onSubmit" size="large" :loading="loading">
            {{ loading ? '注册中...' : '立即注册' }}
          </el-button>

          <div class="login-section">
            <span>已有账号？</span>
            <el-button type="text" class="login-link" @click="goToLogin">
              立即登录
            </el-button>
          </div>
        </el-form-item>
      </el-form>
    </div>

    <!-- 用户协议弹窗 -->
    <el-dialog v-model="agreementVisible" title="用户协议" width="600px" :before-close="closeAgreement">
      <div class="agreement-content">
        <h3>服务条款</h3>
        <p>1. 用户在使用本服务时，必须遵守相关法律法规。</p>
        <p>2. 禁止上传包含违法、违规、侵权内容的音频文件。</p>
        <p>3. 用户对自己上传的内容承担全部责任。</p>
        <p>4. 平台有权对违规内容进行处理。</p>

        <h3>知识产权</h3>
        <p>1. 用户保证拥有上传音频的合法权利。</p>
        <p>2. 生成的语音模型归用户所有。</p>
        <p>3. 平台技术和服务受知识产权保护。</p>

        <h3>免责声明</h3>
        <p>1. 平台不对用户内容的准确性负责。</p>
        <p>2. 用户自行承担使用风险。</p>
        <p>3. 平台保留修改服务条款的权利。</p>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="agreementVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 隐私政策弹窗 -->
    <el-dialog v-model="privacyVisible" title="隐私政策" width="600px" :before-close="closePrivacy">
      <div class="privacy-content">
        <h3>信息收集</h3>
        <p>1. 我们收集您提供的注册信息和上传的音频文件。</p>
        <p>2. 自动收集使用数据和设备信息。</p>
        <p>3. 通过Cookie等技术收集浏览信息。</p>

        <h3>信息使用</h3>
        <p>1. 提供和改进服务功能。</p>
        <p>2. 进行数据分析和用户研究。</p>
        <p>3. 发送服务通知和更新。</p>

        <h3>信息保护</h3>
        <p>1. 采用行业标准的安全措施保护数据。</p>
        <p>2. 不会向第三方出售个人信息。</p>
        <p>3. 用户可以要求删除个人数据。</p>

        <h3>联系我们</h3>
        <p>如有隐私相关问题，请发送邮件至 privacy@example.com</p>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="privacyVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Message, Lock } from '@element-plus/icons-vue'
import { authAPI } from '@/api'

const router = useRouter()

const formRef = ref(null)
const loading = ref(false)
const agreementVisible = ref(false)
const privacyVisible = ref(false)

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  agreement: false
})

// 自定义验证规则
const validatePassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请输入密码'))
  } else if (value.length < 6) {
    callback(new Error('密码长度不能少于6位'))
  } else {
    if (form.confirmPassword !== '') {
      formRef.value.validateField('confirmPassword')
    }
    callback()
  }
}

const validateConfirmPassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== form.password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const validateAgreement = (rule, value, callback) => {
  if (!value) {
    callback(new Error('请阅读并同意用户协议和隐私政策'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度在 2 到 20 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_\u4e00-\u9fa5]+$/, message: '用户名只能包含字母、数字、下划线和中文', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { validator: validatePassword, trigger: 'blur' }
  ],
  confirmPassword: [
    { validator: validateConfirmPassword, trigger: 'blur' }
  ],
  agreement: [
    { validator: validateAgreement, trigger: 'change' }
  ]
}

// 注册提交
const onSubmit = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      const res = await authAPI.register({
        username: form.username,
        email: form.email,
        password: form.password
      })

      ElMessage.success('注册成功！请前往邮箱验证后登录')

      // 跳转到登录页面，并携带注册成功的用户名
      router.push({
        name: 'Login',
        query: {
          username: form.username,
          message: 'register_success'
        }
      })
    } catch (error) {
      console.error('注册失败:', error)
      const errorMessage = error?.response?.data?.message || '注册失败，请重试'
      ElMessage.error(errorMessage)
    } finally {
      loading.value = false
    }
  })
}

// 跳转登录
const goToLogin = () => {
  router.push({ name: 'Login' })
}

// 显示用户协议
const showUserAgreement = () => {
  agreementVisible.value = true
}

// 关闭用户协议
const closeAgreement = () => {
  agreementVisible.value = false
}

// 显示隐私政策
const showPrivacyPolicy = () => {
  privacyVisible.value = true
}

// 关闭隐私政策
const closePrivacy = () => {
  privacyVisible.value = false
}
</script>

<style scoped>
.register-bg {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  padding: 20px 0;
}

.register-bg::before {
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

.register-wrapper {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 480px;
  max-width: 90vw;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  z-index: 1;
  border: 1px solid rgba(255, 255, 255, 0.2);
  max-height: 90vh;
  overflow-y: auto;
}

.register-logo {
  display: flex;
  align-items: center;
  margin-bottom: 32px;
}

.register-logo img {
  width: 48px;
  height: 48px;
  margin-right: 16px;
}

.register-logo span {
  font-size: 24px;
  font-weight: 700;
  color: #333;
  letter-spacing: 1px;
}

.register-form {
  width: 100%;
}

.el-form-item {
  margin-bottom: 20px;
}

.password-tips {
  margin-top: 4px;
  font-size: 12px;
  color: #999;
}

.register-btn {
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

.register-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

.register-btn:active {
  transform: translateY(0);
}

.login-section {
  width: 100%;
  text-align: center;
  margin-top: 20px;
  color: #666;
  font-size: 14px;
}

.login-link {
  color: #667eea;
  font-weight: 600;
  margin-left: 8px;
}

.login-link:hover {
  color: #764ba2;
  text-decoration: underline;
}

.agreement-content,
.privacy-content {
  max-height: 400px;
  overflow-y: auto;
  line-height: 1.6;
}

.agreement-content h3,
.privacy-content h3 {
  color: #333;
  margin: 16px 0 8px 0;
  font-size: 16px;
}

.agreement-content p,
.privacy-content p {
  margin: 8px 0;
  color: #666;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .register-wrapper {
    width: 95%;
    padding: 24px;
    margin: 10px;
  }

  .register-logo span {
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
  line-height: 1.4;
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