<template>
  <el-container class="user-center">
    <el-header class="header">
      <h2>个人中心</h2>
      <div class="header-actions">
        <el-button type="primary" size="small" @click="openChangePwdDialog">修改密码</el-button>
        <el-button type="danger" size="small" @click="logout">退出登录</el-button>
        <el-button type="warning" size="small" @click="openDeleteDialog">注销账号</el-button>
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
        <!-- 只有管理员 role===2 时显示 -->
        <el-button
          v-if="user.role === 2"
          type="danger"
          @click="goToAdmin"
        >进入管理员界面</el-button>
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

    <!-- 注销账号弹窗 -->
    <el-dialog title="确认注销账号" v-model="deleteDialogVisible" width="400px">
      <el-form :model="deleteForm" :rules="deleteRules" ref="deleteFormRef" label-width="100px">
        <el-form-item label="密码" prop="password">
          <el-input v-model="deleteForm.password" type="password" autocomplete="off" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="deleteDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmDelete">确认注销</el-button>
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

// 用户信息
const user = ref({ email: '', username: '', role: 0 })
// 根据 role 转为文本
const roleText = computed(() => {
  const map = { 0: '普通用户', 1: '审核员', 2: '管理员' }
  return map[user.value.role] || '未知角色'
})

// 页面加载时获取用户信息
onMounted(() => {
  request.get('/user/profile')
    .then(res => {
      // 假定后端返回 { data: { profile: { email, username, role } } }
      if (res.data && res.data.profile) {
        user.value = res.data.profile
        localStorage.setItem('user', JSON.stringify(res.data.profile))
      } else {
        throw new Error('获取用户信息格式异常')
      }
    })
    .catch(() => {
      ElMessage.warning('请先登录')
      router.push({ name: 'Login' })
    })
})

// 退出登录
function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  ElMessage.success('已退出登录')
  router.push({ name: 'Login' })
}

// 注销账号相关
const deleteDialogVisible = ref(false)
const deleteForm = ref({ password: '' })
const deleteRules = {
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}
const deleteFormRef = ref(null)

function openDeleteDialog() {
  deleteDialogVisible.value = true
  deleteForm.value.password = ''
}

function confirmDelete() {
  deleteFormRef.value.validate((valid) => {
    if (!valid) return
    request.delete('/user/delete-account', { data: deleteForm.value })
      .then(() => {
        ElMessage.success('账号已删除')
        logout()
      })
      .catch(err => {
        ElMessage.error(err?.response?.data?.message || '删除失败')
      })
  })
}

// 快捷跳转
function goToTasks() {
  router.push({ name: 'TaskHistory' })
}
function goToVoice() {
  router.push({ name: 'VoiceLibrary' })
}
function goToAdmin() {
  // 确保路由中已配置 /admin 对应的管理员页面
  router.push({ path: '/admin' })
}

// 修改密码相关
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
