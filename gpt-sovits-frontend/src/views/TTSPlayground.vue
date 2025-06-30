<!-- ./gpt-sovits-frontend/src/views/TTSPlayground.vue - 修复版 -->
<template>
  <div class="tts-playground">
    <!-- 主体内容区域 -->
    <el-container class="main-content">
      <!-- 文本输入与配置面板 -->
      <el-aside class="editor-panel">
        <div class="panel-header">
          <h2>文本转语音</h2>
          <p>输入文本，选择音色和参数，快速生成语音</p>
        </div>

        <!-- 未登录提示 -->
        <el-alert v-if="!isLoggedIn" title="提示" type="warning" :closable="false" style="margin-bottom: 20px">
          <template #default>
            <div>
              <p>您可以浏览音色库和试听功能，但需要登录后才能生成语音</p>
              <el-button type="primary" size="small" @click="goToLogin">
                立即登录
              </el-button>
            </div>
          </template>
        </el-alert>

        <el-form :model="form" label-position="top" class="tts-form">
          <!-- 文本语言选择 -->
          <el-form-item label="文本语言">
            <el-select v-model="form.textLang" placeholder="选择文本语言" style="width: 100%">
              <el-option label="中文" value="zh-CN" />
              <el-option label="英文" value="en-US" />
              <el-option label="日语" value="ja-JP" />
            </el-select>
          </el-form-item>

          <!-- 模型选择 -->
          <el-form-item label="选择模型">
            <el-select v-model="form.selectedModel" placeholder="选择语音模型" style="width: 100%" :loading="modelsLoading"
              :disabled="!isLoggedIn" @change="onModelChange">
              <el-option v-for="model in availableModels" :key="model.id" :label="model.name" :value="model.id">
                <span style="float: left">{{ model.name }}</span>
                <span style="float: right; color: #8492a6; font-size: 13px">
                  {{ model.model_type === 'official' ? '官方' : '用户' }}
                </span>
              </el-option>
            </el-select>
          </el-form-item>

          <!-- 情感选择 -->
          <el-form-item label="情感风格">
            <el-select v-model="form.selectedEmotion" placeholder="选择情感" style="width: 100%"
              :disabled="!form.selectedModel || !isLoggedIn">
              <el-option v-for="emotion in availableEmotions" :key="emotion.value" :label="emotion.label"
                :value="emotion.value" />
            </el-select>
          </el-form-item>

          <!-- 高级参数 -->
          <el-form-item label="语速调节">
            <el-slider v-model="form.speed" :min="0.5" :max="2.0" :step="0.1" show-input :show-input-controls="false"
              style="margin-right: 12px" :disabled="!isLoggedIn" />
          </el-form-item>

          <!-- 文本输入 -->
          <el-form-item label="输入文本">
            <el-input v-model="form.text" type="textarea" placeholder="请输入要合成的文本，支持多行输入..." :rows="6" :maxlength="1000"
              show-word-limit resize="none" :disabled="!isLoggedIn" />
          </el-form-item>

          <!-- 操作按钮 -->
          <div class="control-buttons">
            <el-button type="primary" :loading="generating" @click="onSynthesize"
              :disabled="!canGenerate || !isLoggedIn" size="large" style="width: 100%">
              <el-icon>
                <Microphone />
              </el-icon>
              {{ generating ? '生成中...' : '生成语音' }}
            </el-button>
            <el-button @click="resetForm" style="width: 100%; margin-top: 12px" :disabled="!isLoggedIn">
              重置
            </el-button>
          </div>
        </el-form>

        <!-- 任务进度显示 -->
        <div v-if="currentTask" class="task-progress">
          <h3>当前任务进度</h3>
          <el-progress :percentage="getTaskProgress(currentTask.status)"
            :status="getProgressStatus(currentTask.status)" />
          <p class="progress-text">{{ getProgressText(currentTask.status) }}</p>
          <div class="task-actions">
            <el-button v-if="currentTask.status === 'completed' && currentTask.result_url" type="success" size="small"
              @click="downloadResult(currentTask)">
              下载结果
            </el-button>
            <el-button v-if="['pending', 'processing'].includes(currentTask.status)" type="danger" size="small"
              @click="cancelTask(currentTask.id)">
              取消任务
            </el-button>
          </div>
        </div>

        <!-- 播放结果区域 -->
        <div v-if="audioUrl" class="audio-result">
          <div class="result-header">
            <h3>生成结果</h3>
            <el-button type="success" size="small" @click="downloadAudio">
              <el-icon>
                <Download />
              </el-icon>
              下载
            </el-button>
          </div>
          <audio ref="audioPlayer" :src="audioUrl" controls style="width: 100%" @loadedmetadata="onAudioLoaded" />
          <div class="audio-info" v-if="audioInfo">
            <p>时长: {{ audioInfo.duration }}秒</p>
            <p>大小: {{ audioInfo.size }}</p>
          </div>
        </div>
      </el-aside>

      <!-- 音色库选择面板 -->
      <el-main class="voice-library">
        <div class="library-header">
          <h2>音色库</h2>
          <el-input v-model="searchKeyword" placeholder="搜索音色..." clearable style="width: 300px" @input="onSearch">
            <template #prefix>
              <el-icon>
                <Search />
              </el-icon>
            </template>
          </el-input>
        </div>

        <!-- 筛选标签 -->
        <div class="filter-tags">
          <el-tag v-for="tag in filterTags" :key="tag" :type="selectedTags.includes(tag) ? '' : 'info'"
            :effect="selectedTags.includes(tag) ? 'dark' : 'plain'" @click="toggleTag(tag)"
            style="margin-right: 8px; margin-bottom: 8px; cursor: pointer">
            {{ tag }}
          </el-tag>
        </div>

        <!-- 音色卡片网格 -->
        <div class="voice-grid" v-loading="voicesLoading">
          <div v-for="voice in filteredVoices" :key="voice.id" class="voice-card"
            :class="{ 'selected': selectedVoice === voice.id }" @click="selectVoice(voice)">
            <div class="voice-avatar">
              <img :src="voice.avatar || defaultAvatar" :alt="voice.name" />
              <div class="voice-overlay">
                <el-button type="primary" size="small" circle @click.stop="previewVoice(voice)">
                  <el-icon>
                    <VideoPlay />
                  </el-icon>
                </el-button>
              </div>
            </div>
            <div class="voice-info">
              <div class="voice-name">{{ voice.name }}</div>
              <div class="voice-desc">{{ voice.description }}</div>

              <!-- 新增：重要信息显示 -->
              <div class="voice-details">
                <div class="detail-item">
                  <span class="detail-label">支持语言：</span>
                  <div class="detail-tags">
                    <el-tag v-for="lang in voice.supported_languages" :key="lang" size="small" type="primary"
                      effect="plain">
                      {{ getLanguageDisplay(lang) }}
                    </el-tag>
                  </div>
                </div>
                <div class="detail-item">
                  <span class="detail-label">支持情感：</span>
                  <div class="detail-tags">
                    <el-tag v-for="emotion in voice.supported_emotions" :key="emotion" size="small" type="success"
                      effect="plain">
                      {{ getEmotionDisplay(emotion) }}
                    </el-tag>
                  </div>
                </div>
              </div>

              <div class="voice-tags">
                <el-tag v-for="tag in voice.tags" :key="tag" size="small" effect="plain">
                  {{ tag }}
                </el-tag>
              </div>
              <div class="voice-stats">
                <span><el-icon>
                    <Star />
                  </el-icon> {{ voice.rating || 5.0 }}</span>
                <span><el-icon>
                    <Microphone />
                  </el-icon> {{ voice.usage_count || 0 }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <el-empty v-if="!voicesLoading && filteredVoices.length === 0" description="暂无匹配的音色" />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Microphone,
  Download,
  Search,
  VideoPlay,
  Star
} from '@element-plus/icons-vue'
import { ttsAPI, tts2API, modelsAPI } from '@/api'
import { userStore } from '@/stores/user'

