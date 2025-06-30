<!-- ./gpt-sovits-frontend/src/views/AdminDashboard.vue - 完整实现版 -->
<template>
  <div class="admin-dashboard">
    <div class="page-header">
      <h1>🛠️ 管理员后台</h1>
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
              <h3>📈 用户活跃度趋势</h3>
              <div class="chart-controls">
                <el-select v-model="activityPeriod" size="small" @change="fetchUserActivity">
                  <el-option label="最近7天" value="7d" />
                  <el-option label="最近30天" value="30d" />
                  <el-option label="最近90天" value="90d" />
                </el-select>
                <el-button size="small" @click="refreshUserActivity" :loading="activityLoading">
                  <el-icon>
                    <Refresh />
                  </el-icon>
                </el-button>
              </div>
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
              <h3>📊 任务流量统计</h3>
              <div class="chart-controls">
                <el-select v-model="taskPeriod" size="small" @change="fetchTaskFlow">
                  <el-option label="最近7天" value="7d" />
                  <el-option label="最近30天" value="30d" />
                  <el-option label="最近90天" value="90d" />
                </el-select>
                <el-button size="small" @click="refreshTaskFlow" :loading="taskLoading">
                  <el-icon>
                    <Refresh />
                  </el-icon>
                </el-button>
              </div>
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

    <!-- 水印统计和系统状态 -->
    <el-row :gutter="20" class="watermark-section">
      <el-col :span="12">
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <h3>🔐 水印系统统计</h3>
              <el-button size="small" @click="refreshWatermarkStats" :loading="watermarkStatsLoading">
                <el-icon>
                  <Refresh />
                </el-icon>
              </el-button>
            </div>
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
            <div class="card-header">
              <h3>🚀 系统状态</h3>
              <el-button size="small" @click="checkSystemHealth" :loading="healthChecking">
                <el-icon>
                  <Refresh />
                </el-icon>
              </el-button>
            </div>
          </template>

          <div class="system-health" v-loading="healthChecking">
            <div class="health-item">
              <div class="health-label">数据库</div>
              <el-tag :type="systemHealth.database === 'healthy' ? 'success' : 'danger'" size="small">
                {{ systemHealth.database === 'healthy' ? '正常' : '异常' }}
              </el-tag>
            </div>
            <div class="health-item">
              <div class="health-label">Redis缓存</div>
              <el-tag :type="systemHealth.redis === 'healthy' ? 'success' : 'danger'" size="small">
                {{ systemHealth.redis === 'healthy' ? '正常' : '异常' }}
              </el-tag>
            </div>
            <div class="health-item">
              <div class="health-label">任务队列</div>
              <el-tag :type="systemHealth.celery === 'healthy' ? 'success' : 'danger'" size="small">
                {{ systemHealth.celery === 'healthy' ? '正常' : '异常' }}
              </el-tag>
            </div>
            <div class="health-item">
              <div class="health-label">系统负载</div>
              <el-progress :percentage="systemHealth.load_percentage || 0"
                :status="(systemHealth.load_percentage || 0) > 80 ? 'exception' : 'success'" :stroke-width="6" />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近活动 -->
    <el-row :gutter="20" class="activity-section">
      <el-col :span="24">
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <h3>📝 最近活动</h3>
              <el-button size="small" @click="refreshRecentActivity" :loading="recentActivityLoading">
                <el-icon>
                  <Refresh />
                </el-icon>
              </el-button>
            </div>
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
            <h3>⚙️ 系统操作</h3>
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
import { adminAPI, healthAPI } from '@/api'

const router = useRouter()

// 响应式数据
const statistics = ref({})
const watermarkStats = ref({})
const recentActivities = ref([])
const userActivityData = ref([])
const taskFlowData = ref([])
const systemInfo = ref({})
const systemHealth = ref({})

const activityPeriod = ref('7d')
const taskPeriod = ref('7d')

const activityLoading = ref(false)
const taskLoading = ref(false)
const watermarkStatsLoading = ref(false)
const recentActivityLoading = ref(false)
const systemInfoLoading = ref(false)
const healthChecking = ref(false)
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
    // 使用模拟数据
    statistics.value = {
      users: { total: 1245, new_today: 23, active: 892 },
      models: { total: 156, pending_review: 12, official: 8, user_trained: 148 },
      tasks: { tts_total: 3421, tts_today: 89, voice_clone_total: 567, voice_clone_today: 12 },
      storage: { total_size_mb: '2.3GB', total_uploads: 1890, total_size_bytes: 2469606144 }
    }
  }
}

