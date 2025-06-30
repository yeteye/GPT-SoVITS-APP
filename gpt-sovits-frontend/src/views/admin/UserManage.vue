<!-- ./gpt-sovits-frontend/src/views/admin/UserManage.vue - 增强版 -->
<template>
  <div class="user-manage-page">
    <div class="page-header">
      <h2>用户管理</h2>
      <p>管理系统中的所有用户信息</p>
    </div>

    <!-- 用户统计 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon total">
              <el-icon>
                <User />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ userStats.total || 0 }}</div>
              <div class="stat-label">总用户数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon active">
              <el-icon>
                <Check />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ userStats.active || 0 }}</div>
              <div class="stat-label">活跃用户</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon admin">
              <el-icon>
                <UserFilled />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ userStats.admins || 0 }}</div>
              <div class="stat-label">管理员</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon today">
              <el-icon>
                <Calendar />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ userStats.new_today || 0 }}</div>
              <div class="stat-label">今日新增</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 搜索区域 -->
    <el-card class="search-card" shadow="hover">
      <el-form :inline="true" class="search-form" @submit.prevent>
        <el-form-item label="用户名/邮箱">
          <el-input v-model="filters.search" placeholder="搜索用户名或邮箱" clearable style="width: 200px"
            @keyup.enter="fetchUsers" />
        </el-form-item>

        <el-form-item label="角色">
          <el-select v-model="filters.role" placeholder="全部角色" clearable style="width: 150px">
            <el-option label="用户" :value="0" />
            <el-option label="审核员" :value="1" />
            <el-option label="管理员" :value="2" />
          </el-select>
        </el-form-item>

        <el-form-item label="状态">
          <el-select v-model="filters.is_active" placeholder="全部状态" clearable style="width: 150px">
            <el-option label="正常" :value="true" />
            <el-option label="已封禁" :value="false" />
          </el-select>
        </el-form-item>

        <el-form-item label="注册时间">
          <el-date-picker v-model="filters.dateRange" type="daterange" range-separator="至" start-placeholder="开始日期"
            end-placeholder="结束日期" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width: 240px" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="fetchUsers" :loading="loading">
            <el-icon>
              <Search />
            </el-icon>
            搜索
          </el-button>
          <el-button @click="resetFilters">
            <el-icon>
              <Refresh />
            </el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 用户表格 -->
    <el-card class="table-card" shadow="hover">
      <el-table :data="users" v-loading="loading" border style="width: 100%">
        <el-table-column prop="id" label="用户ID" width="200" show-overflow-tooltip />

        <el-table-column label="用户信息" width="250">
          <template #default="{ row }">
            <div class="user-info">
              <el-avatar :src="row.avatar_url" :size="32">
                {{ row.username?.charAt(0)?.toUpperCase() }}
              </el-avatar>
              <div class="user-details">
                <div class="username">{{ row.username }}</div>
                <div class="email">{{ row.email }}</div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)" size="small">
              {{ roleMap[row.role] || '未知角色' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '正常' : '已封禁' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="邮箱验证" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_verified ? 'success' : 'warning'" size="small">
              {{ row.is_verified ? '已验证' : '未验证' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="注册时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column prop="last_login_at" label="最后登录" width="180">
          <template #default="{ row }">
            {{ formatTime(row.last_login_at) || '未登录' }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="text" size="small" @click="viewUser(row)">
              <el-icon>
                <View />
              </el-icon>
              查看
            </el-button>
            <el-button type="text" size="small" @click="editUser(row)">
              <el-icon>
                <Edit />
              </el-icon>
              编辑
            </el-button>
            <el-button type="text" size="small" @click="toggleUserStatus(row)"
              :style="{ color: row.is_active ? '#f56c6c' : '#67c23a' }">
              <el-icon>
                <component :is="row.is_active ? 'Lock' : 'Unlock'" />
              </el-icon>
              {{ row.is_active ? '封禁' : '解封' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页器 -->
      <div class="pagination-wrapper">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.per_page"
          :page-sizes="[10, 20, 50, 100]" :total="pagination.total" layout="total, sizes, prev, pager, next, jumper"
          @current-change="handlePageChange" @size-change="handleSizeChange" />
      </div>
    </el-card>

    <!-- 用户详情弹窗 -->
    <el-dialog v-model="userDetailVisible" title="用户详情" width="700px">
      <div v-if="selectedUser" class="user-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用户ID">
            {{ selectedUser.id }}
          </el-descriptions-item>
          <el-descriptions-item label="用户名">
            {{ selectedUser.username }}
          </el-descriptions-item>
          <el-descriptions-item label="邮箱">
            {{ selectedUser.email }}
          </el-descriptions-item>
          <el-descriptions-item label="角色">
            <el-tag :type="getRoleType(selectedUser.role)">
              {{ roleMap[selectedUser.role] }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="selectedUser.is_active ? 'success' : 'danger'">
              {{ selectedUser.is_active ? '正常' : '已封禁' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="邮箱验证">
            <el-tag :type="selectedUser.is_verified ? 'success' : 'warning'">
              {{ selectedUser.is_verified ? '已验证' : '未验证' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="注册时间">
            {{ formatTime(selectedUser.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="最后登录">
            {{ formatTime(selectedUser.last_login_at) || '未登录' }}
          </el-descriptions-item>
          <el-descriptions-item label="头像" :span="2">
            <el-avatar :src="selectedUser.avatar_url" :size="64">
              {{ selectedUser.username?.charAt(0)?.toUpperCase() }}
            </el-avatar>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <template #footer>
        <el-button @click="userDetailVisible = false">关闭</el-button>
        <el-button type="primary" @click="editUser(selectedUser)">编辑用户</el-button>
      </template>
    </el-dialog>

    <!-- 编辑用户弹窗 -->
    <el-dialog v-model="editUserVisible" title="编辑用户" width="600px">
      <el-form :model="editForm" :rules="editRules" ref="editFormRef" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="editForm.username" placeholder="请输入用户名" />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model="editForm.email" placeholder="请输入邮箱" disabled />
          <div class="form-tip">邮箱不可修改</div>
        </el-form-item>

        <el-form-item label="角色" prop="role">
          <el-select v-model="editForm.role" placeholder="选择角色">
            <el-option label="用户" :value="0" />
            <el-option label="审核员" :value="1" />
            <el-option label="管理员" :value="2" />
          </el-select>
        </el-form-item>

        <el-form-item label="状态" prop="is_active">
          <el-switch v-model="editForm.is_active" active-text="正常" inactive-text="封禁" />
        </el-form-item>

        <el-form-item label="头像URL" prop="avatar_url">
          <el-input v-model="editForm.avatar_url" placeholder="请输入头像URL" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="editUserVisible = false">取消</el-button>
        <el-button type="primary" @click="submitUserEdit" :loading="editingUser">
          保存修改
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Refresh,
  User,
  UserFilled,
  Check,
  Calendar,
  View,
  Edit,
  Lock,
  Unlock
} from '@element-plus/icons-vue'
import { adminAPI } from '@/api'

const users = ref([])
const loading = ref(false)
const editingUser = ref(false)
const userDetailVisible = ref(false)
const editUserVisible = ref(false)
const selectedUser = ref(null)

const roleMap = { 0: '用户', 1: '审核员', 2: '管理员' }

const filters = reactive({
  search: '',
  role: null,
  is_active: null,
  dateRange: []
})

const pagination = reactive({
  page: 1,
  per_page: 20,
  total: 0
})

const editForm = reactive({
  username: '',
  email: '',
  role: 0,
  is_active: true,
  avatar_url: ''
})

const editRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度在 2 到 20 个字符', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

// 用户统计
const userStats = computed(() => {
  const stats = {
    total: users.value.length,
    active: 0,
    admins: 0,
    new_today: 0
  }

  const today = new Date().toDateString()

  users.value.forEach(user => {
    if (user.is_active) stats.active++
    if (user.role === 2) stats.admins++
    if (new Date(user.created_at).toDateString() === today) stats.new_today++
  })

  // 如果是分页数据，使用实际总数
  if (pagination.total > users.value.length) {
    stats.total = pagination.total
  }

  return stats
})

const editFormRef = ref()

async function fetchUsers() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page,
      role: filters.role,
      is_active: filters.is_active,
      search: filters.search || undefined,
      start_date: filters.dateRange?.[0],
      end_date: filters.dateRange?.[1]
    }

    const res = await adminAPI.getAllUsers(params)

    if (res.data) {
      users.value = res.data.users || []
      pagination.total = res.data.pagination?.total || 0
    }
  } catch (error) {
    console.error('获取用户列表失败:', error)
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.search = ''
  filters.role = null
  filters.is_active = null
  filters.dateRange = []
  pagination.page = 1
  fetchUsers()
}

function handlePageChange(newPage) {
  pagination.page = newPage
  fetchUsers()
}

function handleSizeChange(newSize) {
  pagination.per_page = newSize
  pagination.page = 1
  fetchUsers()
}

function viewUser(user) {
  selectedUser.value = user
  userDetailVisible.value = true
}

function editUser(user) {
  selectedUser.value = user
  Object.assign(editForm, {
    username: user.username,
    email: user.email,
    role: user.role,
    is_active: user.is_active,
    avatar_url: user.avatar_url || ''
  })
  editUserVisible.value = true
  userDetailVisible.value = false
}

async function submitUserEdit() {
  if (!editFormRef.value) return

  editFormRef.value.validate(async (valid) => {
    if (!valid) return

    editingUser.value = true
    try {
      // 更新用户角色
      if (editForm.role !== selectedUser.value.role) {
        await adminAPI.updateUserRole(selectedUser.value.id, {
          role: editForm.role.toString()
        })
      }

      // 更新用户状态
      if (editForm.is_active !== selectedUser.value.is_active) {
        await adminAPI.updateUserStatus(selectedUser.value.id, {
          is_active: editForm.is_active.toString()
        })
      }

      ElMessage.success('用户信息更新成功')
      editUserVisible.value = false
      fetchUsers()
    } catch (error) {
      console.error('用户信息更新失败:', error)
      ElMessage.error('用户信息更新失败: ' + (error?.response?.data?.message || '未知错误'))
    } finally {
      editingUser.value = false
    }
  })
}

async function toggleUserStatus(user) {
  try {
    const action = user.is_active ? '封禁' : '解封'
    await ElMessageBox.confirm(
      `确定要${action}用户 "${user.username}" 吗？`,
      '确认操作',
      {
        type: 'warning',
        confirmButtonText: `确认${action}`,
        cancelButtonText: '取消'
      }
    )

    await adminAPI.updateUserStatus(user.id, {
      is_active: (!user.is_active).toString()
    })

    ElMessage.success(`用户已${action}`)
    fetchUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

function getRoleType(role) {
  const typeMap = {
    0: '',
    1: 'warning',
    2: 'danger'
  }
  return typeMap[role] || ''
}

function formatTime(timeStr) {
  if (!timeStr) return ''
  return new Date(timeStr).toLocaleString()
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.user-manage-page {
  padding: 24px;
  background: #f8f9fb;
  min-height: 100vh;
}

.page-header {
  text-align: center;
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  font-size: 28px;
  color: #303133;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  color: #666;
  font-size: 16px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-icon.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.active {
  background: linear-gradient(135deg, #67c23a 0%, #529b2e 100%);
}

.stat-icon.admin {
  background: linear-gradient(135deg, #e6a23c 0%, #d3901a 100%);
}

.stat-icon.today {
  background: linear-gradient(135deg, #f56c6c 0%, #f25454 100%);
}

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.search-card {
  margin-bottom: 20px;
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.search-form {
  margin-bottom: 0;
}

.table-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-details {
  flex: 1;
}

.username {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.email {
  font-size: 12px;
  color: #909399;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.user-detail {
  padding: 16px 0;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .user-manage-page {
    padding: 16px;
  }

  .stats-row .el-col {
    margin-bottom: 12px;
  }

  .search-form .el-form-item {
    margin-bottom: 12px;
  }
}

/* Element Plus 样式覆盖 */
:deep(.el-card__body) {
  padding: 20px;
}

:deep(.el-table) {
  border-radius: 8px;
  overflow: hidden;
}

:deep(.el-dialog) {
  border-radius: 16px;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #409eff 0%, #2d8cf0 100%);
  border: none;
}

:deep(.el-tag) {
  border-radius: 8px;
}
</style>