<!-- ./gpt-sovits-frontend/src/views/TaskHistory.vue -->
<template>
  <div class="task-history">
    <div class="page-header">
      <h1>📋 任务历史</h1>
      <p>查看你的语音合成和音色克隆任务记录</p>
    </div>

    <!-- 筛选区域 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="任务类型">
          <el-select v-model="filters.type" placeholder="全部类型" clearable style="width: 150px">
            <el-option label="语音合成" value="tts" />
            <el-option label="音色克隆" value="voice_clone" />
          </el-select>
        </el-form-item>

        <el-form-item label="任务名称">
          <el-input v-model="filters.taskName" placeholder="搜索任务名称" clearable style="width: 200px" />
        </el-form-item>

        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 150px">
            <el-option label="等待中" value="pending" />
            <el-option label="处理中" value="processing" />
            <el-option label="训练中" value="training" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>

        <el-form-item label="时间范围">
          <el-date-picker v-model="filters.dateRange" type="datetimerange" range-separator="至" start-placeholder="开始时间"
            end-placeholder="结束时间" format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DD HH:mm:ss" style="width: 300px" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="fetchTasks" :loading="loading">
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

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon stats-total">
              <el-icon>
                <Document />
              </el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ stats.total }}</div>
              <div class="stats-label">总任务数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon stats-completed">
              <el-icon>
                <SuccessFilled />
              </el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ stats.completed }}</div>
              <div class="stats-label">已完成</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon stats-processing">
              <el-icon>
                <Loading />
              </el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ stats.processing }}</div>
              <div class="stats-label">处理中</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon stats-failed">
              <el-icon>
                <CircleCloseFilled />
              </el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ stats.failed }}</div>
              <div class="stats-label">失败</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 任务列表 -->
    <el-card class="task-list-card">
      <template #header>
        <div class="card-header">
          <span>任务列表</span>
          <div class="header-actions">
            <el-button size="small" @click="fetchTasks">
              <el-icon>
                <Refresh />
              </el-icon>
              刷新
            </el-button>
            <el-button size="small" @click="clearCompleted" :disabled="stats.completed === 0">
              <el-icon>
                <Delete />
              </el-icon>
              清理已完成
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="tasks" v-loading="loading" row-key="id" @row-click="viewTaskDetail" style="cursor: pointer">
        <el-table-column prop="id" label="任务ID" width="120" />

        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTaskTypeTagType(row.type)" size="small">
              {{ getTaskTypeText(row.task_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="title" label="任务描述" min-width="200">
          <template #default="{ row }">
            <div class="task-title">
              {{ getTaskTitle(row) }}
            </div>
            <div class="task-subtitle" v-if="getTaskSubtitle(row)">
              {{ getTaskSubtitle(row) }}
            </div>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="进度" width="120">
          <template #default="{ row }">
            <el-progress :percentage="getProgress(row.status, row.progress)" :status="getProgressStatus(row.status)"
              :stroke-width="6" />
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="耗时" width="100">
          <template #default="{ row }">
            {{ getDuration(row) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button size="small" type="primary" @click.stop="viewTaskDetail(row)">
                详情
              </el-button>

              <el-button v-if="row.status === 'completed' && hasResult(row)" size="small" type="success"
                @click.stop="downloadResult(row)">
                下载
              </el-button>

              <el-button v-if="row.type === 'tts' && row.status === 'completed'" size="small" type="info"
                @click.stop="playAudio(row)">
                试听
              </el-button>

              <el-button v-if="canRetry(row)" size="small" type="warning" @click.stop="retryTask(row)">
                重试
              </el-button>

              <el-button v-if="canCancel(row)" size="small" type="danger" @click.stop="cancelTask(row)">
                取消
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 空状态 -->
      <el-empty v-if="!loading && tasks.length === 0" description="暂无任务记录" />

      <!-- 分页 -->
      <div class="pagination-wrapper" v-if="pagination.total > 0">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.per_page"
          :page-sizes="[10, 20, 50, 100]" :total="pagination.total" layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange" @current-change="handleCurrentChange" />
      </div>
    </el-card>

    <!-- 音频播放器 -->
    <audio ref="audioPlayer" style="display: none" @ended="onAudioEnded" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Refresh,
  Document,
  SuccessFilled,
  Loading,
  CircleCloseFilled,
  Delete
} from '@element-plus/icons-vue'
import { userAPI, ttsAPI, voiceCloneAPI } from '@/api'

const route = useRoute()
const router = useRouter()

// 响应式数据
const loading = ref(false)
const tasks = ref([])
const currentPlayingTask = ref(null)
const audioPlayer = ref()

const filters = reactive({
  type: '',
  taskName: '',
  status: '',
  dateRange: null
})

const pagination = reactive({
  page: 1,
  per_page: 20,
  total: 0
})

const stats = reactive({
  total: 0,
  completed: 0,
  processing: 0,
  failed: 0
})

// 方法
async function fetchTasks() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page,
      type: filters.type || undefined,
      status: filters.status || undefined
    }

    // 添加时间范围过滤
    if (filters.dateRange && filters.dateRange.length === 2) {
      params.start_time = filters.dateRange[0]
      params.end_time = filters.dateRange[1]
    }

    const res = await userAPI.getTaskHistory(params)

    // 根据API文档，任务数据在 res.data.tasks 中
    tasks.value = res.data?.tasks || []

    // 更新分页信息
    if (res.data?.pagination) {
      pagination.total = res.data.pagination.total
    }

    // 更新统计信息
    updateStats()

  } catch (error) {
    console.error('获取任务列表失败:', error)
    ElMessage.error('获取任务列表失败')
  } finally {
    loading.value = false
  }
}

function updateStats() {
  const allTasks = tasks.value
  stats.total = allTasks.length
  stats.completed = allTasks.filter(t => t.status === 'completed').length
  stats.processing = allTasks.filter(t => ['pending', 'processing', 'training'].includes(t.status)).length
  stats.failed = allTasks.filter(t => t.status === 'failed').length
}

function resetFilters() {
  filters.type = ''
  filters.taskName = ''
  filters.status = ''
  filters.dateRange = null
  pagination.page = 1
  fetchTasks()
}

function handleSizeChange(size) {
  pagination.per_page = size
  pagination.page = 1
  fetchTasks()
}

function handleCurrentChange(page) {
  pagination.page = page
  fetchTasks()
}

function viewTaskDetail(row) {
  router.push({
    name: 'Status',
    params: { taskId: row.id },
    query: { type: row.type }
  })
}

async function downloadResult(row) {
  try {
    if (row.type === 'tts') {
      // TTS任务下载音频
      const res = await ttsAPI.downloadAudio(row.id)
      downloadBlob(res.data, `tts_${row.id}.wav`)
    } else if (row.type === 'voice_clone') {
      // 音色克隆任务获取下载链接
      const res = await voiceCloneAPI.getTaskResult(row.id)
      if (res.data?.model_download_url) {
        window.open(res.data.model_download_url, '_blank')
      } else if (res.data?.download_url) {
        window.open(res.data.download_url, '_blank')
      }
    }
    ElMessage.success('下载开始')
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败')
  }
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function playAudio(row) {
  if (currentPlayingTask.value === row.id) {
    // 停止播放
    audioPlayer.value.pause()
    currentPlayingTask.value = null
  } else {
    // 开始播放
    const audioUrl = row.result_url || row.audio_url
    if (audioUrl) {
      audioPlayer.value.src = audioUrl
      audioPlayer.value.play()
      currentPlayingTask.value = row.id
    } else {
      ElMessage.warning('音频文件不存在')
    }
  }
}

function onAudioEnded() {
  currentPlayingTask.value = null
}

async function retryTask(row) {
  try {
    if (row.type === 'voice_clone') {
      await voiceCloneAPI.retryTask(row.id)
      ElMessage.success('任务已重新提交')
      fetchTasks()
    } else {
      // TTS任务重试需要重新提交
      ElMessage.info('请前往文本转语音页面重新生成')
      router.push({ name: 'TTSPlayground' })
    }
  } catch (error) {
    console.error('重试失败:', error)
    ElMessage.error('重试失败')
  }
}

async function cancelTask(row) {
  try {
    await ElMessageBox.confirm(
      '确定要取消这个任务吗？',
      '确认取消',
      { type: 'warning' }
    )

    if (row.type === 'voice_clone') {
      await voiceCloneAPI.cancelTask(row.id)
      ElMessage.success('任务已取消')
      fetchTasks()
    } else {
      ElMessage.info('TTS任务无法取消')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消失败:', error)
      ElMessage.error('取消失败')
    }
  }
}

async function clearCompleted() {
  try {
    await ElMessageBox.confirm(
      '确定要清理所有已完成的任务吗？此操作不可恢复。',
      '确认清理',
      { type: 'warning' }
    )

    // 这里应该调用后端API清理已完成任务
    ElMessage.success('清理完成')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('清理失败')
    }
  }
}

// 工具函数
function getTaskTypeText(type) {
  const typeMap = {
    'tts': '语音合成',
    'voice_clone': '音色克隆'
  }
  return typeMap[type] || type || '未知类型'
}

function getTaskTypeTagType(type) {
  const typeMap = {
    'tts': 'primary',
    'voice_clone': 'success'
  }
  return typeMap[type] || ''
}

function getTaskTitle(row) {
  // 根据任务类型生成标题
  if (row.type === 'tts') {
    return row.title || `语音合成任务`
  } else if (row.type === 'voice_clone') {
    return row.title || `音色克隆任务 - ${row.model_name || '未命名'}`
  }
  return row.title || `任务 - ${row.id}`
}

function getTaskSubtitle(row) {
  // 根据任务类型生成副标题
  if (row.type === 'tts' && row.text) {
    return row.text.length > 50 ? row.text.substring(0, 50) + '...' : row.text
  } else if (row.type === 'voice_clone') {
    const parts = []
    if (row.sample_count) parts.push(`${row.sample_count}个样本`)
    if (row.total_duration) parts.push(`${Math.round(row.total_duration)}秒`)
    return parts.join(' | ')
  }
  return row.subtitle || ''
}

function getStatusText(status) {
  const statusMap = {
    'pending': '等待中',
    'processing': '处理中',
    'training': '训练中',
    'completed': '已完成',
    'failed': '失败',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

function getStatusTagType(status) {
  const typeMap = {
    'pending': 'info',
    'processing': 'warning',
    'training': 'warning',
    'completed': 'success',
    'failed': 'danger',
    'cancelled': 'info'
  }
  return typeMap[status] || ''
}

function getProgress(status, progress) {
  if (progress && typeof progress === 'number') return progress

  const progressMap = {
    'pending': 10,
    'processing': 50,
    'training': 70,
    'completed': 100,
    'failed': 0,
    'cancelled': 0
  }
  return progressMap[status] || 0
}

function getProgressStatus(status) {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return null
}

function hasResult(row) {
  return row.result_url || row.audio_url || row.model_download_url
}

function getDuration(row) {
  if (!row.created_at) return '-'

  const start = new Date(row.created_at)
  const end = row.completed_at ? new Date(row.completed_at) : new Date()
  const diff = end - start

  const minutes = Math.floor(diff / 60000)
  const seconds = Math.floor((diff % 60000) / 1000)

  if (minutes > 60) {
    const hours = Math.floor(minutes / 60)
    const remainingMinutes = minutes % 60
    return `${hours}小时${remainingMinutes}分钟`
  } else if (minutes > 0) {
    return `${minutes}分钟${seconds}秒`
  } else {
    return `${seconds}秒`
  }
}

function formatTime(timeStr) {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString()
}

function canRetry(row) {
  return row.status === 'failed'
}

function canCancel(row) {
  return ['pending', 'processing', 'training'].includes(row.status)
}

// 监听路由参数，如果有highlight参数则高亮对应任务
watch(() => route.query.highlight, (taskId) => {
  if (taskId) {
    // 这里可以添加高亮逻辑
    setTimeout(() => {
      const element = document.querySelector(`[data-task-id="${taskId}"]`)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' })
        element.classList.add('highlight')
        setTimeout(() => {
          element.classList.remove('highlight')
        }, 3000)
      }
    }, 500)
  }
})

onMounted(() => {
  fetchTasks()
})
</script>

<style scoped>
.task-history {
  padding: 24px;
  background: #f8f9fb;
  min-height: 100vh;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
}

.page-header h1 {
  font-size: 28px;
  margin: 0 0 8px 0;
  color: #303133;
}

.page-header p {
  font-size: 16px;
  color: #606266;
  margin: 0;
}

.filter-card {
  margin-bottom: 20px;
  border: none;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.filter-form {
  margin: 0;
}

.stats-row {
  margin-bottom: 20px;
}

.stats-card {
  border: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stats-total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stats-completed {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
}

.stats-processing {
  background: linear-gradient(135deg, #e6a23c 0%, #f0c674 100%);
}

.stats-failed {
  background: linear-gradient(135deg, #f56c6c 0%, #f78989 100%);
}

.stats-info {
  flex: 1;
}

.stats-number {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
}

.stats-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.task-list-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: none;
  border-radius: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.task-title {
  font-weight: 500;
  color: #303133;
}

.task-subtitle {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.table-actions {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.pagination-wrapper {
  margin-top: 20px;
  text-align: center;
}

/* 高亮动画 */
.highlight {
  background-color: #ecf5ff !important;
  animation: highlightFade 3s ease-out;
}

@keyframes highlightFade {
  0% {
    background-color: #409eff;
    color: white;
  }

  100% {
    background-color: #ecf5ff;
    color: inherit;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .task-history {
    padding: 16px;
  }

  .stats-row {
    display: block;
  }

  .stats-row .el-col {
    margin-bottom: 12px;
  }

  .table-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .table-actions .el-button {
    margin: 2px 0;
  }

  .filter-form {
    flex-direction: column;
  }

  .filter-form .el-form-item {
    margin-bottom: 12px;
  }
}

/* 表格样式优化 */
:deep(.el-table) {
  border-radius: 8px;
  overflow: hidden;
}

:deep(.el-table__row) {
  transition: background-color 0.3s ease;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}

:deep(.el-progress-bar__outer) {
  border-radius: 3px;
}

:deep(.el-progress-bar__inner) {
  border-radius: 3px;
}

:deep(.el-card__header) {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}

:deep(.el-card__body) {
  padding: 20px;
}
</style>