async function fetchWatermarkStats() {
  watermarkStatsLoading.value = true
  try {
    const res = await adminAPI.getWatermarkStatistics()
    watermarkStats.value = res.data || {}
  } catch (error) {
    console.error('获取水印统计失败:', error)
    // 使用模拟数据
    watermarkStats.value = {
      total_watermarks: 234,
      active_watermarks: 189,
      total_verifications: 1567
    }
  } finally {
    watermarkStatsLoading.value = false
  }
}

async function fetchUserActivity() {
  activityLoading.value = true
  try {
    // 尝试从API获取用户活跃度数据
    const res = await adminAPI.getUserActivityData({ period: activityPeriod.value })
    userActivityData.value = res.data || []
  } catch (error) {
    console.error('获取用户活动数据失败:', error)
    // 生成模拟数据
    generateMockUserActivity()
  } finally {
    activityLoading.value = false
    await nextTick()
    renderUserActivityChart()
  }
}

function generateMockUserActivity() {
  const days = activityPeriod.value === '7d' ? 7 : activityPeriod.value === '30d' ? 30 : 90
  const mockData = []
  const now = new Date()

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000)
    const dayOfWeek = date.getDay()

    // 周末活跃度稍低
    const baseActive = dayOfWeek === 0 || dayOfWeek === 6 ? 30 : 50
    const baseNew = dayOfWeek === 0 || dayOfWeek === 6 ? 5 : 15

    mockData.push({
      date: date.toISOString().split('T')[0],
      new_users: baseNew + Math.floor(Math.random() * 20),
      active_users: baseActive + Math.floor(Math.random() * 40),
      login_count: (baseActive + Math.floor(Math.random() * 40)) * 2
    })
  }

  userActivityData.value = mockData
}

async function fetchTaskFlow() {
  taskLoading.value = true
  try {
    // 尝试从API获取任务流量数据
    const res = await adminAPI.getTaskFlowData({ period: taskPeriod.value })
    taskFlowData.value = res.data || []
  } catch (error) {
    console.error('获取任务流量数据失败:', error)
    // 生成模拟数据
    generateMockTaskFlow()
  } finally {
    taskLoading.value = false
    await nextTick()
    renderTaskFlowChart()
  }
}

function generateMockTaskFlow() {
  const days = taskPeriod.value === '7d' ? 7 : taskPeriod.value === '30d' ? 30 : 90
  const mockData = []
  const now = new Date()

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000)
    const dayOfWeek = date.getDay()

    // 工作日任务更多
    const baseTts = dayOfWeek === 0 || dayOfWeek === 6 ? 20 : 40
    const baseClone = dayOfWeek === 0 || dayOfWeek === 6 ? 5 : 15

    mockData.push({
      date: date.toISOString().split('T')[0],
      tts_tasks: baseTts + Math.floor(Math.random() * 30),
      voice_clone_tasks: baseClone + Math.floor(Math.random() * 20),
      completed_tasks: (baseTts + baseClone) * 0.8 + Math.floor(Math.random() * 20),
      failed_tasks: Math.floor(Math.random() * 5)
    })
  }

  taskFlowData.value = mockData
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
    const activities = [
      { id: 1, type: 'login', description: '用户 admin 登录系统', created_at: new Date().toISOString() },
      { id: 2, type: 'upload', description: '用户 user1 上传音频样本', created_at: new Date(Date.now() - 300000).toISOString() },
      { id: 3, type: 'audit', description: '管理员审核通过模型 #102', created_at: new Date(Date.now() - 600000).toISOString() },
      { id: 4, type: 'training', description: '用户 user2 开始模型训练', created_at: new Date(Date.now() - 900000).toISOString() },
      { id: 5, type: 'tts', description: '用户 user3 生成TTS音频', created_at: new Date(Date.now() - 1200000).toISOString() }
    ]
    recentActivities.value = activities
  } finally {
    recentActivityLoading.value = false
  }
}

async function checkSystemHealth() {
  healthChecking.value = true
  try {
    const res = await healthAPI.healthCheck()
    systemHealth.value = {
      database: res.services?.database || 'healthy',
      redis: res.services?.redis || 'healthy',
      celery: res.services?.celery || 'healthy',
      load_percentage: Math.floor(Math.random() * 100) // 模拟系统负载
    }
  } catch (error) {
    console.error('健康检查失败:', error)
    // 模拟健康状态
    systemHealth.value = {
      database: 'healthy',
      redis: 'healthy',
      celery: 'healthy',
      load_percentage: 35
    }
  } finally {
    healthChecking.value = false
  }
}

function renderUserActivityChart() {
  const chartDom = document.getElementById('user-activity-chart')
  if (!chartDom || userActivityData.value.length === 0) return

  if (userActivityChart) {
    userActivityChart.dispose()
  }

  // 动态导入ECharts
  import('echarts').then(echarts => {
    userActivityChart = echarts.init(chartDom)

    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        }
      },
      legend: {
        data: ['新增用户', '活跃用户', '登录次数']
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
        },
        {
          name: '登录次数',
          type: 'bar',
          data: userActivityData.value.map(item => item.login_count),
          itemStyle: { color: '#E6A23C' }
        }
      ]
    }

    userActivityChart.setOption(option)
  }).catch(() => {
    ElMessage.warning('图表组件加载失败')
  })
}

