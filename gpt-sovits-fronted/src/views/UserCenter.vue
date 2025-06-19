<template>
  <el-container class="user-center">
    <el-header class="header">
      <h2>个人中心</h2>
    </el-header>
    <el-main>
      <el-card class="user-info">
        <template #header>
          <span>账户信息</span>
        </template>
        <p><strong>邮箱：</strong>{{ user.email }}</p>
        <p><strong>用户名：</strong>{{ user.username }}</p>
        <p><strong>角色：</strong>{{ user.role }}</p>
      </el-card>

      <el-card class="user-actions" style="margin-top: 20px;">
        <template #header>
          <span>快捷操作</span>
        </template>
        <el-button type="primary" @click="goToTasks">查看任务记录</el-button>
        <el-button type="success" @click="goToVoice">管理我的音色</el-button>
      </el-card>
    </el-main>
  </el-container>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
const user = {
  email: 'user@example.com',
  username: '演示用户',
  role: '普通用户'
}

function goToTasks() {
  router.push({ name: 'TaskHistory' })
}
function goToVoice() {
  router.push({ name: 'VoiceLibrary' })
}
</script>

<style scoped>
.user-center {
  padding: 20px;
  background: #f8f9fa;
}
.header {
  background: #fff;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.user-info, .user-actions {
  background: #fff;
}
</style>
