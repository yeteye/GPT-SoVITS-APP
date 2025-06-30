<!-- ./gpt-sovits-frontend/src/views/VoiceClone.vue - 修复版 -->
<template>
  <div class="voice-clone-container">
    <div class="page-header">
      <div class="header-content">
        <div class="header-text">
          <h1>🎙️ 音色克隆</h1>
          <p>上传你的语音样本，AI将学习并生成专属音色模型</p>
        </div>
        <div class="header-stats">
          <div class="stat-item">
            <div class="stat-number">{{ totalSamples }}</div>
            <div class="stat-label">已上传样本</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ trainingTasks }}</div>
            <div class="stat-label">训练中任务</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ completedModels }}</div>
            <div class="stat-label">完成模型</div>
          </div>
        </div>
      </div>
    </div>

    <el-row :gutter="24">
      <!-- 左侧：上传和训练区域 -->
      <el-col :lg="14" :md="24" :sm="24">
        <!-- 音频样本上传 -->
        <el-card class="upload-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <h3>🎵 上传音频样本</h3>
              <el-tooltip content="建议上传10-30秒的高质量音频，包含不同情感和语调">
                <el-icon class="help-icon">
                  <QuestionFilled />
                </el-icon>
              </el-tooltip>
            </div>
          </template>

          <div class="upload-section">
            <el-upload ref="uploadRef" class="audio-upload" drag :action="uploadAction" :headers="uploadHeaders"
              :on-success="handleUploadSuccess" :on-error="handleUploadError" :on-progress="handleUploadProgress"
              :before-upload="beforeUpload" :file-list="fileList" accept="audio/*" multiple :limit="10"
              :on-exceed="handleExceed">
              <div class="upload-content">
                <el-icon class="upload-icon">
                  <Upload />
                </el-icon>
                <div class="upload-text">
                  <div class="main-text">拖拽音频文件到此处，或点击上传</div>
                  <div class="sub-text">支持 WAV、MP3、M4A 格式，单个文件不超过50MB</div>
                </div>
              </div>
            </el-upload>

            <div class="upload-tips">
              <h4>💡 上传建议</h4>
              <ul>
                <li>建议上传3-10个不同内容的音频片段</li>
                <li>每个音频时长10-30秒为最佳</li>
                <li>包含不同情感：平静、开心、严肃等</li>
                <li>确保音频清晰，无背景噪音</li>
                <li>建议在安静环境下录制</li>
              </ul>
            </div>
          </div>
        </el-card>

        <!-- 训练设置 -->
        <el-card class="training-card" shadow="hover" v-if="samples.length > 0">
          <template #header>
            <h3>⚙️ 训练设置</h3>
          </template>

          <el-form :model="trainingForm" :rules="trainingRules" ref="trainingFormRef" label-width="120px"
            class="training-form">
            <div class="form-section">
              <el-form-item label="模型名称" prop="modelName">
                <el-input v-model="trainingForm.modelName" placeholder="为你的音色模型起个名字" clearable />
              </el-form-item>

              <el-form-item label="模型描述" prop="description">
                <el-input v-model="trainingForm.description" type="textarea" :rows="3" placeholder="简单描述一下这个音色的特点..."
                  maxlength="200" show-word-limit />
              </el-form-item>
            </div>

            <div class="form-section">
              <el-form-item label="支持语言" prop="supported_languages">
                <el-select v-model="trainingForm.supported_languages" multiple placeholder="选择支持的语言">
                  <el-option label="中文" value="zh" />
                  <el-option label="英文" value="en" />
                  <el-option label="日语" value="ja" />
                </el-select>
              </el-form-item>

              <el-form-item label="支持情感" prop="supported_emotions">
                <el-select v-model="trainingForm.supported_emotions" multiple placeholder="选择支持的情感">
                  <el-option label="自然" value="neutral" />
                  <el-option label="快乐" value="happy" />
                  <el-option label="悲伤" value="sad" />
                  <el-option label="愤怒" value="angry" />
                </el-select>
              </el-form-item>

              <el-form-item label="是否公开">
                <el-switch v-model="trainingForm.isPublic" active-text="公开模型" inactive-text="私有模型" />
                <div class="setting-tip">公开后其他用户可以使用你的音色模型</div>
              </el-form-item>
            </div>

            <div class="form-actions">
              <el-form-item>
                <el-button type="primary" @click="startTraining" :loading="isTraining"
                  :disabled="trainingForm.selectedSamples.length === 0" size="large" class="training-button">
                  <el-icon>
                    <Cpu />
                  </el-icon>
                  {{ isTraining ? '正在提交训练...' : '开始训练' }}
                </el-button>
                <div class="training-info">
                  <span>预计训练时间：{{ estimatedTime }}分钟</span>
                </div>
              </el-form-item>
            </div>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右侧：样本选择和任务状态 -->
      <el-col :lg="10" :md="24" :sm="24">
        <!-- 样本选择区域 -->
        <el-card class="sample-selection-card" shadow="hover" v-if="samples.length > 0">
          <template #header>
            <h3>🎯 样本选择</h3>
          </template>

          <div class="sample-selection-container">
            <!-- 已选择样本 -->
            <div class="selected-samples">
              <h4>已选择样本 ({{ trainingForm.selectedSamples.length }})</h4>
              <div class="selected-list">
                <div v-for="sampleId in trainingForm.selectedSamples" :key="sampleId" class="selected-item">
                  <div class="sample-info">
                    <div class="sample-name">{{ getSampleById(sampleId)?.filename }}</div>
                    <div class="sample-meta">
                      {{ formatDuration(getSampleById(sampleId)?.duration) }} |
                      {{ formatFileSize(getSampleById(sampleId)?.file_size) }}
                    </div>
                  </div>
                  <div class="sample-actions">
                    <el-button type="text" @click="previewSample(getSampleById(sampleId))" size="small">
                      <el-icon>
                        <VideoPlay />
                      </el-icon>
                    </el-button>
                    <el-button type="text" @click="removeSample(sampleId)" size="small" style="color: #f56c6c;">
                      <el-icon>
                        <Close />
                      </el-icon>
                    </el-button>
                  </div>
                </div>
                <el-empty v-if="trainingForm.selectedSamples.length === 0" description="暂未选择样本" />
              </div>
            </div>

            <!-- 可选择样本 -->
            <div class="available-samples">
              <h4>可选择样本</h4>
              <div class="available-list">
                <div v-for="sample in availableSamples" :key="sample.upload_id" class="available-item"
                  @click="addSample(sample.upload_id)">
                  <div class="sample-info">
                    <div class="sample-name">{{ sample.filename }}</div>
                    <div class="sample-meta">
                      {{ formatDuration(sample.duration) }} | {{ formatFileSize(sample.file_size) }}
                    </div>
                  </div>
                  <div class="sample-actions" @click.stop>
                    <el-button type="text" @click="previewSample(sample)" size="small">
                      <el-icon>
                        <VideoPlay />
                      </el-icon>
                    </el-button>
                    <el-button type="text" @click="deleteSample(sample)" size="small" style="color: #f56c6c;">
                      <el-icon>
                        <Delete />
                      </el-icon>
                    </el-button>
                  </div>
                </div>
                <el-empty v-if="availableSamples.length === 0" description="暂无可选择样本" />
              </div>
            </div>
          </div>
        </el-card>

        <!-- 当前任务状态 -->
        <el-card class="status-card" shadow="hover" v-if="currentTask">
          <template #header>
            <h3>🔄 当前训练任务</h3>
          </template>

          <div class="task-status">
            <div class="task-header">
              <div class="task-name">{{ currentTask.model_name }}</div>
              <el-tag :type="getStatusType(currentTask.status)">
                {{ getStatusText(currentTask.status) }}
              </el-tag>
            </div>

            <div class="task-progress">
              <el-progress :percentage="currentTask.progress || getDefaultProgress(currentTask.status)"
                :status="getProgressStatus(currentTask.status)" :stroke-width="8" :show-text="true" />
              <div class="progress-text">
                {{ getProgressText(currentTask.status) }}
              </div>
            </div>

            <div class="task-meta">
              <div class="meta-row">
                <div class="meta-item">
                  <span class="label">样本数量：</span>
                  <span class="value">{{ currentTask.sample_count }}个</span>
                </div>
                <div class="meta-item">
                  <span class="label">总时长：</span>
                  <span class="value">{{ formatDuration(currentTask.total_duration) }}</span>
                </div>
              </div>
              <div class="meta-row">
                <div class="meta-item">
                  <span class="label">开始时间：</span>
                  <span class="value">{{ formatTime(currentTask.created_at) }}</span>
                </div>
                <div class="meta-item" v-if="currentTask.estimated_completion">
                  <span class="label">预计完成：</span>
                  <span class="value">{{ formatTime(currentTask.estimated_completion) }}</span>
                </div>
              </div>
            </div>

            <div class="task-actions" v-if="canCancelTask(currentTask)">
              <el-button type="danger" @click="cancelTask(currentTask.task_id)">
                取消训练
              </el-button>
            </div>
          </div>
        </el-card>

        <!-- 历史任务列表 -->
        <el-card class="history-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <h3>📋 训练历史</h3>
              <el-button type="text" @click="refreshTasks">
                <el-icon>
                  <Refresh />
                </el-icon>
                刷新
              </el-button>
            </div>
          </template>

          <div class="task-list" v-loading="tasksLoading">
            <div v-for="task in tasks.slice(0, 5)" :key="task.task_id" class="task-item" @click="viewTaskDetail(task)">
              <div class="task-info">
                <div class="task-title">{{ task.model_name }}</div>
                <div class="task-time">{{ formatTime(task.created_at) }}</div>
              </div>
              <div class="task-status-badge">
                <el-tag :type="getStatusType(task.status)" size="small">
                  {{ getStatusText(task.status) }}
                </el-tag>
              </div>
              <div class="task-actions">
                <el-button v-if="task.status === 'completed'" type="text" size="small" @click.stop="useModel(task)">
                  使用
                </el-button>
                <el-button v-if="task.status === 'failed'" type="text" size="small"
                  @click.stop="retryTask(task.task_id)">
                  重试
                </el-button>
                <el-button type="text" size="small" @click.stop="viewTaskDetail(task)">
                  详情
                </el-button>
              </div>
            </div>

            <el-empty v-if="!tasksLoading && tasks.length === 0" description="暂无训练记录" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 音频预览播放器 -->
    <audio ref="audioPlayer" style="display: none" @ended="onAudioEnded" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Upload,
  QuestionFilled,
  VideoPlay,
  Delete,
  Close,
  Cpu,
  Refresh
} from '@element-plus/icons-vue'
import { voiceCloneAPI } from '@/api'