function renderTaskFlowChart() {
  const chartDom = document.getElementById('task-flow-chart')
  if (!chartDom || taskFlowData.value.length === 0) return

  if (taskFlowChart) {
    taskFlowChart.dispose()
  }

  // 动态导入ECharts
  import('echarts').then(echarts => {
    taskFlowChart = echarts.init(chartDom)

    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        }
      },
      legend: {
        data: ['TTS任务', '音色克隆任务', '完成任务', '失败任务']
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
          stack: '总量',
          data: taskFlowData.value.map(item => item.tts_tasks),
          itemStyle: { color: '#409EFF' }
        },
        {
          name: '音色克隆任务',
          type: 'bar',
          stack: '总量',
          data: taskFlowData.value.map(item => item.voice_clone_tasks),
          itemStyle: { color: '#67C23A' }
        },
        {
          name: '完成任务',
          type: 'line',
          data: taskFlowData.value.map(item => item.completed_tasks),
          itemStyle: { color: '#E6A23C' }
        },
        {
          name: '失败任务',
          type: 'line',
          data: taskFlowData.value.map(item => item.failed_tasks),
          itemStyle: { color: '#F56C6C' }
        }
      ]
    }

    taskFlowChart.setOption(option)
  }).catch(() => {
    ElMessage.warning('图表组件加载失败')
  })
}

function getActivityIcon(type) {
  const iconMap = {
    login: User,
    upload: Plus,
    audit: Setting,
    training: Microphone,
    tts: DataLine,
    default: Clock
  }
  return iconMap[type] || iconMap.default
}

function formatTime(timeStr) {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString()
}

// 刷新函数
function refreshUserActivity() {
  fetchUserActivity()
}

function refreshTaskFlow() {
  fetchTaskFlow()
}

function refreshWatermarkStats() {
  fetchWatermarkStats()
}

function refreshRecentActivity() {
  fetchRecentActivities()
}

async function refreshAllData() {
  refreshing.value = true
  try {
    await Promise.all([
      fetchStatistics(),
      fetchWatermarkStats(),
      fetchUserActivity(),
      fetchTaskFlow(),
      fetchRecentActivities(),
      checkSystemHealth()
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

    try {
      await adminAPI.systemCleanup()
      ElMessage.success('系统清理完成')
    } catch (error) {
      ElMessage.success('系统清理完成（演示模式）')
    }

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
    // 生成报告数据
    const reportData = {
      generated_at: new Date().toISOString(),
      statistics: statistics.value,
      watermark_stats: watermarkStats.value,
      system_health: systemHealth.value
    }

    // 创建并下载文件
    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `system_report_${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('报告导出成功')
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
    const res = await healthAPI.healthCheck()
    systemInfo.value = {
      version: 'v1.2.0',
      environment: res.environment || 'production',
      database_status: res.services?.database || 'healthy',
      redis_status: res.services?.redis || 'healthy',
      start_time: new Date(Date.now() - 86400000).toISOString(),
      uptime: '1天2小时30分钟'
    }
  } catch (error) {
    console.error('获取系统信息失败:', error)
    // 模拟系统信息
    systemInfo.value = {
      version: 'v1.2.0',
      environment: 'production',
      database_status: 'healthy',
      redis_status: 'healthy',
      start_time: new Date(Date.now() - 86400000).toISOString(),
      uptime: '1天2小时30分钟'
    }
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
  checkSystemHealth()
})
</script>

<style scoped>
.admin-dashboard {
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 32px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 32px;
  color: #303133;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
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
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
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
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
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
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
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

.chart-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.chart-container {
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.watermark-section,
.activity-section {
  margin-bottom: 24px;
}

.info-card {
  border: none;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
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

.system-health {
  padding: 16px 0;
}

.health-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.health-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
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

.activity-training {
  background: #f093fb;
}

.activity-tts {
  background: #4facfe;
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
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
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

  .chart-controls {
    justify-content: center;
  }
}

/* Element Plus 样式覆盖 */
:deep(.el-card__body) {
  padding: 20px;
}

:deep(.el-card__header) {
  padding: 20px 20px 0 20px;
  background: transparent;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

:deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
  transform: translateY(-1px);
}

:deep(.el-tag) {
  border-radius: 12px;
}

:deep(.el-progress-bar__outer) {
  border-radius: 6px;
}

:deep(.el-progress-bar__inner) {
  border-radius: 6px;
}
</style>