<template>
  <div class="admin-page">
    <h2>音色模型审核</h2>
    <el-table :data="models" style="width: 100%" border>
      <el-table-column prop="id" label="模型ID" width="100" />
      <el-table-column prop="name" label="模型名称" />
      <el-table-column prop="creator" label="创建者" />
      <el-table-column prop="status" label="审核状态" width="120" />
      <el-table-column label="操作" width="220">
        <template #default="{ row }">
          <el-button type="success" size="small" @click="approve(row)">通过</el-button>
          <el-button type="warning" size="small" @click="reject(row)">驳回</el-button>
          <el-button type="info" size="small" @click="viewDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const models = ref([
  { id: 101, name: '角色A音色', creator: 'user1@example.com', status: '待审核' },
  { id: 102, name: '角色B音色', creator: 'creator@example.com', status: '已通过' }
])

function approve(model) {
  console.log('审核通过', model)
}

function reject(model) {
  console.log('审核驳回', model)
}

function viewDetail(model) {
  console.log('查看详情', model)
}
</script>

<style scoped>
.admin-page {
  padding: 20px;
}
</style>
