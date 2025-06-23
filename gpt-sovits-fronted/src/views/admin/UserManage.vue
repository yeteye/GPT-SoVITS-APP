<template>
  <div class="admin-page">
    <h2>用户管理</h2>

    <!-- 搜索区域 -->
    <el-form :inline="true" class="search-bar" @submit.prevent>
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

      <el-form-item>
        <el-button type="primary" @click="fetchUsers">搜索</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 用户表格 -->
    <el-table :data="users" v-loading="loading" border style="width: 100%; margin-top: 20px;">
      <el-table-column prop="id" label="用户ID" width="200" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column label="角色" width="120">
        <template #default="{ row }">{{ roleMap[row.role] || '未知角色' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="120">
        <template #default="{ row }">{{ row.is_active ? '正常' : '已封禁' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="editUser(row)">编辑</el-button>
          <el-button type="danger" size="small" @click="banUser(row)">封禁</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页器 -->
    <div class="pagination">
      <el-pagination
        layout="prev, pager, next, sizes, total"
        :total="pagination.total"
        :current-page="pagination.page"
        :page-size="pagination.per_page"
        :page-sizes="[10, 20, 50]"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const users = ref([])
const loading = ref(false)

const roleMap = { 0: '用户', 1: '审核员', 2: '管理员' }

const filters = ref({
  role: null,
  is_active: null
})

const pagination = ref({
  page: 1,
  per_page: 10,
  total: 0
})

function fetchUsers() {
  loading.value = true
  request
    .get('/admin/users', {
      params: {
        page: pagination.value.page,
        per_page: pagination.value.per_page,
        role: filters.value.role,
        is_active: filters.value.is_active
      }
    })
    .then((res) => {
      // 根据实际结构调整字段名
      users.value = res.data.users || res.data.data || []
      pagination.value.total = res.data.total || 0
    })
    .catch((err) => {
      ElMessage.error(err?.response?.data?.message || '获取用户列表失败')
    })
    .finally(() => {
      loading.value = false
    })
}

function resetFilters() {
  filters.value.role = null
  filters.value.is_active = null
  pagination.value.page = 1
  fetchUsers()
}

function handlePageChange(newPage) {
  pagination.value.page = newPage
  fetchUsers()
}

function handleSizeChange(newSize) {
  pagination.value.per_page = newSize
  pagination.value.page = 1
  fetchUsers()
}

function editUser(user) {
  console.log('编辑用户', user)
}

function banUser(user) {
  console.log('封禁用户', user)
}

onMounted(fetchUsers)
</script>

<style scoped>
.admin-page {
  padding: 20px;
}
.search-bar {
  margin-bottom: 10px;
}
.pagination {
  margin-top: 20px;
  text-align: right;
}
</style>
