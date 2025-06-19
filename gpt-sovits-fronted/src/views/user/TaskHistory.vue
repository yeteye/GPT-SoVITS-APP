<template>
  <div class="task-history">
    <h2>任务与历史记录</h2>
    <el-table :data="tasks" style="width: 100%">
      <el-table-column prop="type" label="任务类型" width="120" />
      <el-table-column prop="status" label="状态" width="120" />
      <el-table-column prop="createdAt" label="提交时间" />
    </el-table>
  </div>
</template>

<script setup>
const tasks = [
  { type: '克隆', status: '已完成', createdAt: '2025-06-17 10:23' },
  { type: '合成', status: '排队中', createdAt: '2025-06-17 10:35' }
]
</script>

<style scoped>
.task-history {
  padding: 24px;
}
</style>