const router = useRouter()

// 表单数据
const form = ref({
  text: '你好，欢迎使用 GPT-SoVITS 在线语音合成系统。',
  textLang: '中文',
  selectedModel: null,
  selectedEmotion: 'neutral',
  speed: 1.0
})

// 状态变量
const generating = ref(false)
const modelsLoading = ref(false)
const voicesLoading = ref(false)
const audioUrl = ref(null)
const audioInfo = ref(null)
const selectedVoice = ref(null)
const searchKeyword = ref('')
const selectedTags = ref([])
const currentTask = ref(null)
const pollingTimer = ref(null)

// 数据
const availableModels = ref([])
const availableEmotions = ref([
  { label: '自然', value: 'neutral' },
  { label: '快乐', value: 'happy' },
  { label: '悲伤', value: 'sad' },
  { label: '愤怒', value: 'angry' },
  { label: '惊讶', value: 'surprised' }
])
const voices = ref([])
const filterTags = ref(['男声', '女声', '温柔', '磁性', '播音', '童声'])

const defaultAvatar = new URL('@/assets/voice.png', import.meta.url).href

// 计算属性
const isLoggedIn = computed(() => userStore.isLoggedIn.value)

const canGenerate = computed(() => {
  return form.value.text.trim() && form.value.selectedModel && selectedVoice.value && isLoggedIn.value
})

