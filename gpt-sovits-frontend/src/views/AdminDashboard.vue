<!-- ./gpt-sovits-frontend/src/views/AdminDashboard.vue -->
<template>
  <div class="admin-dashboard">
    <div class="page-header">
      <h1>管理员后台</h1>
      <p>系统管理与数据统计概览</p>
    </div>

    <!-- 系统统计卡片 -->
    <el-row :gutter="20" class="stats-overview">
      <el-col :span="6">
        <el-card class="stats-card user-stats">
          <div class="stats-content">
            <div class="stats-icon">
              <el-icon>
                <User />
              </el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ statistics.users?.total || 0 }}</div>
              <div class="stats-label">总用户数</div>
              <div class="stats-subtitle">今日新增: {{ statistics.users?.new_today || 0 }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stats-card model-stats">
          <div class="stats-content">
            <div class="stats-icon">
              <el-icon>
                <Microphone />
              </el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ statistics.models?.total || 0 }}</div>
              <div class="stats-label">音色模型</div>
              <div class="stats-subtitle">待审核: {{ statistics.models?.pending_review || 0 }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stats-card task-stats">
          <div class="stats-content">
            <div class="stats-icon">
              <el-icon>
                <DataLine />
              </el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ (statistics.tasks?.tts_total || 0) + (statistics.tasks?.voice_clone_total ||
                0) }}</div>
              <div class="stats-label">总任务数</div>
              <div class="stats-subtitle">今日: {{ (statistics.tasks?.tts_today || 0) +
                (statistics.tasks?.voice_clone_today || 0) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stats-card storage-stats">
          <div class="stats-content">
            <div class="stats-icon">
              <el-icon>
                <FolderOpened />
              </el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ statistics.storage?.total_size_mb || '0MB' }}</div>
              <div class="stats-label">存储使用</div>
              <div class="stats-subtitle">文件: {{ statistics.storage?.total_uploads || 0 }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快速操作卡片 -->
    <el-row :gutter="20" class="quick-actions">
      <el-col :span="6">
        <el-card class="action-card" @click="goUserManage">
          <div class="action-content">
            <div class="action-icon user-action">
              <el-icon>
                <UserFilled />
              </el-icon>
            </div>
            <div class="action-info">
              <h3>用户管理</h3>
              <p>查看、搜索和管理用户账户</p>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="action-card" @click="goModelAudit">
          <div class="action-content">
            <div class="action-icon model-action">
              <el-icon>
                <Microphone />
              </el-icon>
            </div>
            <div class="action-info">
              <h3>模型审核</h3>
              <p>审核用户上传的音色模型</p>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="action-card" @click="goWatermarkAdmin">
          <div class="action-content">
            <div class="action-icon watermark-action">
              <el-icon>
                <Lock />
              </el-icon>
            </div>
            <div class="action-info">
              <h3>水印管理</h3>
              <p>管理音频水印和验证记录</p>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="action-card" @click="goSystemLog">
          <div class="action-content">
            <div class="action-icon log-action">
              <el-icon>
                <Document />
              </el-icon>
            </div>
            <div class="action-info">
              <h3>系统日志</h3>
              <p>查看系统操作和错误日志</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表和详细数据 -->
    <el-row :gutter="20" class="charts-section">
      <!-- 用户活跃度图表 -->
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <h3>用户活跃度趋势</h3>
              <el-date-picker v-model="activityDateRange" type="daterange" range-separator="至" start-placeholder="开始日期"
                end-placeholder="结束日期" size="small" @change="fetchUserActivity" />
            </div>
          </template>

          <div class="chart-container" v-loading="activityLoading">
            <div v-if="!activityLoading && userActivityData.length > 0" id="user-activity-chart"
              style="width: 100%; height: 300px;"></div>
            <el-empty v-else-if="!activityLoading" description="暂无数据" />
          </div>
        </el-card>
      </el-col>

      <!-- 任务流量图表 -->
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <h3>任务流量统计</h3>
              <el-select v-model="taskPeriod" size="small" @change="fetchTaskFlow">
                <el-option label="最近7天" value="7d" />
                <el-option label="最近30天" value="30d" />
                <el-option label="最近90天" value="90d" />
              </el-select>
            </div>
          </template>

          <div class="chart-container" v-loading="taskLoading">
            <div v-if="!taskLoading && taskFlowData.length > 0" id="task-flow-chart"
              style="width: 100%; height: 300px;">
            </div>
            <el-empty v-else-if="!taskLoading" description="暂无数据" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 水印统计 -->
    <el-row :gutter="20" class="watermark-section">
      <el-col :span="12">
        <el-card class="info-card">
          <template #header>
            <h3>水印系统统计</h3>
          </template>

          <el-row :gutter="16" v-loading="watermarkStatsLoading">
            <el-col :span="8">
              <div class="metric-item">
                <div class="metric-number">{{ watermarkStats.total_watermarks || 0 }}</div>
                <div class="metric-label">总水印数</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="metric-item">
                <div class="metric-number">{{ watermarkStats.active_watermarks || 0 }}</div>
                <div class="metric-label">活跃水印</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="metric-item">
                <div class="metric-number">{{ watermarkStats.total_verifications || 0 }}</div>
                <div class="metric-label">验证总数</div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="info-card">
          <template #header>
            <h3>最近活动</h3>
          </template>

          <div class="activity-list" v-loading="recentActivityLoading">
            <div v-for="activity in recentActivities" :key="activity.id" class="activity-item">
              <div class="activity-icon" :class="`activity-${activity.type}`">
                <el-icon>
                  <component :is="getActivityIcon(activity.type)" />
                </el-icon>
              </div>
              <div class="activity-content">
                <div class="activity-text">{{ activity.description }}</div>
                <div class="activity-time">{{ formatTime(activity.created_at) }}</div>
              </div>
            </div>

            <el-empty v-if="!recentActivityLoading && recentActivities.length === 0" description="暂无活动记录" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 系统操作 -->
    <el-row :gutter="20" class="system-operations">
      <el-col :span="24">
        <el-card class="operation-card">
          <template #header>
            <h3>系统操作</h3>
          </template>

          <div class="operation-buttons">
            <el-button type="primary" @click="refreshAllData" :loading="refreshing">
              <el-icon>
                <Refresh />
              </el-icon>
              刷新数据
            </el-button>

            <el-button type="warning" @click="showCleanupDialog">
              <el-icon>
                <Delete />
              </el-icon>
              系统清理
            </el-button>

            <el-button @click="exportSystemReport" :loading="exporting">
              <el-icon>
                <Download />
              </el-icon>
              导出报告
            </el-button>

            <el-button type="info" @click="showSystemInfo">
              <el-icon>
                <InfoFilled />
              </el-icon>
              系统信息
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 系统清理确认弹窗 -->
    <el-dialog v-model="cleanupDialogVisible" title="系统清理" width="500px">
      <div class="cleanup-content">
        <el-alert title="系统清理将执行以下操作：" type="warning" :closable="false" show-icon />

        <ul class="cleanup-list">
          <li>清理临时文件和缓存</li>
          <li>删除过期的任务记录</li>
          <li>优化数据库性能</li>
          <li>清理无效的上传文件</li>
        </ul>

        <el-alert title="此操作不可撤销，请谨慎操作！" type="error" :closable="false" show-icon />
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="cleanupDialogVisible = false">取消</el-button>
          <el-button type="danger" @click="executeCleanup" :loading="cleanupLoading">
            确认清理
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 系统信息弹窗 -->
    <el-dialog v-model="systemInfoVisible" title="系统信息" width="600px">
      <el-descriptions :column="2" border v-loading="systemInfoLoading">
        <el-descriptions-item label="系统版本">{{ systemInfo.version || '-' }}</el-descriptions-item>
        <el-descriptions-item label="运行环境">{{ systemInfo.environment || '-' }}</el-descriptions-item>
        <el-descriptions-item label="数据库状态">
          <el-tag :type="systemInfo.database_status === 'healthy' ? 'success' : 'danger'">
            {{ systemInfo.database_status || '未知' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Redis状态">
          <el-tag :type="systemInfo.redis_status === 'healthy' ? 'success' : 'danger'">
            {{ systemInfo.redis_status || '未知' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="启动时间">{{ formatTime(systemInfo.start_time) }}</el-descriptions-item>
        <el-descriptions-item label="运行时长">{{ systemInfo.uptime || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User,
  UserFilled,
  Microphone,
  DataLine,
  FolderOpened,
  Lock,
  Document,
  Refresh,
  Delete,
  Download,
  InfoFilled,
  Plus,
  Setting,
  Clock
} from '@element-plus/icons-vue'
import { adminAPI } from '@/api'
import * as echarts from 'echarts'

const router = useRouter()

// 响应式数据
const statistics = ref({})
const watermarkStats = ref({})
const recentActivities = ref([])
const userActivityData = ref([])
const taskFlowData = ref([])
const systemInfo = ref({})

const activityDateRange = ref([])
const taskPeriod = ref('7d')

const activityLoading = ref(false)
const taskLoading = ref(false)
const watermarkStatsLoading = ref(false)
const recentActivityLoading = ref(false)
const systemInfoLoading = ref(false)
const refreshing = ref(false)
const exporting = ref(false)
const cleanupLoading = ref(false)

const cleanupDialogVisible = ref(false)
const systemInfoVisible = ref(false)

let userActivityChart = null
let taskFlowChart = null

// 方法
async function fetchStatistics() {
  try {
    const res = await adminAPI.getSystemStatistics()
    statistics.value = res.data || {}
  } catch (error) {
    console.error('获取统计信息失败:', error)
  }
}

async function fetchWatermarkStats() {
  watermarkStatsLoading.value = true
  try {
    const res = await adminAPI.getWatermarkStatistics()
    watermarkStats.value = res.data || {}
  } catch (error) {
    console.error('获取水印统计失败:', error)
  } finally {
    watermarkStatsLoading.value = false
  }
}

async function fetchUserActivity() {
  activityLoading.value = true
  try {
    // 模拟用户活跃度数据
    const mockData = [
      { date: '2025-06-20', new_users: 12, active_users: 45 },
      { date: '2025-06-21', new_users: 15, active_users: 52 },
      { date: '2025-06-22', new_users: 8, active_users: 38 },
      { date: '2025-06-23', new_users: 20, active_users: 67 },
      { date: '2025-06-24', new_users: 18, active_users: 58 },
      { date: '2025-06-25', new_users: 25, active_users: 73 },
      { date: '2025-06-26', new_users: 22, active_users: 69 }
    ]

    userActivityData.value = mockData
    await nextTick()
    renderUserActivityChart()
  } catch (error) {
    console.error('获取用户活动数据失败:', error)
  } finally {
    activityLoading.value = false
  }
}

async function fetchTaskFlow() {
  taskLoading.value = true
  try {
    // 模拟任务流量数据
    const mockData = [
      { date: '2025-06-20', tts_tasks: 28, voice_clone_tasks: 12 },
      { date: '2025-06-21', tts_tasks: 35, voice_clone_tasks: 15 },
      { date: '2025-06-22', tts_tasks: 42, voice_clone_tasks: 18 },
      { date: '2025-06-23', tts_tasks: 38, voice_clone_tasks: 22 },
      { date: '2025-06-24', tts_tasks: 45, voice_clone_tasks: 25 },
      { date: '2025-06-25', tts_tasks: 52, voice_clone_tasks: 28 },
      { date: '2025-06-26', tts_tasks: 48, voice_clone_tasks: 30 }
    ]

    taskFlowData.value = mockData
    await nextTick()
    renderTaskFlowChart()
  } catch (error) {
    console.error('获取任务流量数据失败:', error)
  } finally {
    taskLoading.value = false
  }
}

async function fetchRecentActivities() {
  recentActivityLoading.value = true
  try {
    const res = await adminAPI.getAuditLogs({ per_page: 10 })
    recentActivities.value = (res.data?.logs || []).map(log => ({
      id: log.id,
      type: log.action,
      description: `${log.user_name || '系统'} ${log.action} ${log.resource_type}`,
      created_at: log.created_at
    }))
  } catch (error) {
    // 使用模拟数据
    recentActivities.value = [
      { id: 1, type: 'login', description: '用户 admin 登录系统', created_at: new Date().toISOString() },
      { id: 2, type: 'upload', description: '用户 user1 上传音频样本', created_at: new Date(Date.now() - 300000).toISOString() },
      { id: 3, type: 'audit', description: '管理员审核通过模型 #102', created_at: new Date(Date.now() - 600000).toISOString() }
    ]
  } finally {
    recentActivityLoading.value = false
  }
}

function renderUserActivityChart() {
  const chartDom = document.getElementById('user-activity-chart')
  if (!chartDom || userActivityData.value.length === 0) return

  if (userActivityChart) {
    userActivityChart.dispose()
  }

  userActivityChart = echarts.init(chartDom)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['新增用户', '活跃用户']
    },
    xAxis: {
      type: 'category',
      data: userActivityData.value.map(item => item.date)
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '新增用户',
        type: 'line',
        data: userActivityData.value.map(item => item.new_users),
        itemStyle: { color: '#409EFF' }
      },
      {
        name: '活跃用户',
        type: 'line',
        data: userActivityData.value.map(item => item.active_users),
        itemStyle: { color: '#67C23A' }
      }
    ]
  }

  userActivityChart.setOption(option)
}

function renderTaskFlowChart() {
  const chartDom = document.getElementById('task-flow-chart')
  if (!chartDom || taskFlowData.value.length === 0) return

  if (taskFlowChart) {
    taskFlowChart.dispose()
  }

  taskFlowChart = echarts.init(chartDom)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['TTS任务', '音色克隆任务']
    },
    xAxis: {
      type: 'category',
      data: taskFlowData.value.map(item => item.date)
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: 'TTS任务',
        type: 'bar',
        data: taskFlowData.value.map(item => item.tts_tasks),
        itemStyle: { color: '#E6A23C' }
      },
      {
        name: '音色克隆任务',
        type: 'bar',
        data: taskFlowData.value.map(item => item.voice_clone_tasks),
        itemStyle: { color: '#F56C6C' }
      }
    ]
  }

  taskFlowChart.setOption(option)
}

