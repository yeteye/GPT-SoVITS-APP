<!-- ./gpt-sovits-frontend/src/views/admin/SystemLog.vue - API版本 -->
<template>
  <div class="system-log-page">
    <div class="page-header">
      <h2>系统日志</h2>
      <p>查看和管理系统运行日志</p>
    </div>

    <!-- 筛选区域 -->
    <el-card class="filter-card" shadow="hover">
      <div class="filters">
        <div class="filter-group">
          <el-input v-model="filters.keyword" placeholder="搜索关键字" clearable style="width: 250px"
            @keyup.enter="fetchLogs">
            <template #prefix>
              <el-icon>
                <Search />
              </el-icon>
            </template>
          </el-input>

          <el-select v-model="filters.action" placeholder="操作类型" clearable style="width: 150px">
            <el-option label="全部" value="" />
            <el-option label="登录" value="login" />
            <el-option label="注册" value="register" />
            <el-option label="上传" value="upload" />
            <el-option label="创建" value="create" />
            <el-option label="更新" value="update" />
            <el-option label="删除" value="delete" />
            <el-option label="审核" value="review" />
          </el-select>

          <el-select v-model="filters.resource_type" placeholder="资源类型" clearable style="width: 150px">
            <el-option label="全部" value="" />
            <el-option label="用户" value="user" />
            <el-option label="模型" value="model" />
            <el-option label="任务" value="task" />
            <el-option label="上传文件" value="upload" />
            <el-option label="水印" value="watermark" />
          </el-select>

          <el-input v-model="filters.user_id" placeholder="用户ID" clearable style="width: 200px" />

          <el-date-picker v-model="filters.dateRange" type="datetimerange" range-separator="至" start-placeholder="开始时间"
            end-placeholder="结束时间" format="YYYY-MM-DD HH:mm:ss" value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 350px" />
        </div>

        <div class="filter-actions">
          <el-button type="primary" @click="fetchLogs" :loading="loading">
            <el-icon>
              <Search />
            </el-icon>
            查询
          </el-button>
          <el-button @click="resetFilters">
            <el-icon>
              <Refresh />
            </el-icon>
            重置
          </el-button>
          <el-button @click="exportLogs" :loading="exporting">
            <el-icon>
              <Download />
            </el-icon>
            导出
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 日志统计 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon total">
              <el-icon>
                <Document />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ logStats.total || 0 }}</div>
              <div class="stat-label">总日志数</div>
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
              <div class="stat-number">{{ logStats.today || 0 }}</div>
              <div class="stat-label">今日新增</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon users">
              <el-icon>
                <User />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ logStats.unique_users || 0 }}</div>
              <div class="stat-label">活跃用户</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon actions">
              <el-icon>
                <Operation />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ logStats.actions || 0 }}</div>
              <div class="stat-label">操作类型</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 日志表格 -->
    <el-card class="table-card" shadow="hover">
      <el-table :data="logs" v-loading="loading" style="width: 100%" @row-click="viewLogDetail">
        <el-table-column prop="id" label="ID" width="80" />

        <el-table-column prop="created_at" label="时间" width="180" sortable>
          <template #default="{ row }">
            <div class="timestamp">
              <el-icon>
                <Clock />
              </el-icon>
              {{ formatTime(row.created_at) }}
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="action" label="操作" width="100">
          <template #default="{ row }">
            <el-tag :type="getActionType(row.action)" size="small">
              {{ getActionDisplay(row.action) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="resource_type" label="资源类型" width="120">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">
              {{ getResourceDisplay(row.resource_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="user_name" label="用户" width="120">
          <template #default="{ row }">
            <span v-if="row.user_name">{{ row.user_name }}</span>
            <span v-else class="system-user">系统</span>
          </template>
        </el-table-column>

        <el-table-column prop="resource_id" label="资源ID" width="150">
          <template #default="{ row }">
            <span v-if="row.resource_id">{{ row.resource_id }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column prop="ip_address" label="IP地址" width="130">
          <template #default="{ row }">
            <span v-if="row.ip_address">{{ row.ip_address }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column prop="details" label="详情" min-width="200">
          <template #default="{ row }">
            <div class="log-details" :title="row.details">
              {{ row.details || '无详情' }}
            </div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="text" size="small" @click.stop="viewLogDetail(row)">
              <el-icon>
                <View />
              </el-icon>
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.per_page"
          :page-sizes="[20, 50, 100, 200]" :total="pagination.total" layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange" @current-change="handleCurrentChange" />
      </div>
    </el-card>

    <!-- 日志详情弹窗 -->
    <el-dialog v-model="detailVisible" title="日志详情" width="800px">
      <div v-if="selectedLog" class="log-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="日志ID">
            {{ selectedLog.id }}
          </el-descriptions-item>
          <el-descriptions-item label="时间">
            {{ formatTime(selectedLog.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="操作">
            <el-tag :type="getActionType(selectedLog.action)">
              {{ getActionDisplay(selectedLog.action) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="资源类型">
            {{ getResourceDisplay(selectedLog.resource_type) }}
          </el-descriptions-item>
          <el-descriptions-item label="用户">
            {{ selectedLog.user_name || selectedLog.user_id || '系统' }}
          </el-descriptions-item>
          <el-descriptions-item label="用户ID">
            {{ selectedLog.user_id || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="资源ID">
            {{ selectedLog.resource_id || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="IP地址">
            {{ selectedLog.ip_address || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="用户代理" :span="2">
            {{ selectedLog.user_agent || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="详情" :span="2">
            <div class="log-content">{{ selectedLog.details || '无详情' }}</div>
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedLog.metadata" label="元数据" :span="2">
            <pre class="metadata">{{ formatMetadata(selectedLog.metadata) }}</pre>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="primary" @click="copyLogDetail">复制详情</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Search,
  Refresh,
  Download,
  Document,
  Calendar,
  User,
  Operation,
  Clock,
  View
} from '@element-plus/icons-vue'
import { adminAPI } from '@/api'

// 响应式数据
const loading = ref(false)
const exporting = ref(false)
const detailVisible = ref(false)
const logs = ref([])
const selectedLog = ref(null)

// 筛选条件
const filters = reactive({
  keyword: '',
  action: '',
  resource_type: '',
  user_id: '',
  dateRange: []
})

// 分页
const pagination = reactive({
  page: 1,
  per_page: 50,
  total: 0
})

// 日志统计
const logStats = ref({
  total: 0,
  today: 0,
  unique_users: 0,
  actions: 0
})

// 获取日志数据
async function fetchLogs() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page,
      action: filters.action || undefined,
      resource_type: filters.resource_type || undefined,
      user_id: filters.user_id || undefined,
      start_time: filters.dateRange?.[0],
      end_time: filters.dateRange?.[1]
    }

    const res = await adminAPI.getAuditLogs(params)

    if (res.data) {
      logs.value = res.data.logs || []
      pagination.total = res.data.pagination?.total || 0

      // 计算统计信息
      calculateStats()
    }
  } catch (error) {
    console.error('获取日志失败:', error)
    ElMessage.error('获取日志失败')
  } finally {
    loading.value = false
  }
}

// 计算统计信息
function calculateStats() {
  const today = new Date().toDateString()
  const uniqueUsers = new Set()
  const actions = new Set()
  let todayCount = 0

  logs.value.forEach(log => {
    if (log.user_id) {
      uniqueUsers.add(log.user_id)
    }
    if (log.action) {
      actions.add(log.action)
    }
    if (new Date(log.created_at).toDateString() === today) {
      todayCount++
    }
  })

  logStats.value = {
    total: pagination.total,
    today: todayCount,
    unique_users: uniqueUsers.size,
    actions: actions.size
  }
}

// 重置筛选条件
function resetFilters() {
  filters.keyword = ''
  filters.action = ''
  filters.resource_type = ''
  filters.user_id = ''
  filters.dateRange = []
  pagination.page = 1
  fetchLogs()
}

// 导出日志
async function exportLogs() {
  try {
    exporting.value = true

    const params = {
      action: filters.action || undefined,
      resource_type: filters.resource_type || undefined,
      user_id: filters.user_id || undefined,
      start_time: filters.dateRange?.[0],
      end_time: filters.dateRange?.[1],
      format: 'csv'
    }

    // 模拟导出功能
    ElMessage.success('日志导出功能开发中')

  } catch (error) {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

// 查看日志详情
function viewLogDetail(row) {
  selectedLog.value = row
  detailVisible.value = true
}

// 复制日志详情
function copyLogDetail() {
  if (!selectedLog.value) return

  const detail = `
日志ID: ${selectedLog.value.id}
时间: ${formatTime(selectedLog.value.created_at)}
操作: ${getActionDisplay(selectedLog.value.action)}
资源类型: ${getResourceDisplay(selectedLog.value.resource_type)}
用户: ${selectedLog.value.user_name || selectedLog.value.user_id || '系统'}
IP地址: ${selectedLog.value.ip_address || '-'}
详情: ${selectedLog.value.details || '无详情'}
${selectedLog.value.metadata ? `\n元数据:\n${formatMetadata(selectedLog.value.metadata)}` : ''}
  `.trim()

  navigator.clipboard.writeText(detail).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

// 分页处理
function handleSizeChange(size) {
  pagination.per_page = size
  pagination.page = 1
  fetchLogs()
}

function handleCurrentChange(page) {
  pagination.page = page
  fetchLogs()
}

// 工具函数
function getActionType(action) {
  const typeMap = {
    'login': 'success',
    'register': 'info',
    'create': 'primary',
    'update': 'warning',
    'delete': 'danger',
    'upload': 'info',
    'review': 'warning'
  }
  return typeMap[action] || ''
}

function getActionDisplay(action) {
  const actionMap = {
    'login': '登录',
    'register': '注册',
    'create': '创建',
    'update': '更新',
    'delete': '删除',
    'upload': '上传',
    'review': '审核',
    'logout': '登出'
  }
  return actionMap[action] || action
}

function getResourceDisplay(resourceType) {
  const resourceMap = {
    'user': '用户',
    'model': '模型',
    'task': '任务',
    'upload': '上传文件',
    'watermark': '水印'
  }
  return resourceMap[resourceType] || resourceType
}

function formatTime(timeStr) {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString()
}

function formatMetadata(metadata) {
  if (!metadata) return ''
  try {
    if (typeof metadata === 'string') {
      return JSON.stringify(JSON.parse(metadata), null, 2)
    }
    return JSON.stringify(metadata, null, 2)
  } catch {
    return metadata
  }
}

onMounted(() => {
  fetchLogs()
})
</script>

<style scoped>
.system-log-page {
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

.filter-card {
  margin-bottom: 20px;
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.filters {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.filter-group {
  display: flex;
  gap: 12px;
  flex: 1;
  align-items: center;
  flex-wrap: wrap;
}

.filter-actions {
  display: flex;
  gap: 8px;
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

.stat-icon.today {
  background: linear-gradient(135deg, #67c23a 0%, #529b2e 100%);
}

.stat-icon.users {
  background: linear-gradient(135deg, #e6a23c 0%, #d3901a 100%);
}

.stat-icon.actions {
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

.table-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.timestamp {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.log-details {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

.system-user {
  color: #909399;
  font-style: italic;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.log-detail {
  padding: 16px 0;
}

.log-content {
  line-height: 1.6;
  word-break: break-all;
}

.metadata {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.4;
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .system-log-page {
    padding: 16px;
  }

  .filters {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .filter-group {
    flex-direction: column;
    gap: 8px;
  }

  .filter-actions {
    justify-content: center;
  }

  .stats-row .el-col {
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