const filteredVoices = computed(() => {
  let result = voices.value

  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(voice =>
      voice.name.toLowerCase().includes(keyword) ||
      voice.description.toLowerCase().includes(keyword)
    )
  }

  // 标签筛选
  if (selectedTags.value.length > 0) {
    result = result.filter(voice =>
      selectedTags.value.some(tag => voice.tags?.includes(tag))
    )
  }

  return result
})

// 方法
const goToLogin = () => {
  router.push({ name: 'Login', query: { redirect: router.currentRoute.value.fullPath } })
}

// 新增：语言和情感显示名称转换
function getLanguageDisplay(lang) {
  const langMap = {
    'zh-CN': '中文',
    'en-US': '英文',
    'ja-JP': '日语'
  }
  return langMap[lang] || lang
}

function getEmotionDisplay(emotion) {
  const emotionMap = {
    'neutral': '自然',
    'happy': '快乐',
    'sad': '悲伤',
    'angry': '愤怒',
    'surprised': '惊讶'
  }
  return emotionMap[emotion] || emotion
}

async function fetchModels() {
  modelsLoading.value = true
  try {
    const res = await ttsAPI.getAvailableModels({ per_page: 50 })
    availableModels.value = res.data?.models || []
  } catch (error) {
    console.error('获取模型列表失败:', error)
    ElMessage.error('获取模型列表失败')
  } finally {
    modelsLoading.value = false
  }
}

async function fetchVoices() {
  voicesLoading.value = true
  try {
    const res = await ttsAPI.getAvailableModels({ per_page: 100 })
    voices.value = (res.data?.models || [])
      .filter(model => model.is_public)
      .map(model => ({
        id: model.id,
        name: model.name,
        description: model.description || '暂无描述',
        avatar: model.avatar_url,
        tags: model.voice_characteristics || (model.tags ? model.tags.map(tag => tag.name) : []),
        rating: model.quality_score,
        usage_count: model.usage_count,
        supported_languages: model.supported_languages || ['zh-CN'],
        supported_emotions: model.supported_emotions || ['neutral']
      }))
  } catch (error) {
    console.error('获取音色库失败:', error)
    ElMessage.error('获取音色库失败')
  } finally {
    voicesLoading.value = false
  }
}

function selectVoice(voice) {
  selectedVoice.value = voice.id
  if (!form.value.selectedModel) {
    form.value.selectedModel = voice.id
  }
}

function toggleTag(tag) {
  const index = selectedTags.value.indexOf(tag)
  if (index > -1) {
    selectedTags.value.splice(index, 1)
  } else {
    selectedTags.value.push(tag)
  }
}

function onSearch() {
  // 搜索逻辑已在computed中处理
}

function onModelChange(modelId) {
  selectedVoice.value = modelId
  form.value.selectedEmotion = 'neutral'
}

async function previewVoice(voice) {
  ElMessage.info(`预览 ${voice.name} - 功能开发中`)
}

