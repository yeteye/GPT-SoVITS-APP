<!-- ./gpt-sovits-frontend/src/views/admin/SystemLog.vue -->
<template>
  <div class="admin-page">
    <h2>系统日志</h2>

    <!-- 筛选区域 -->
    <div class="filters">
      <el-input v-model="keyword" placeholder="搜索关键字" prefix-icon="el-icon-search" @keyup.enter="search" clearable />
      <el-select v-model="level" placeholder="日志级别" clearable>
        <el-option label="INFO" value="INFO" />
        <el-option label="WARN" value="WARN" />
        <el-option label="ERROR" value="ERROR" />
      </el-select>
      <el-button type="primary" @click="search">查询</el-button>
    </div>

    <!-- 日志表格 -->
    <el-table :data="filteredLogs" border style="width: 100%; margin-top: 20px;">
      <el-table-column prop="timestamp" label="时间" width="180" />
      <el-table-column prop="level" label="级别" width="100" />
      <el-table-column prop="module" label="模块" width="120" />
      <el-table-column prop="message" label="日志内容" />
    </el-table>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const logs = ref([
  {
    timestamp: '2025-06-17 14:23:45',
    level: 'INFO',
    module: '用户登录',
    message: '用户 admin 登录成功'
  },
  {
    timestamp: '2025-06-17 14:25:02',
    level: 'WARN',
    module: '音色审核',
    message: '模型 #102 审核超时'
  },
  {
    timestamp: '2025-06-17 14:28:10',
    level: 'ERROR',
    module: '任务调度',
    message: '任务执行失败，错误代码 500'
  }
])

const keyword = ref('')
const level = ref('')

const filteredLogs = computed(() => {
  return logs.value.filter(log => {
    const matchKeyword =
      !keyword.value ||
      log.message.includes(keyword.value) ||
      log.module.includes(keyword.value)
    const matchLevel = !level.value || log.level === level.value
    return matchKeyword && matchLevel
  })
})

function search() {
  // 当前筛选逻辑已由 computed 实现，无需额外处理
}
</script>

<style scoped>
.admin-page {
  padding: 20px;
}

.filters {
  display: flex;
  gap: 12px;
  margin-bottom: 10px;
  align-items: center;
}
</style>
