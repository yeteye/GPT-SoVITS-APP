<template>
  <div class="login-bg">
    <div class="login-wrapper">
      <div class="login-logo">
        <img src="/favicon.ico" alt="logo" />
        <span>GPT-SoVITS 登录</span>
      </div>
      <el-form :model="form" :rules="rules" ref="formRef" class="login-form" label-position="top">
        <el-form-item label="邮箱" prop="email" class="el-form-item">
          <el-input v-model="form.email" placeholder="请输入邮箱" clearable size="large" style="width:100%; min-height: 15px;"  />
        </el-form-item>
        <el-form-item label="密码" prop="password" class="el-form-item">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" clearable size="large" style="width:100%" />
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
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const form = reactive({
  email: '',
  password: '',
});

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
};

const formRef = ref(null);

function onSubmit() {
  formRef.value.validate((valid) => {
    if (valid) {
      console.log('登录成功', form);
    } else {
      console.log('登录失败');
    }
  });
}

function goToRegister() {
  router.push({ name: 'Register' });
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
  width: 100%;
  min-height: 56px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.el-input__wrapper {
  border-radius: 8px !important;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.08);
  border: 1px solid #e0e7ff;
  background: #f8faff;
  transition: border-color 0.2s;
}
.el-input__wrapper:focus-within {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.15);
}
.el-input__inner {
  font-size: 16px;
  padding: 12px 14px;
  background: transparent;
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
  transition: background 0.2s, box-shadow 0.2s;
}
.login-btn:hover {
  background: linear-gradient(90deg, #66b1ff 0%, #409eff 100%);
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.18);
}
.register-link {
  width: 100%;
  text-align: center;
  color: #409eff;
  font-size: 15px;
  margin-top: 10px;
  margin-bottom: 0;
  letter-spacing: 1px;
}
.register-link:hover {
  color: #66b1ff;
  text-decoration: underline;
}
</style>