function getActivityIcon(type) {
  const iconMap = {
    login: User,
    upload: Plus,
    audit: Setting,
    default: Clock
  }
  return iconMap[type] || iconMap.default
}

function formatTime(timeStr) {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString()
}

async function refreshAllData() {
  refreshing.value = true
  try {
    await Promise.all([
      fetchStatistics(),
      fetchWatermarkStats(),
      fetchUserActivity(),
      fetchTaskFlow(),
      fetchRecentActivities()
    ])
    ElMessage.success('数据刷新成功')
  } catch (error) {
    ElMessage.error('数据刷新失败')
  } finally {
    refreshing.value = false
  }
}

function showCleanupDialog() {
  cleanupDialogVisible.value = true
}

async function executeCleanup() {
  try {
    await ElMessageBox.confirm('确定要执行系统清理吗？此操作不可撤销！', '确认清理', {
      type: 'warning'
    })

    cleanupLoading.value = true
    await adminAPI.systemCleanup()
    ElMessage.success('系统清理完成')
    cleanupDialogVisible.value = false
    refreshAllData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('系统清理失败')
    }
  } finally {
    cleanupLoading.value = false
  }
}

async function exportSystemReport() {
  exporting.value = true
  try {
    // 模拟导出功能
    ElMessage.success('报告导出功能开发中')
  } catch (error) {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

async function showSystemInfo() {
  systemInfoVisible.value = true
  systemInfoLoading.value = true

  try {
    // 模拟系统信息
    systemInfo.value = {
      version: 'v1.0.0',
      environment: 'production',
      database_status: 'healthy',
      redis_status: 'healthy',
      start_time: new Date(Date.now() - 86400000).toISOString(),
      uptime: '1天2小时30分钟'
    }
  } catch (error) {
    console.error('获取系统信息失败:', error)
  } finally {
    systemInfoLoading.value = false
  }
}

// 导航方法
function goUserManage() {
  router.push({ name: 'UserManage' })
}

function goModelAudit() {
  router.push({ name: 'ModelAudit' })
}

function goWatermarkAdmin() {
  router.push({ name: 'WatermarkAdmin' })
}

function goSystemLog() {
  router.push({ name: 'SystemLog' })
}

onMounted(() => {
  fetchStatistics()
  fetchWatermarkStats()
  fetchUserActivity()
  fetchTaskFlow()
  fetchRecentActivities()
})
</script>

<style scoped>
.admin-dashboard {
  padding: 24px;
  background: #f8f9fb;
  min-height: 100vh;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 32px;
  color: #303133;
  font-weight: 700;
}

.page-header p {
  margin: 0;
  font-size: 16px;
  color: #606266;
}

.stats-overview {
  margin-bottom: 24px;
}

.stats-card {
  border: none;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.stats-content {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
}

.stats-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: white;
}

.user-stats .stats-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.model-stats .stats-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.task-stats .stats-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.storage-stats .stats-icon {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stats-info {
  flex: 1;
}

.stats-number {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1;
  margin-bottom: 4px;
}

.stats-label {
  font-size: 16px;
  color: #606266;
  font-weight: 500;
  margin-bottom: 2px;
}

.stats-subtitle {
  font-size: 12px;
  color: #909399;
}

.quick-actions {
  margin-bottom: 24px;
}

.action-card {
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.action-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.action-content {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
}

.action-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.user-action {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.model-action {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.watermark-action {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.log-action {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.action-info h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
  color: #303133;
  font-weight: 600;
}

.action-info p {
  margin: 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.4;
}

.charts-section {
  margin-bottom: 24px;
}

.chart-card {
  border: none;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
  font-weight: 600;
}

.chart-container {
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.watermark-section {
  margin-bottom: 24px;
}

.info-card {
  border: none;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.metric-item {
  text-align: center;
  padding: 16px;
}

.metric-number {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 4px;
}

.metric-label {
  font-size: 14px;
  color: #606266;
}

.activity-list {
  max-height: 300px;
  overflow-y: auto;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: white;
}

.activity-login {
  background: #67c23a;
}

.activity-upload {
  background: #409eff;
}

.activity-audit {
  background: #e6a23c;
}

.activity-default {
  background: #909399;
}

.activity-content {
  flex: 1;
}

.activity-text {
  font-size: 14px;
  color: #303133;
  margin-bottom: 2px;
}

.activity-time {
  font-size: 12px;
  color: #909399;
}

.system-operations {
  margin-bottom: 24px;
}

.operation-card {
  border: none;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.operation-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.cleanup-content {
  padding: 16px 0;
}

.cleanup-list {
  margin: 16px 0;
  padding-left: 20px;
}

.cleanup-list li {
  margin-bottom: 8px;
  color: #606266;
}

/* 响应式设计 */
@media (max-width: 1200px) {

  .stats-overview .el-col,
  .quick-actions .el-col {
    margin-bottom: 16px;
  }
}

@media (max-width: 768px) {
  .admin-dashboard {
    padding: 16px;
  }

  .stats-content,
  .action-content {
    flex-direction: column;
    text-align: center;
    gap: 12px;
  }

  .charts-section .el-col,
  .watermark-section .el-col {
    margin-bottom: 16px;
  }

  .operation-buttons {
    flex-direction: column;
  }

  .card-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
}
</style>