async function onSynthesize() {
  if (!canGenerate.value) {
    if (!isLoggedIn.value) {
      ElMessage.warning('请先登录')
      goToLogin()
      return
    }
    ElMessage.warning('请完善必填信息')
    return
  }

  generating.value = true

  if (audioUrl.value) {
    URL.revokeObjectURL(audioUrl.value)
    audioUrl.value = null
    audioInfo.value = null
  }

  try {
    const payload = {
      text: form.value.text,
      model_id: form.value.selectedModel,
      emotion: form.value.selectedEmotion,
      speed: form.value.speed,
      language: form.value.textLang
    }
    const realpayload = {
      text: "",
      text_lang: "",
      ref_audio_path: "",
      aux_ref_audio_paths: [],
      prompt_text: "",
      prompt_lang: "",
      top_k: 5,
      top_p: 1,
      temperature: 1,
      text_split_method: "cut0",
      batch_size: 1,
      batch_threshold: 0.75,
      split_bucket: True,
      speed_factor: 1.0,
      streaming_mode: False,
      seed: -1,
      parallel_infer: True,
      repetition_penalty: 1.35,
      sample_steps: 32,
      super_sampling: False
    }

    const response = await tts2API.generateSpeech(payload)

    if (response.data?.audio_url) {
      audioUrl.value = response.data.audio_url
      ElMessage.success('语音生成成功')
    } else if (response.data?.task_id) {
      currentTask.value = {
        id: response.data.task_id,
        status: 'pending',
        created_at: response.data.created_at,  // 使用后端返回的时间
        text: response.data.text,
        model_id: response.data.model_id,
        emotion: response.data.emotion,
        speed: response.data.speed
      }
      startPolling(response.data.task_id)
      ElMessage.success('任务已提交，请等待处理')
    } else {
      throw new Error('生成失败')
    }
  } catch (error) {
    console.error('语音生成失败:', error)
    ElMessage.error(error?.response?.data?.message || '语音生成失败')
  } finally {
    generating.value = false
  }
}

function startPolling(taskId) {
  if (pollingTimer.value) return

  pollingTimer.value = setInterval(async () => {
    try {
      const res = await tts2API.getTTSTaskDetail(taskId)
      const task = res.data

      currentTask.value = task

      if (task.status === 'completed') {
        stopPolling()
        if (task.result_url) {
          audioUrl.value = task.result_url
          ElMessage.success('语音生成完成')
        } else {
          const audioRes = await ttsAPI.downloadAudio(taskId)
          const blob = new Blob([audioRes.data], { type: 'audio/wav' })
          audioUrl.value = URL.createObjectURL(blob)

          audioInfo.value = {
            duration: (blob.size / 16000).toFixed(1),
            size: formatFileSize(blob.size)
          }
          ElMessage.success('语音生成完成')
        }
      } else if (task.status === 'failed') {
        stopPolling()
        ElMessage.error(task.error_message || '生成失败')
        currentTask.value = null
      }
    } catch (error) {
      console.error('轮询任务状态失败:', error)
    }
  }, 12000)
}

function stopPolling() {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
    pollingTimer.value = null
  }
}

async function cancelTask(taskId) {
  try {
    ElMessage.info('任务取消功能开发中')
  } catch (error) {
    ElMessage.error('取消任务失败')
  }
}

