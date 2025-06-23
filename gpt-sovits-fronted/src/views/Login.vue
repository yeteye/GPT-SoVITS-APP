<template>
  <div class="login-bg">
    <div class="login-wrapper">
      <div class="login-logo">
        <img src="/favicon.ico" alt="logo" />
        <span>GPT-SoVITS 登录</span>
      </div>
      <el-form :model="form" :rules="rules" ref="formRef" class="login-form" label-position="top">
        <el-form-item label="用户名" prop="identifier">
          <el-input v-model="form.identifier" placeholder="请输入用户名" clearable size="large" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" clearable size="large" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" class="login-btn" @click="onSubmit" size="large">登录</el-button>
          <el-button type="text" class="register-link" @click="goToRegister">没有账号？去注册</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request' // 自定义的 axios 封装

const router = useRouter()

const formRef = ref(null)
const form = reactive({
  identifier: '',
  password: ''
})

const rules = {
  identifier: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const onSubmit = () => {
  formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const res = await request.post('/auth/login', {
          identifier: form.identifier,
          password: form.password
        })
        // console.log('登录请求结果:', res)
        // 假设 token 返回在 res.data.access_token 中
        if (res && res.data.access_token) {
          // console.log('登录成功:', res.data)
          localStorage.setItem('token', res.data.access_token)
          ElMessage.success('登录成功')
          router.push({ name: 'Home' }) // 登录后跳转页面
        } else {
          ElMessage.error('登录失败，返回数据缺少 token')
        }
      } catch (err) {
        ElMessage.error('登录失败，请检查用户名或密码')
      }
    }
  })
}

const goToRegister = () => {
  router.push({ name: 'Register' })
}
</script>

<style scoped>
.login-bg {
  min-height: 100vh;
  background: linear-gradient(135deg, #e0e7ff 0%, #f5f5f5 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-wrapper {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
  padding: 48px 36px 32px 36px;
  width: 380px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.login-logo {
  display: flex;
  align-items: center;
  margin-bottom: 32px;
}

.login-logo img {
  width: 40px;
  height: 40px;
  margin-right: 12px;
}

.login-logo span {
  font-size: 22px;
  font-weight: 600;
  color: #333;
  letter-spacing: 1px;
}

.login-form {
  width: 100%;
}

.el-form-item {
  margin-bottom: 24px;
}

.login-btn {
  width: 100%;
  font-size: 16px;
  letter-spacing: 2px;
  border-radius: 8px;
  height: 44px;
  background: linear-gradient(90deg, #409eff 0%, #66b1ff 100%);
  border: none;
  color: #fff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.15);
}

.login-btn:hover {
  background: linear-gradient(90deg, #66b1ff 0%, #409eff 100%);
}

.register-link {
  width: 100%;
  text-align: center;
  color: #409eff;
  font-size: 15px;
  margin-top: 10px;
  letter-spacing: 1px;
}

.register-link:hover {
  color: #66b1ff;
  text-decoration: underline;
}
</style>
