<template>
  <el-container class="user-center">
    <el-header class="header">
      <h2>个人中心</h2>
      <div class="header-actions">
        <el-button type="primary" size="small" @click="openChangePwdDialog">修改密码</el-button>
        <el-button type="danger" size="small" @click="logout">退出登录</el-button>
      </div>
    </el-header>

    <el-main>
      <el-card class="user-info">
        <template #header>
          <span>账户信息</span>
        </template>
        <p><strong>邮箱：</strong>{{ user.email }}</p>
        <p><strong>用户名：</strong>{{ user.username }}</p>
        <p><strong>角色：</strong>{{ roleText }}</p>
      </el-card>

      <el-card class="user-actions" style="margin-top: 20px;">
        <template #header>
          <span>快捷操作</span>
        </template>
        <el-button type="primary" @click="goToTasks">查看任务记录</el-button>
        <el-button type="success" @click="goToVoice">管理我的音色</el-button>
      </el-card>
    </el-main>

    <!-- 修改密码弹窗 -->
    <el-dialog title="修改密码" v-model="pwdDialogVisible" width="400px">
      <el-form :model="pwdForm" :rules="pwdRules" ref="pwdFormRef" label-width="100px">
        <el-form-item label="原密码" prop="current_password">
          <el-input v-model="pwdForm.current_password" type="password" autocomplete="off" />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="pwdForm.new_password" type="password" autocomplete="off" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitChangePwd">确认修改</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const router = useRouter()

// 获取本地存储的用户信息
const user = ref({ email: '', username: '', role: 0 })
const roleText = computed(() => {
  const map = { 0: '普通用户', 1: '审核员', 2: '管理员' }
  return map[user.value.role] || '未知角色'
})

onMounted(() => {
  const storedUser = localStorage.getItem('user')
  if (storedUser) {
    user.value = JSON.parse(storedUser)
  } else {
    ElMessage.warning('请先登录')
    router.push({ name: 'Login' })
  }
})

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  ElMessage.success('已退出登录')
  router.push({ name: 'Login' })
}

function goToTasks() {
  router.push({ name: 'TaskHistory' })
}

function goToVoice() {
  router.push({ name: 'VoiceLibrary' })
}

// 修改密码逻辑
const pwdDialogVisible = ref(false)
const pwdForm = ref({
  current_password: '',
  new_password: ''
})
const pwdRules = {
  current_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [{ required: true, message: '请输入新密码', trigger: 'blur' }]
}
const pwdFormRef = ref(null)

function openChangePwdDialog() {
  pwdDialogVisible.value = true
  pwdForm.value.current_password = ''
  pwdForm.value.new_password = ''
}

function submitChangePwd() {
  pwdFormRef.value.validate((valid) => {
    if (!valid) return
    request.post('/auth/change-password', pwdForm.value)
      .then(() => {
        ElMessage.success('密码修改成功，请重新登录')
        logout()
      })
      .catch(err => {
        ElMessage.error(err?.response?.data?.message || '修改失败')
      })
  })
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
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.user-info,
.user-actions {
  background: #fff;
}
.header-actions {
  display: flex;
  gap: 10px;
}
</style>