const router = useRouter()

// 响应式数据
const uploadRef = ref()
const trainingFormRef = ref()
const audioPlayer = ref()
const fileList = ref([])
const samples = ref([])
const tasks = ref([])
const currentTask = ref(null)
const isTraining = ref(false)
const tasksLoading = ref(false)
const currentPlayingSample = ref(null)
const pollingTimer = ref(null)

// 统计数据
const totalSamples = computed(() => samples.value.length)
const trainingTasks = computed(() => tasks.value.filter(t => ['pending', 'processing', 'training'].includes(t.status)).length)
const completedModels = computed(() => tasks.value.filter(t => t.status === 'completed').length)

// 可选择的样本（未被选中的样本）
const availableSamples = computed(() => {
  return samples.value.filter(sample => !trainingForm.selectedSamples.includes(sample.upload_id))
})

// 训练表单
const trainingForm = reactive({
  modelName: '',
  description: '',
  selectedSamples: [],
  supported_languages: ['zh'],
  supported_emotions: ['neutral'],
  isPublic: false
})

// 表单验证规则
const trainingRules = {
  modelName: [
    { required: true, message: '请输入模型名称', trigger: 'blur' },
    { min: 2, max: 50, message: '模型名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入模型描述', trigger: 'blur' }
  ],
  supported_languages: [
    { required: true, message: '请选择支持的语言', trigger: 'change' }
  ],
  supported_emotions: [
    { required: true, message: '请选择支持的情感', trigger: 'change' }
  ]
}

