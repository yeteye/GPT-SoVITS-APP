<template>
  <div class="admin-page">
    <h2>用户管理</h2>
    <el-table :data="users" style="width: 100%" border>
      <el-table-column prop="id" label="用户ID" width="100" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column prop="role" label="角色" width="120" />
      <el-table-column prop="status" label="状态" width="120" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="editUser(row)">编辑</el-button>
          <el-button type="danger" size="small" @click="banUser(row)">封禁</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const users = ref([
  { id: 1, email: 'user1@example.com', role: '用户', status: '正常' },
  { id: 2, email: 'admin@example.com', role: '管理员', status: '正常' }
])

function editUser(user) {
  console.log('编辑用户', user)
}

function banUser(user) {
  console.log('封禁用户', user)
}
</script>

<style scoped>
.admin-page {
  padding: 20px;
}
</style>