function getTaskProgress(status) {
  const progressMap = {
    'pending': 10,
    'processing': 50,
    'completed': 100,
    'failed': 0
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
    'pending': '任务已提交，等待处理...',
    'processing': '正在生成语音，请稍候...',
    'completed': '语音生成完成！',
    'failed': '生成失败'
  }
  return textMap[status] || ''
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function onAudioLoaded() {
  const audio = document.querySelector('audio')
  if (audio && audioInfo.value) {
    audioInfo.value.duration = audio.duration.toFixed(1)
  }
}

async function downloadAudio() {
  if (!audioUrl.value) return

  try {
    const link = document.createElement('a')
    link.href = audioUrl.value
    link.download = `tts_${Date.now()}.wav`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    ElMessage.success('下载成功')
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

async function downloadResult(task) {
  try {
    if (task.result_url) {
      window.open(task.result_url, '_blank')
    } else {
      const res = await ttsAPI.downloadAudio(task.id)
      const blob = new Blob([res.data])
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `tts_${task.id}.wav`
      link.click()
      URL.revokeObjectURL(url)
    }
    ElMessage.success('下载开始')
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

function resetForm() {
  form.value = {
    text: '你好，欢迎使用 GPT-SoVITS 在线语音合成系统。',
    textLang: 'zh-CN',
    selectedModel: null,
    selectedEmotion: 'neutral',
    speed: 1.0
  }
  selectedVoice.value = null

  if (audioUrl.value) {
    URL.revokeObjectURL(audioUrl.value)
    audioUrl.value = null
    audioInfo.value = null
  }

  currentTask.value = null
  stopPolling()
}

// 监听模型变化，自动获取支持的情感
watch(() => form.value.selectedModel, async (newModelId) => {
  if (newModelId) {
    try {
      const res = await ttsAPI.getModelDetail(newModelId)
      const model = res.data
      if (model.supported_emotions) {
        const emotions = model.supported_emotions.map(emotion => ({
          label: getEmotionDisplay(emotion),
          value: emotion
        }))
        availableEmotions.value = emotions

        if (emotions.length > 0) {
          form.value.selectedEmotion = emotions[0].value
        }
      }
    } catch (error) {
      console.error('获取模型详情失败:', error)
    }
  }
})

onMounted(() => {
  fetchModels()
  fetchVoices()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.tts-playground {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.main-content {
  height: 100vh;
  overflow: hidden;
}

.editor-panel {
  width: 450px;
  background: #fff;
  padding: 24px;
  border-right: 1px solid #e4e7ed;
  overflow-y: auto;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
}

.panel-header {
  margin-bottom: 24px;
  text-align: center;
}

.panel-header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #303133;
  font-weight: 600;
}

.panel-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.tts-form {
  margin-bottom: 24px;
}

.control-buttons {
  margin-top: 20px;
}

.task-progress {
  margin-top: 24px;
  padding: 16px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  border-radius: 12px;
  border: 1px solid #e4e7ed;
}

.task-progress h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #303133;
}

.progress-text {
  margin: 8px 0;
  font-size: 12px;
  color: #666;
  text-align: center;
}

.task-actions {
  margin-top: 12px;
  text-align: center;
}

.audio-result {
  margin-top: 24px;
  padding: 16px;
  background: linear-gradient(135deg, #e8f5e8 0%, #f0f8e8 100%);
  border-radius: 12px;
  border: 1px solid #b3d9b3;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.result-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.audio-info {
  margin-top: 8px;
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #909399;
}

.audio-info p {
  margin: 0;
}

.voice-library {
  padding: 24px;
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
}

.library-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.library-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
  font-weight: 600;
}

.filter-tags {
  margin-bottom: 20px;
}

.voice-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.voice-card {
  background: #fff;
  border: 2px solid #e4e7ed;
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.voice-card:hover {
  border-color: #409eff;
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(64, 158, 255, 0.2);
}

.voice-card.selected {
  border-color: #409eff;
  background: linear-gradient(135deg, #ecf5ff 0%, #fff 100%);
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.3);
}

.voice-avatar {
  position: relative;
  height: 160px;
  overflow: hidden;
}

.voice-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.voice-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.voice-card:hover .voice-overlay {
  opacity: 1;
}

.voice-info {
  padding: 20px;
}

.voice-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
  line-height: 1.4;
}

.voice-desc {
  font-size: 14px;
  color: #606266;
  margin-bottom: 12px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 新增：音色详细信息样式 */
.voice-details {
  margin-bottom: 12px;
  padding: 12px;
  background: #f8f9fb;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.detail-item {
  margin-bottom: 8px;
}

.detail-item:last-child {
  margin-bottom: 0;
}

.detail-label {
  font-size: 12px;
  color: #666;
  font-weight: 500;
  display: block;
  margin-bottom: 4px;
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.voice-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 12px;
  min-height: 20px;
}

.voice-stats {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

.voice-stats span {
  display: flex;
  align-items: center;
  gap: 4px;
}

@media (max-width: 1200px) {
  .voice-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }
}

@media (max-width: 768px) {
  .main-content {
    flex-direction: column;
    height: auto;
  }

  .editor-panel {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #e4e7ed;
  }

  .voice-grid {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 16px;
  }

  .library-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
}

/* Element Plus 样式覆盖 */
:deep(.el-form-item__label) {
  color: #606266;
  font-weight: 500;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

:deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
}

:deep(.el-slider__runway) {
  background-color: #e4e7ed;
}

:deep(.el-slider__bar) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

:deep(.el-slider__button) {
  border-color: #667eea;
}

:deep(.el-tag) {
  border-radius: 12px;
}
</style>