// 上传配置
const uploadAction = computed(() => `${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000/api'}/voice-clone/upload-sample`)
const uploadHeaders = computed(() => ({
  'Authorization': `Bearer ${localStorage.getItem('token')}`
}))

// 预计训练时间
const estimatedTime = computed(() => {
  const sampleCount = trainingForm.selectedSamples.length
  return Math.max(3, Math.min(15, sampleCount * 2))
})

// 方法
function getSampleById(id) {
  return samples.value.find(sample => sample.upload_id === id)
}

function addSample(sampleId) {
  if (!trainingForm.selectedSamples.includes(sampleId)) {
    trainingForm.selectedSamples.push(sampleId)
  }
}

function removeSample(sampleId) {
  const index = trainingForm.selectedSamples.indexOf(sampleId)
  if (index > -1) {
    trainingForm.selectedSamples.splice(index, 1)
  }
}

async function fetchSamples() {
  try {
    const res = await voiceCloneAPI.getUserSamples({ per_page: 50 })
    samples.value = res.data?.samples || []
  } catch (error) {
    console.error('获取音频样本失败:', error)
    ElMessage.error('获取音频样本失败')
  }
}

async function fetchTasks() {
  tasksLoading.value = true
  try {
    const res = await voiceCloneAPI.getUserTasks({ per_page: 20 })
    tasks.value = res.data?.tasks || []

    const activeTask = tasks.value.find(task =>
      task &&
      task.task_id &&
      typeof task.task_id === 'string' &&
      task.task_id !== 'undefined' &&
      ['pending', 'processing', 'training'].includes(task.status)
    )

    if (activeTask && (!currentTask.value || currentTask.value.task_id !== activeTask.task_id)) {
      currentTask.value = activeTask
      startPolling()
    } else if (!activeTask && currentTask.value) {
      currentTask.value = null
      stopPolling()
    }
  } catch (error) {
    console.error('获取训练任务失败:', error)
    ElMessage.error('获取训练任务失败')
  } finally {
    tasksLoading.value = false
  }
}

