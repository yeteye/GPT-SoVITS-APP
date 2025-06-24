<template>
  <div class="register-bg">
    <div class="register-wrapper">
      <div class="register-logo">
        <img src="/favicon.ico" alt="logo" />
        <span>GPT-SoVITS 注册</span>
      </div>
      <el-form :model="form" :rules="rules" ref="formRef" class="register-form" label-position="top">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" clearable size="large" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" clearable size="large" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" clearable size="large" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onSubmit" class="register-btn" size="large">注册</el-button>
          <el-button type="text" @click="goToLogin" class="login-link">已有账号？登录</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from '@/utils/request'

const router = useRouter()
const formRef = ref(null)

const form = reactive({
  username: '',
  email: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const onSubmit = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      const res = await axios.post('/auth/register', {
        username: form.username,
        email: form.email,
        password: form.password
      })
      ElMessage.success('注册成功，请登录')
      router.push({ name: 'Login' })
    } catch (err) {
      ElMessage.error(err?.response?.data?.message || '注册失败')
    }
  })
}

function goToLogin() {
  router.push({ name: 'Login' })
}
</script>

<style scoped>
.register-bg {
  min-height: 100vh;
  background: linear-gradient(135deg, #e0e7ff 0%, #f5f5f5 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.register-wrapper {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);
  padding: 48px 36px;
  width: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.register-logo {
  display: flex;
  align-items: center;
  margin-bottom: 32px;
}

.register-logo img {
  width: 40px;
  height: 40px;
  margin-right: 12px;
}

.register-logo span {
  font-size: 22px;
  font-weight: 600;
  color: #333;
}

.register-form {
  width: 100%;
}

.el-form-item {
  margin-bottom: 24px;
}

.register-btn {
  width: 100%;
  font-size: 16px;
  border-radius: 8px;
}

.login-link {
  display: block;
  text-align: center;
  margin-top: 10px;
  color: #409eff;
}
</style>
