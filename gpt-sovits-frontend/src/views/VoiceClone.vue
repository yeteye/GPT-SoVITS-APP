<!-- ./gpt-sovits-frontend/src/views/VoiceClone.vue -->
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
      <el-col :lg="12" :md="24" :sm="24">
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

          <el-form :model="trainingForm" :rules="trainingRules" ref="trainingFormRef" label-width="120px">
            <el-form-item label="模型名称" prop="modelName">
              <el-input v-model="trainingForm.modelName" placeholder="为你的音色模型起个名字" clearable />
            </el-form-item>

            <el-form-item label="模型描述" prop="description">
              <el-input v-model="trainingForm.description" type="textarea" :rows="3" placeholder="简单描述一下这个音色的特点..."
                maxlength="200" show-word-limit />
            </el-form-item>

            <el-form-item label="选择样本" prop="selectedSamples">
              <div class="sample-selection">
                <el-checkbox-group v-model="trainingForm.selectedSamples">
                  <div v-for="sample in samples" :key="sample.upload_id" class="sample-item">
                    <el-checkbox :label="sample.upload_id">
                      <div class="sample-info">
                        <div class="sample-name">{{ sample.filename }}</div>
                        <div class="sample-meta">
                          {{ formatDuration(sample.duration) }} | {{ formatFileSize(sample.file_size) }}
                        </div>
                      </div>
                    </el-checkbox>
                    <div class="sample-actions">
                      <el-button type="text" @click="previewSample(sample)">
                        <el-icon>
                          <VideoPlay />
                        </el-icon>
                      </el-button>
                      <el-button type="text" @click="deleteSample(sample)" style="color: #f56c6c;">
                        <el-icon>
                          <Delete />
                        </el-icon>
                      </el-button>
                    </div>
                  </div>
                </el-checkbox-group>
              </div>
            </el-form-item>

            <el-form-item label="公开设置">
              <el-switch v-model="trainingForm.isPublic" active-text="公开模型" inactive-text="私有模型" />
              <div class="setting-tip">公开后其他用户可以使用你的音色模型</div>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="startTraining" :loading="isTraining"
                :disabled="trainingForm.selectedSamples.length === 0" size="large">
                <el-icon>
                  <Cpu />
                </el-icon>
                {{ isTraining ? '正在提交训练...' : '开始训练' }}
              </el-button>
              <div class="training-info">
                <span>预计训练时间：{{ estimatedTime }}分钟</span>
              </div>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右侧：任务状态和历史 -->
      <el-col :lg="12" :md="24" :sm="24">
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
              <div class="meta-item">
                <span class="label">样本数量：</span>
                <span class="value">{{ currentTask.sample_count }}个</span>
              </div>
              <div class="meta-item">
                <span class="label">总时长：</span>
                <span class="value">{{ formatDuration(currentTask.total_duration) }}</span>
              </div>
              <div class="meta-item">
                <span class="label">开始时间：</span>
                <span class="value">{{ formatTime(currentTask.created_at) }}</span>
              </div>
              <div class="meta-item" v-if="currentTask.estimated_completion">
                <span class="label">预计完成：</span>
                <span class="value">{{ formatTime(currentTask.estimated_completion) }}</span>
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
            <div v-for="task in tasks" :key="task.task_id" class="task-item" @click="viewTaskDetail(task)">
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

// 训练表单
const trainingForm = reactive({
  modelName: '',
  description: '',
  selectedSamples: [],
  isPublic: false
})

// 表单验证规则
const trainingRules = {
  modelName: [
    { required: true, message: '请输入模型名称', trigger: 'blur' },
    { min: 2, max: 50, message: '模型名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  selectedSamples: [
    { required: true, message: '请至少选择一个音频样本', trigger: 'change' }
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
async function fetchSamples() {
  try {
    const res = await voiceCloneAPI.getUserSamples({ per_page: 50 })
    samples.value = res.data?.samples || []
  } catch (error) {
    ElMessage.error('获取音频样本失败')
  }
}

async function fetchTasks() {
  tasksLoading.value = true
  try {
    const res = await voiceCloneAPI.getUserTasks({ per_page: 20 })
    tasks.value = res.data?.tasks || []

    // 查找当前进行中的任务
    currentTask.value = tasks.value.find(task =>
      ['pending', 'processing', 'training'].includes(task.status)
    ) || null

    // 如果有进行中的任务，开始轮询
    if (currentTask.value) {
      startPolling()
    } else {
      stopPolling()
    }
  } catch (error) {
    ElMessage.error('获取训练任务失败')
  } finally {
    tasksLoading.value = false
  }
}

function startPolling() {
  if (pollingTimer.value) return

  pollingTimer.value = setInterval(() => {
    fetchTasks()
  }, 5000) // 每5秒轮询一次
}

function stopPolling() {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
    pollingTimer.value = null
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
    fetchSamples() // 刷新样本列表

    // 自动选中新上传的样本
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
        is_public: trainingForm.isPublic
      })

      ElMessage.success('训练任务已提交')

      // 重置表单
      trainingForm.modelName = ''
      trainingForm.description = ''
      trainingForm.selectedSamples = []
      trainingForm.isPublic = false

      // 刷新任务列表
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

    // 从选中列表中移除
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
    // 停止播放
    audioPlayer.value.pause()
    currentPlayingSample.value = null
  } else {
    // 开始播放
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
  background: #f8f9fb;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 32px;
  color: white;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
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
}

.header-text p {
  margin: 0;
  font-size: 16px;
  opacity: 0.9;
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
}

.stat-label {
  font-size: 14px;
  opacity: 0.8;
}

.upload-card,
.training-card,
.status-card,
.history-card {
  margin-bottom: 24px;
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
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
}

.help-icon:hover {
  color: #409eff;
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
  background: #f8f9fb;
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.upload-tips h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #333;
}

.upload-tips ul {
  margin: 0;
  padding-left: 20px;
}

.upload-tips li {
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
}

.sample-selection {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  background: #fafafa;
}

.sample-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #eee;
}

.sample-item:last-child {
  border-bottom: none;
}

.sample-info {
  flex: 1;
  margin-left: 8px;
}

.sample-name {
  font-size: 14px;
  color: #333;
  margin-bottom: 4px;
}

.sample-meta {
  font-size: 12px;
  color: #999;
}

.sample-actions {
  display: flex;
  gap: 8px;
}

.setting-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.training-info {
  margin-top: 8px;
  font-size: 12px;
  color: #666;
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
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 16px;
}

.meta-item {
  font-size: 13px;
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
  max-height: 400px;
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
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
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

  .task-meta {
    grid-template-columns: 1fr;
  }

  .task-item {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .task-actions {
    justify-content: center;
  }
}

/* Element Plus 样式覆盖 */
:deep(.el-upload-dragger) {
  border: 2px dashed #d9d9d9;
  border-radius: 12px;
  background: #fafafa;
  transition: all 0.3s ease;
}

:deep(.el-upload-dragger:hover) {
  border-color: #409eff;
  background: #ecf5ff;
}

:deep(.el-progress-bar__outer) {
  border-radius: 4px;
}

:deep(.el-progress-bar__inner) {
  border-radius: 4px;
}

:deep(.el-checkbox-group) {
  width: 100%;
}

:deep(.el-checkbox) {
  width: 100%;
  margin-right: 0;
}

:deep(.el-card__header) {
  padding: 20px 20px 0 20px;
}

:deep(.el-card__body) {
  padding: 20px;
}
</style>