function startPolling() {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
  }

  if (!currentTask.value || !currentTask.value.task_id) {
    console.warn('无法开始轮询：任务ID无效')
    return
  }

  pollingTimer.value = setInterval(() => {
    if (currentTask.value &&
      currentTask.value.task_id &&
      ['pending', 'processing', 'training'].includes(currentTask.value.status)) {
      fetchTaskDetail(currentTask.value.task_id)
    } else {
      stopPolling()
    }
  }, 5000)
}

function stopPolling() {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
    pollingTimer.value = null
  }
}

async function fetchTaskDetail(taskId) {
  if (!taskId ||
    taskId === 'undefined' ||
    taskId === null ||
    taskId === 'null' ||
    typeof taskId !== 'string' ||
    taskId.trim() === '') {
    console.warn('无效的任务ID:', taskId)
    stopPolling()
    currentTask.value = null
    return
  }

  try {
    const res = await voiceCloneAPI.getTaskDetail(taskId)
    const task = res.data

    if (currentTask.value && currentTask.value.task_id === taskId) {
      currentTask.value = task

      if (!['pending', 'processing', 'training'].includes(task.status)) {
        currentTask.value = null
        stopPolling()
        fetchTasks()

        if (task.status === 'completed') {
          ElMessage.success('模型训练完成！')
        } else if (task.status === 'failed') {
          ElMessage.error('模型训练失败')
        }
      }
    }
  } catch (error) {
    console.error('获取任务详情失败:', error)
    if (error.response?.status === 404 || error.message?.includes('Invalid task ID')) {
      console.warn('任务不存在，停止轮询')
      currentTask.value = null
      stopPolling()
    }
  }
}

function beforeUpload(file) {
  const isAudio = file.type.startsWith('audio/')
  const isLt50M = file.size / 1024 / 1024 < 50

  if (!isAudio) {
    ElMessage.error('只能上传音频文件!')
    return false
  }
  if (!isLt50M) {
    ElMessage.error('上传文件大小不能超过 50MB!')
    return false
  }
  return true
}

function handleUploadSuccess(response, file) {
  if (response.success) {
    ElMessage.success(`${file.name} 上传成功`)
    fetchSamples()

    if (response.data?.upload_id) {
      trainingForm.selectedSamples.push(response.data.upload_id)
    }
  } else {
    ElMessage.error(`${file.name} 上传失败: ${response.message}`)
  }
}

function handleUploadError(error, file) {
  console.error('Upload error:', error)
  ElMessage.error(`${file.name} 上传失败`)
}

function handleUploadProgress(event, file) {
  // 可以在这里显示上传进度
}

function handleExceed(files, fileList) {
  ElMessage.warning(`最多只能上传 10 个文件，当前选择了 ${files.length} 个文件，已上传 ${fileList.length} 个文件`)
}

