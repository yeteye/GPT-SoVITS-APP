<!-- src/views/admin/WatermarkAdmin.vue -->
<template>
  <div class="watermark-admin">
    <div class="page-header">
      <h2>水印系统管理</h2>
      <p>管理系统中所有的音频水印和验证记录</p>
    </div>

    <!-- 统计概览 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon total">
              <el-icon>
                <Document />
              </el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ stats.total_watermarks || 0 }}</div>
              <div class="stats-label">总水印数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon active">
              <el-icon>
                <Check />
              </el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ stats.active_watermarks || 0 }}</div>
              <div class="stats-label">活跃水印</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon verified">
              <el-icon>
                <Lock />
              </el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ stats.total_verifications || 0 }}</div>
              <div class="stats-label">验证总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon users">
              <el-icon>
                <User />
              </el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ stats.unique_users || 0 }}</div>
              <div class="stats-label">用户数量</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 水印管理 -->
    <el-card class="watermark-list-card">
      <template #header>
        <div class="card-header">
          <h3>水印列表</h3>
          <div class="header-filters">
            <el-input v-model="filters.username" placeholder="搜索用户名" clearable style="width: 200px" />
            <el-select v-model="filters.is_active" placeholder="状态" clearable style="width: 120px">
              <el-option label="活跃" :value="true" />
              <el-option label="已停用" :value="false" />
            </el-select>
            <el-button type="primary" @click="fetchWatermarks">
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
          </div>
        </div>
      </template>

      <el-table :data="watermarks" v-loading="watermarksLoading" row-key="id">
        <el-table-column prop="watermark_code" label="水印码" width="200">
          <template #default="{ row }">
            <el-tag type="info" effect="plain">{{ row.watermark_code }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="username" label="用户" width="150" />

        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />

        <el-table-column prop="model_name" label="关联模型" width="150" show-overflow-tooltip />

        <el-table-column prop="code_length" label="码长" width="80" />

        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '活跃' : '已停用' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="verification_count" label="验证次数" width="100" />

        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="text" size="small" @click="viewWatermarkDetail(row)">
              详情
            </el-button>
            <el-button type="text" size="small" @click="copyWatermarkCode(row)">
              复制码
            </el-button>
            <el-button type="text" size="small" @click="toggleWatermarkStatus(row)"
              :style="{ color: row.is_active ? '#f56c6c' : '#67c23a' }">
              {{ row.is_active ? '停用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.per_page"
          :page-sizes="[10, 20, 50, 100]" :total="pagination.total" layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange" @current-change="handleCurrentChange" />
      </div>
    </el-card>

    <!-- 验证日志 -->
    <el-card class="verification-logs-card">
      <template #header>
        <div class="card-header">
          <h3>验证日志</h3>
          <div class="header-filters">
            <el-input v-model="logFilters.watermark_code" placeholder="搜索水印码" clearable style="width: 200px" />
            <el-select v-model="logFilters.success" placeholder="验证结果" clearable style="width: 120px">
              <el-option label="成功" :value="true" />
              <el-option label="失败" :value="false" />
            </el-select>
            <el-button type="primary" @click="fetchVerificationLogs">
              <el-icon>
                <Search />
              </el-icon>
              搜索
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="verificationLogs" v-loading="logsLoading">
        <el-table-column prop="watermark_code" label="水印码" width="200" />

        <el-table-column label="验证结果" width="100">
          <template #default="{ row }">
            <el-tag :type="row.success ? 'success' : 'danger'">
              {{ row.success ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="ip_address" label="IP地址" width="150" />

        <el-table-column prop="user_agent" label="用户代理" min-width="200" show-overflow-tooltip />

        <el-table-column prop="created_at" label="验证时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="text" size="small" @click="viewLogDetail(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination v-model:current-page="logPagination.page" v-model:page-size="logPagination.per_page"
          :page-sizes="[10, 20, 50]" :total="logPagination.total" layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleLogSizeChange" @current-change="handleLogCurrentChange" />
      </div>
    </el-card>

    <!-- 水印详情弹窗 -->
    <el-dialog v-model="detailDialogVisible" title="水印详情" width="700px">
      <div v-if="currentWatermark">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="水印码">
            <el-tag type="info">{{ currentWatermark.watermark_code }}</el-tag>
            <el-button type="text" size="small" @click="copyWatermarkCode(currentWatermark)">
              复制
            </el-button>
          </el-descriptions-item>
          <el-descriptions-item label="用户">
            {{ currentWatermark.username }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentWatermark.is_active ? 'success' : 'danger'">
              {{ currentWatermark.is_active ? '活跃' : '已停用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="关联模型">
            {{ currentWatermark.model_name }}
          </el-descriptions-item>
          <el-descriptions-item label="码长度">
            {{ currentWatermark.code_length }} bits
          </el-descriptions-item>
          <el-descriptions-item label="验证次数">
            {{ currentWatermark.verification_count }}
          </el-descriptions-item>
          <el-descriptions-item label="最后验证">
            {{ formatTime(currentWatermark.last_verified_at) || '暂无' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatTime(currentWatermark.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ currentWatermark.description || '暂无描述' }}
          </el-descriptions-item>
        </el-descriptions>

        <div class="watermark-actions" style="margin-top: 20px; text-align: right;">
          <el-button :type="currentWatermark.is_active ? 'danger' : 'success'"
            @click="toggleWatermarkStatus(currentWatermark)">
            {{ currentWatermark.is_active ? '停用' : '启用' }}
          </el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 验证日志详情弹窗 -->
    <el-dialog v-model="logDetailDialogVisible" title="验证日志详情" width="600px">
      <div v-if="currentLog">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="水印码">
            {{ currentLog.watermark_code }}
          </el-descriptions-item>
          <el-descriptions-item label="验证结果">
            <el-tag :type="currentLog.success ? 'success' : 'danger'">
              {{ currentLog.success ? '成功' : '失败' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="IP地址">
            {{ currentLog.ip_address }}
          </el-descriptions-item>
          <el-descriptions-item label="验证时间">
            {{ formatTime(currentLog.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="用户代理" :span="2">
            {{ currentLog.user_agent }}
          </el-descriptions-item>
          <el-descriptions-item label="错误信息" :span="2" v-if="!currentLog.success && currentLog.error_message">
            <el-text type="danger">{{ currentLog.error_message }}</el-text>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Document,
  Check,
  Lock,
  User,
  Search,
  Refresh
} from '@element-plus/icons-vue'
import { adminAPI } from '@/api'

// 响应式数据
const watermarksLoading = ref(false)
const logsLoading = ref(false)
const detailDialogVisible = ref(false)
const logDetailDialogVisible = ref(false)

const stats = ref({
  total_watermarks: 0,
  active_watermarks: 0,
  total_verifications: 0,
  unique_users: 0
})

const watermarks = ref([])
const verificationLogs = ref([])
const currentWatermark = ref(null)
const currentLog = ref(null)

// 筛选和分页
const filters = reactive({
  username: '',
  is_active: null
})

const logFilters = reactive({
  watermark_code: '',
  success: null
})

const pagination = reactive({
  page: 1,
  per_page: 20,
  total: 0
})

const logPagination = reactive({
  page: 1,
  per_page: 20,
  total: 0
})

// 方法
async function fetchStats() {
  try {
    const res = await adminAPI.getWatermarkStatistics()
    stats.value = res.data || stats.value
  } catch (error) {
    console.error('获取统计信息失败:', error)
  }
}

async function fetchWatermarks() {
  watermarksLoading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page,
      username: filters.username || undefined,
      is_active: filters.is_active
    }

    const res = await adminAPI.getAllWatermarks(params)
    watermarks.value = res.data?.watermarks || []
    pagination.total = res.data?.total || 0
  } catch (error) {
    ElMessage.error('获取水印列表失败')
  } finally {
    watermarksLoading.value = false
  }
}

async function fetchVerificationLogs() {
  logsLoading.value = true
  try {
    const params = {
      page: logPagination.page,
      per_page: logPagination.per_page,
      watermark_code: logFilters.watermark_code || undefined,
      success: logFilters.success
    }

    const res = await adminAPI.getAllVerificationLogs(params)
    verificationLogs.value = res.data?.logs || []
    logPagination.total = res.data?.total || 0
  } catch (error) {
    ElMessage.error('获取验证日志失败')
  } finally {
    logsLoading.value = false
  }
}

function resetFilters() {
  filters.username = ''
  filters.is_active = null
  pagination.page = 1
  fetchWatermarks()
}

function handleSizeChange(size) {
  pagination.per_page = size
  pagination.page = 1
  fetchWatermarks()
}

function handleCurrentChange(page) {
  pagination.page = page
  fetchWatermarks()
}

function handleLogSizeChange(size) {
  logPagination.per_page = size
  logPagination.page = 1
  fetchVerificationLogs()
}

function handleLogCurrentChange(page) {
  logPagination.page = page
  fetchVerificationLogs()
}

function viewWatermarkDetail(watermark) {
  currentWatermark.value = watermark
  detailDialogVisible.value = true
}

function viewLogDetail(log) {
  currentLog.value = log
  logDetailDialogVisible.value = true
}

async function toggleWatermarkStatus(watermark) {
  try {
    const action = watermark.is_active ? '停用' : '启用'
    await ElMessageBox.confirm(`确定要${action}此水印吗？`, '确认操作', {
      type: 'warning'
    })

    // 这里需要后端提供管理员操作水印状态的接口
    // 暂时模拟操作
    watermark.is_active = !watermark.is_active
    ElMessage.success(`水印已${action}`)

    fetchStats()

  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

function copyWatermarkCode(watermark) {
  navigator.clipboard.writeText(watermark.watermark_code).then(() => {
    ElMessage.success('水印码已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

function formatTime(timeStr) {
  if (!timeStr) return ''
  return new Date(timeStr).toLocaleString()
}

onMounted(() => {
  fetchStats()
  fetchWatermarks()
  fetchVerificationLogs()
})
</script>

<style scoped>
.watermark-admin {
  padding: 24px;
  background: #f8f9fb;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
  text-align: center;
}

.page-header h2 {
  margin: 0 0 8px 0;
  font-size: 28px;
  color: #333;
}

.page-header p {
  margin: 0;
  color: #666;
  font-size: 16px;
}

.stats-row {
  margin-bottom: 24px;
}

.stats-card {
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  border-radius: 12px;
}

.stats-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stats-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stats-icon.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stats-icon.active {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
}

.stats-icon.verified {
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
}

.stats-icon.users {
  background: linear-gradient(135deg, #e6a23c 0%, #f0c674 100%);
}

.stats-info {
  flex: 1;
}

.stats-number {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
  line-height: 1;
}

.stats-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.watermark-list-card,
.verification-logs-card {
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.header-filters {
  display: flex;
  gap: 12px;
  align-items: center;
}

.pagination-wrapper {
  margin-top: 20px;
  text-align: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .watermark-admin {
    padding: 16px;
  }

  .stats-row .el-col {
    margin-bottom: 12px;
  }

  .card-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .header-filters {
    flex-direction: column;
    gap: 8px;
  }
}

/* Element Plus 样式覆盖 */
:deep(.el-table) {
  border-radius: 8px;
  overflow: hidden;
}

:deep(.el-card__header) {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}

:deep(.el-card__body) {
  padding: 20px;
}
</style>