async function startTraining() {
  if (!trainingFormRef.value) return

  // 检查是否选择了样本
  if (trainingForm.selectedSamples.length === 0) {
    ElMessage.warning('请至少选择一个音频样本')
    return
  }

  trainingFormRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      await ElMessageBox.confirm(
        '确定要开始训练吗？训练过程大约需要几分钟时间。',
        '确认训练',
        { type: 'info' }
      )

      isTraining.value = true

      const res = await voiceCloneAPI.startTraining({
        model_name: trainingForm.modelName,
        sample_ids: trainingForm.selectedSamples,
        description: trainingForm.description,
        supported_languages: trainingForm.supported_languages,
        supported_emotions: trainingForm.supported_emotions,
        is_public: trainingForm.isPublic
      })

      ElMessage.success('训练任务已提交')

      // 重置表单
      trainingForm.modelName = ''
      trainingForm.description = ''
      trainingForm.selectedSamples = []
      trainingForm.supported_languages = ['zh']
      trainingForm.supported_emotions = ['neutral']
      trainingForm.isPublic = false

      fetchTasks()

    } catch (error) {
      if (error !== 'cancel') {
        ElMessage.error(error?.response?.data?.message || '提交训练失败')
      }
    } finally {
      isTraining.value = false
    }
  })
}

async function cancelTask(taskId) {
  try {
    await ElMessageBox.confirm('确定要取消训练吗？', '确认取消', { type: 'warning' })

    await voiceCloneAPI.cancelTask(taskId)
    ElMessage.success('训练任务已取消')
    currentTask.value = null
    stopPolling()
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('取消训练失败')
    }
  }
}

async function retryTask(taskId) {
  try {
    await voiceCloneAPI.retryTask(taskId)
    ElMessage.success('任务已重新提交')
    fetchTasks()
  } catch (error) {
    ElMessage.error('重试失败')
  }
}

async function deleteSample(sample) {
  try {
    await ElMessageBox.confirm(`确定要删除 "${sample.filename}" 吗？`, '确认删除', { type: 'warning' })

    await voiceCloneAPI.deleteSample(sample.upload_id)
    ElMessage.success('样本已删除')

    const index = trainingForm.selectedSamples.indexOf(sample.upload_id)
    if (index > -1) {
      trainingForm.selectedSamples.splice(index, 1)
    }

    fetchSamples()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

function previewSample(sample) {
  if (currentPlayingSample.value === sample.upload_id) {
    audioPlayer.value.pause()
    currentPlayingSample.value = null
  } else {
    if (sample.file_url) {
      audioPlayer.value.src = sample.file_url
      audioPlayer.value.play()
      currentPlayingSample.value = sample.upload_id
    } else {
      ElMessage.warning('音频文件不可用')
    }
  }
}

function onAudioEnded() {
  currentPlayingSample.value = null
}

function viewTaskDetail(task) {
  router.push({
    name: 'Status',
    params: { taskId: task.task_id },
    query: { type: 'voice-clone' }
  })
}

function useModel(task) {
  router.push({
    name: 'TTSPlayground',
    query: { model_id: task.model_id }
  })
}

function refreshTasks() {
  fetchTasks()
}

// 工具函数
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

function getStatusType(status) {
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

function getDefaultProgress(status) {
  const progressMap = {
    'pending': 10,
    'processing': 30,
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

function getProgressText(status) {
  const textMap = {
    'pending': '任务已提交，等待开始训练...',
    'processing': '正在预处理音频数据...',
    'training': 'AI正在学习你的声音特征...',
    'completed': '训练完成！',
    'failed': '训练失败',
    'cancelled': '训练已取消'
  }
  return textMap[status] || ''
}

function canCancelTask(task) {
  return ['pending', 'processing', 'training'].includes(task.status)
}

function formatDuration(seconds) {
  if (!seconds) return '0s'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return mins > 0 ? `${mins}m${secs}s` : `${secs}s`
}

function formatFileSize(bytes) {
  if (!bytes) return '0B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatTime(timeStr) {
  if (!timeStr) return ''
  return new Date(timeStr).toLocaleString()
}

onMounted(() => {
  fetchSamples()
  fetchTasks()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.voice-clone-container {
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 32px;
  color: #333;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-text h1 {
  margin: 0 0 8px 0;
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.header-text p {
  margin: 0;
  font-size: 16px;
  color: #666;
}

.header-stats {
  display: flex;
  gap: 32px;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 4px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.upload-card,
.training-card,
.sample-selection-card,
.status-card,
.history-card {
  margin-bottom: 24px;
  border-radius: 16px;
  border: none;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
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
  font-weight: 600;
  color: #333;
}

.help-icon {
  color: #909399;
  cursor: pointer;
  transition: color 0.3s ease;
}

.help-icon:hover {
  color: #667eea;
}

.upload-section {
  margin-bottom: 16px;
}

.audio-upload {
  margin-bottom: 24px;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px;
  text-align: center;
}

.upload-icon {
  font-size: 48px;
  color: #c0c4cc;
  margin-bottom: 16px;
}

.main-text {
  font-size: 16px;
  color: #606266;
  margin-bottom: 8px;
}

.sub-text {
  font-size: 14px;
  color: #909399;
}

.upload-tips {
  background: linear-gradient(135deg, #f8f9fb 0%, #e8f4f8 100%);
  padding: 20px;
  border-radius: 12px;
  border-left: 4px solid #667eea;
}

.upload-tips h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #333;
  font-weight: 600;
}

.upload-tips ul {
  margin: 0;
  padding-left: 20px;
}

.upload-tips li {
  font-size: 13px;
  color: #666;
  margin-bottom: 6px;
  line-height: 1.5;
}

.training-form {
  padding: 0;
}

.form-section {
  background: linear-gradient(135deg, #fafafa 0%, #f0f0f0 100%);
  padding: 24px;
  margin-bottom: 20px;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
}

.form-actions {
  text-align: center;
  padding: 24px 0;
}

.training-button {
  width: 200px;
  height: 48px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 24px;
  font-weight: 600;
}

.training-info {
  margin-top: 12px;
  font-size: 12px;
  color: #666;
}

.setting-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

/* 样本选择区域样式 */
.sample-selection-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-height: 500px;
}

.selected-samples,
.available-samples {
  flex: 1;
}

.selected-samples h4,
.available-samples h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
  padding-bottom: 8px;
  border-bottom: 2px solid #e4e7ed;
}

.selected-list,
.available-list {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fafafa;
}

.selected-item,
.available-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
  transition: background-color 0.3s ease;
}

.selected-item:last-child,
.available-item:last-child {
  border-bottom: none;
}

.available-item {
  cursor: pointer;
}

.available-item:hover {
  background: #f0f8ff;
}

.selected-item {
  background: linear-gradient(135deg, #e8f5e8 0%, #f0f8e8 100%);
  border-left: 3px solid #67c23a;
}

.sample-info {
  flex: 1;
}

.sample-name {
  font-size: 14px;
  color: #333;
  margin-bottom: 4px;
  font-weight: 500;
}

.sample-meta {
  font-size: 12px;
  color: #999;
}

.sample-actions {
  display: flex;
  gap: 8px;
}

.task-status {
  padding: 16px 0;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.task-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.task-progress {
  margin-bottom: 16px;
}

.progress-text {
  text-align: center;
  margin-top: 8px;
  font-size: 13px;
  color: #666;
}

.task-meta {
  margin-bottom: 16px;
}

.meta-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.meta-item {
  font-size: 13px;
  flex: 1;
}

.meta-item .label {
  color: #999;
}

.meta-item .value {
  color: #333;
  font-weight: 500;
}

.task-actions {
  text-align: center;
}

.task-list {
  max-height: 300px;
  overflow-y: auto;
}

.task-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fff;
}

.task-item:hover {
  border-color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15);
}

.task-info {
  flex: 1;
}

.task-title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.task-time {
  font-size: 12px;
  color: #999;
}

.task-status-badge {
  margin-right: 12px;
}

.task-actions {
  display: flex;
  gap: 4px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .voice-clone-container {
    padding: 16px;
  }

  .header-content {
    flex-direction: column;
    text-align: center;
    gap: 20px;
  }

  .header-stats {
    gap: 20px;
  }

  .form-section {
    padding: 16px;
  }

  .meta-row {
    flex-direction: column;
    gap: 4px;
  }

  .task-item {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .task-actions {
    justify-content: center;
  }

  .sample-selection-container {
    gap: 16px;
  }
}

/* Element Plus 样式覆盖 */
:deep(.el-upload-dragger) {
  border: 2px dashed #d9d9d9;
  border-radius: 12px;
  background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
  transition: all 0.3s ease;
}

:deep(.el-upload-dragger:hover) {
  border-color: #667eea;
  background: linear-gradient(135deg, #ecf5ff 0%, #e8f4f8 100%);
}

:deep(.el-progress-bar__outer) {
  border-radius: 8px;
  background: #e4e7ed;
}

:deep(.el-progress-bar__inner) {
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

:deep(.el-card__header) {
  padding: 20px 20px 0 20px;
  background: transparent;
}

:deep(.el-card__body) {
  padding: 20px;
}

:deep(.el-form-item) {
  margin-bottom: 18px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
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

:deep(.el-switch.is-checked .el-switch__core) {
  background-color: #667eea;
}
</style>