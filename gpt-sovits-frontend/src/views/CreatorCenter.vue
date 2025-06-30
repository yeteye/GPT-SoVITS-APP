<!-- ./gpt-sovits-frontend/src/views/CreatorCenter.vue - 增强版 -->
<template>
  <div class="creator-center">
    <div class="creator-header">
      <div class="creator-info">
        <h2>创作者中心</h2>
        <p>欢迎上传和管理你的音频与音色模型，构建你的专属声音品牌。</p>
      </div>
      <div class="creator-stats">
        <div class="stat-card">
          <div class="stat-number">{{ audioList.length }}</div>
          <div class="stat-label">音频样本</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{{ modelList.length }}</div>
          <div class="stat-label">音色模型</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{{ approvedModels }}</div>
          <div class="stat-label">已通过审核</div>
        </div>
      </div>
    </div>

    <!-- 上传入口 -->
    <div class="upload-actions">
      <el-button type="primary" size="large" @click="showUploadAudioDialog">
        <el-icon>
          <Upload />
        </el-icon>
        上传音频
      </el-button>
      <el-button type="success" size="large" @click="showUploadModelDialog">
        <el-icon>
          <Upload />
        </el-icon>
        上传音色模型
      </el-button>
    </div>

    <el-row :gutter="24">
      <el-col :lg="12" :md="24" :sm="24">
        <!-- 我的音频 -->
        <section class="content-section">
          <div class="section-header">
            <h3>🎵 我的音频</h3>
            <el-button @click="fetchAudioSamples" :loading="audioLoading" size="small">
              <el-icon>
                <Refresh />
              </el-icon>
              刷新
            </el-button>
          </div>

          <div class="audio-grid" v-loading="audioLoading">
            <div v-for="audio in audioList" :key="audio.id" class="audio-card">
              <div class="audio-cover">
                <div class="audio-icon">
                  <el-icon size="32">
                    <Microphone />
                  </el-icon>
                </div>
                <div class="audio-overlay">
                  <el-button type="primary" circle @click="playAudio(audio)"
                    :class="{ 'playing': currentPlayingAudio === audio.id }">
                    <el-icon>
                      <component :is="currentPlayingAudio === audio.id ? 'VideoPause' : 'VideoPlay'" />
                    </el-icon>
                  </el-button>
                </div>
              </div>
              <div class="audio-info">
                <div class="audio-name">{{ audio.filename }}</div>
                <div class="audio-meta">
                  <span>{{ formatDuration(audio.file_metadata?.duration) }}</span>
                  <span>{{ formatTime(audio.created_at) }}</span>
                </div>
                <div class="audio-actions">
                  <el-button type="text" size="small" @click="downloadAudio(audio)">
                    <el-icon>
                      <Download />
                    </el-icon>
                    下载
                  </el-button>
                  <el-button type="text" size="small" @click="deleteAudio(audio)" style="color: #f56c6c;">
                    <el-icon>
                      <Delete />
                    </el-icon>
                    删除
                  </el-button>
                </div>
              </div>
            </div>
          </div>

          <el-empty v-if="!audioLoading && audioList.length === 0" description="暂无音频文件">
            <el-button type="primary" @click="showUploadAudioDialog">上传第一个音频</el-button>
          </el-empty>
        </section>
      </el-col>

      <el-col :lg="12" :md="24" :sm="24">
        <!-- 我的音色模型 -->
        <section class="content-section">
          <div class="section-header">
            <h3>🧬 我的音色模型</h3>
            <el-button @click="fetchMyModels" :loading="modelsLoading" size="small">
              <el-icon>
                <Refresh />
              </el-icon>
              刷新
            </el-button>
          </div>

          <div class="model-list" v-loading="modelsLoading">
            <div v-for="model in modelList" :key="model.id" class="model-card" @click="viewModelDetail(model)">
              <div class="model-header">
                <div class="model-avatar">
                  <img :src="model.avatar_url || defaultModelAvatar" :alt="model.name" />
                </div>
                <div class="model-basic-info">
                  <div class="model-name">{{ model.name }}</div>
                  <div class="model-id">ID: {{ model.id }}</div>
                </div>
                <div class="model-status">
                  <el-tag :type="getStatusType(model.review_status)" size="small">
                    {{ getStatusText(model.review_status) }}
                  </el-tag>
                  <el-tag :type="model.is_public ? 'success' : 'info'" size="small">
                    {{ model.is_public ? '公开' : '私有' }}
                  </el-tag>
                </div>
              </div>

              <div class="model-description">
                {{ model.description || '暂无描述' }}
              </div>

              <div class="model-details">
                <div class="detail-row">
                  <div class="detail-item">
                    <span class="detail-label">支持语言：</span>
                    <div class="detail-tags">
                      <el-tag v-for="lang in model.supported_languages" :key="lang" size="small" type="primary"
                        effect="plain">
                        {{ getLanguageDisplay(lang) }}
                      </el-tag>
                    </div>
                  </div>
                </div>
                <div class="detail-row">
                  <div class="detail-item">
                    <span class="detail-label">支持情感：</span>
                    <div class="detail-tags">
                      <el-tag v-for="emotion in model.supported_emotions" :key="emotion" size="small" type="success"
                        effect="plain">
                        {{ getEmotionDisplay(emotion) }}
                      </el-tag>
                    </div>
                  </div>
                </div>
              </div>

              <div class="model-meta">
                <div class="meta-item">
                  <span class="meta-label">创建时间：</span>
                  <span class="meta-value">{{ formatTime(model.created_at) }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-label">最近使用：</span>
                  <span class="meta-value">{{ formatTime(model.last_used_at) || '未使用' }}</span>
                </div>
              </div>

              <div class="model-actions" @click.stop>
                <el-button type="text" size="small" @click="viewModelDetail(model)">
                  <el-icon>
                    <View />
                  </el-icon>
                  查看详情
                </el-button>
                <el-button type="text" size="small" @click="togglePublic(model)">
                  <el-icon>
                    <Switch />
                  </el-icon>
                  {{ model.is_public ? '设为私有' : '设为公开' }}
                </el-button>
                <el-button type="text" size="small" @click="editModel(model)">
                  <el-icon>
                    <Edit />
                  </el-icon>
                  编辑
                </el-button>
                <el-button type="text" size="small" @click="deleteModel(model)" style="color: #f56c6c;">
                  <el-icon>
                    <Delete />
                  </el-icon>
                  删除
                </el-button>
              </div>
            </div>
          </div>

          <el-empty v-if="!modelsLoading && modelList.length === 0" description="暂无音色模型">
            <el-button type="primary" @click="showUploadModelDialog">上传第一个模型</el-button>
          </el-empty>
        </section>
      </el-col>
    </el-row>

    <!-- 上传音频弹窗 -->
    <el-dialog v-model="uploadAudioVisible" title="上传音频" width="600px">
      <el-upload ref="audioUploadRef" class="upload-demo" drag :action="uploadAudioAction" :headers="uploadHeaders"
        :on-success="handleAudioUploadSuccess" :on-error="handleUploadError" :before-upload="beforeAudioUpload"
        accept="audio/*" :limit="1" :file-list="audioFileList" :auto-upload="false">
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">拖拽音频文件到此处，或<em>点击上传</em></div>
        <div class="el-upload__tip">支持 WAV、MP3、M4A 等格式，文件大小不超过50MB</div>
      </el-upload>

      <template #footer>
        <el-button @click="uploadAudioVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAudioUpload" :loading="uploadingAudio">
          确认上传
        </el-button>
      </template>
    </el-dialog>

    <!-- 上传模型弹窗 -->
    <el-dialog v-model="uploadModelVisible" title="上传音色模型" width="700px">
      <el-form :model="modelForm" :rules="modelRules" ref="modelFormRef" label-width="120px">
        <el-form-item label="模型名称" prop="model_name">
          <el-input v-model="modelForm.model_name" placeholder="请输入模型名称" />
        </el-form-item>

        <el-form-item label="模型描述" prop="description">
          <el-input v-model="modelForm.description" type="textarea" :rows="3" placeholder="请描述模型特点..." maxlength="200"
            show-word-limit />
        </el-form-item>

        <el-form-item label="GPT模型文件" prop="gpt_model_file">
          <el-upload ref="gptUploadRef" :auto-upload="false" :limit="1" accept=".pth" :on-change="handleGptFileChange"
            :file-list="gptFileList">
            <el-button>选择GPT模型文件(.pth)</el-button>
          </el-upload>
        </el-form-item>

        <el-form-item label="SoVITS模型文件" prop="sovits_model_file">
          <el-upload ref="sovitsUploadRef" :auto-upload="false" :limit="1" accept=".ckpt"
            :on-change="handleSovitsFileChange" :file-list="sovitsFileList">
            <el-button>选择SoVITS模型文件(.ckpt)</el-button>
          </el-upload>
        </el-form-item>

        <el-form-item label="支持语言" prop="supported_languages">
          <el-select v-model="modelForm.supported_languages" multiple placeholder="选择支持的语言">
            <el-option label="中文" value="zh" />
            <el-option label="英文" value="en" />
            <el-option label="日语" value="ja" />
          </el-select>
        </el-form-item>

        <el-form-item label="支持情感" prop="supported_emotions">
          <el-select v-model="modelForm.supported_emotions" multiple placeholder="选择支持的情感">
            <el-option label="自然" value="neutral" />
            <el-option label="快乐" value="happy" />
            <el-option label="悲伤" value="sad" />
            <el-option label="愤怒" value="angry" />
            <el-option label="惊讶" value="surprised" />
            <el-option label="厌恶" value="disgusted" />
            <el-option label="害怕" value="fearful" />
            <el-option label="平静" value="calm" />
            <el-option label="兴奋" value="excited" />
            <el-option label="自信" value="confident" />
            <el-option label="温和" value="gentle" />
            <el-option label="愉快" value="cheerful" />
            <el-option label="忧郁" value="melancholy" />
            <el-option label="精力充沛" value="energetic" />
            <el-option label="平和" value="peaceful" />
            <el-option label="热情" value="passionate" />
            <el-option label="严肃" value="serious" />
            <el-option label="顽皮" value="playful" />
            <el-option label="浪漫" value="romantic" />
            <el-option label="神秘" value="mysterious" />
          </el-select>
        </el-form-item>

        <el-form-item label="是否公开">
          <el-switch v-model="modelForm.is_public" active-text="公开" inactive-text="私有" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="uploadModelVisible = false">取消</el-button>
        <el-button type="primary" @click="submitModelUpload" :loading="uploadingModel">
          确认上传
        </el-button>
      </template>
    </el-dialog>

    <!-- 模型详情弹窗 -->
    <el-dialog v-model="modelDetailVisible" :title="selectedModel?.name" width="800px">
      <div v-if="selectedModel" class="model-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="模型ID">
            {{ selectedModel.id }}
          </el-descriptions-item>
          <el-descriptions-item label="模型名称">
            {{ selectedModel.name }}
          </el-descriptions-item>
          <el-descriptions-item label="审核状态">
            <el-tag :type="getStatusType(selectedModel.review_status)">
              {{ getStatusText(selectedModel.review_status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="公开状态">
            <el-tag :type="selectedModel.is_public ? 'success' : 'info'">
              {{ selectedModel.is_public ? '公开' : '私有' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatTime(selectedModel.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="最近使用">
            {{ formatTime(selectedModel.last_used_at) || '未使用' }}
          </el-descriptions-item>
          <el-descriptions-item label="使用次数">
            {{ selectedModel.usage_count || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="质量评分">
            {{ selectedModel.quality_score || 'N/A' }}
          </el-descriptions-item>
          <el-descriptions-item label="模型描述" :span="2">
            {{ selectedModel.description || '暂无描述' }}
          </el-descriptions-item>
          <el-descriptions-item label="支持语言" :span="2">
            <el-tag v-for="lang in selectedModel.supported_languages" :key="lang" style="margin-right: 8px"
              type="primary">
              {{ getLanguageDisplay(lang) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="支持情感" :span="2">
            <el-tag v-for="emotion in selectedModel.supported_emotions" :key="emotion" style="margin-right: 8px"
              type="success">
              {{ getEmotionDisplay(emotion) }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <template #footer>
        <el-button @click="modelDetailVisible = false">关闭</el-button>
        <el-button type="primary" @click="useModelInTTS(selectedModel)">
          使用此模型
        </el-button>
      </template>
    </el-dialog>

    <!-- 模型编辑弹窗 -->
    <el-dialog v-model="editModelVisible" title="编辑模型" width="600px">
      <el-form :model="editForm" :rules="editRules" ref="editFormRef" label-width="120px">
        <el-form-item label="模型名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入模型名称" />
        </el-form-item>

        <el-form-item label="模型描述" prop="description">
          <el-input v-model="editForm.description" type="textarea" :rows="3" placeholder="请描述模型特点..." maxlength="200"
            show-word-limit />
        </el-form-item>

        <el-form-item label="支持语言" prop="supported_languages">
          <el-select v-model="editForm.supported_languages" multiple placeholder="选择支持的语言">
            <el-option label="中文" value="zh" />
            <el-option label="英文" value="en" />
            <el-option label="日语" value="ja" />
          </el-select>
        </el-form-item>

        <el-form-item label="支持情感" prop="supported_emotions">
          <el-select v-model="editForm.supported_emotions" multiple placeholder="选择支持的情感">
            <el-option label="自然" value="neutral" />
            <el-option label="快乐" value="happy" />
            <el-option label="悲伤" value="sad" />
            <el-option label="愤怒" value="angry" />
            <el-option label="惊讶" value="surprised" />
            <el-option label="厌恶" value="disgusted" />
            <el-option label="害怕" value="fearful" />
            <el-option label="平静" value="calm" />
            <el-option label="兴奋" value="excited" />
            <el-option label="自信" value="confident" />
            <el-option label="温和" value="gentle" />
            <el-option label="愉快" value="cheerful" />
            <el-option label="忧郁" value="melancholy" />
            <el-option label="精力充沛" value="energetic" />
            <el-option label="平和" value="peaceful" />
            <el-option label="热情" value="passionate" />
            <el-option label="严肃" value="serious" />
            <el-option label="顽皮" value="playful" />
            <el-option label="浪漫" value="romantic" />
            <el-option label="神秘" value="mysterious" />
          </el-select>
        </el-form-item>

        <el-form-item label="是否公开">
          <el-switch v-model="editForm.is_public" active-text="公开" inactive-text="私有" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="editModelVisible = false">取消</el-button>
        <el-button type="primary" @click="submitModelEdit" :loading="editingModel">
          保存修改
        </el-button>
      </template>
    </el-dialog>

    <!-- 音频预览播放器 -->
    <audio ref="audioPlayer" style="display: none" @ended="onAudioEnded" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Upload,
  Refresh,
  VideoPlay,
  VideoPause,
  Delete,
  View,
  Switch,
  Edit,
  Download,
  Microphone,
  UploadFilled
} from '@element-plus/icons-vue'
import { userAPI, voiceCloneAPI, modelsAPI } from '@/api'

const router = useRouter()

// 响应式数据
const audioList = ref([])
const modelList = ref([])
const audioLoading = ref(false)
const modelsLoading = ref(false)
const uploadAudioVisible = ref(false)
const uploadModelVisible = ref(false)
const modelDetailVisible = ref(false)
const editModelVisible = ref(false)
const uploadingAudio = ref(false)
const uploadingModel = ref(false)
const editingModel = ref(false)
const audioFileList = ref([])
const gptFileList = ref([])
const sovitsFileList = ref([])
const currentPlayingAudio = ref(null)
const selectedModel = ref(null)
const editingModelData = ref(null)

// refs
const audioUploadRef = ref()
const gptUploadRef = ref()
const sovitsUploadRef = ref()
const modelFormRef = ref()
const editFormRef = ref()
const audioPlayer = ref()

// 计算属性
const approvedModels = computed(() => {
  return modelList.value.filter(model => model.review_status === 'approved').length
})

// 表单数据
const modelForm = reactive({
  model_name: '',
  description: '',
  gpt_model_file: null,
  sovits_model_file: null,
  supported_languages: [],
  supported_emotions: [],
  is_public: false
})

const editForm = reactive({
  name: '',
  description: '',
  supported_languages: [],
  supported_emotions: [],
  is_public: false
})

// 验证规则
const modelRules = {
  model_name: [
    { required: true, message: '请输入模型名称', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入模型描述', trigger: 'blur' }
  ],
  gpt_model_file: [
    { required: true, message: '请选择GPT模型文件', trigger: 'change' }
  ],
  sovits_model_file: [
    { required: true, message: '请选择SoVITS模型文件', trigger: 'change' }
  ],
  supported_languages: [
    { required: true, message: '请选择支持的语言', trigger: 'change' }
  ],
  supported_emotions: [
    { required: true, message: '请选择支持的情感', trigger: 'change' }
  ]
}

const editRules = {
  name: [
    { required: true, message: '请输入模型名称', trigger: 'blur' }
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
const uploadAudioAction = import.meta.env.VITE_API_BASE_URL + '/voice-clone/upload-sample'
const uploadHeaders = {
  'Authorization': `Bearer ${localStorage.getItem('token')}`
}

const defaultModelAvatar = new URL('@/assets/model.png', import.meta.url).href

// 语言和情感显示转换
function getLanguageDisplay(lang) {
  const langMap = {
    'zh': '中文',
    'en': '英文',
    'ja': '日语'
  }
  return langMap[lang] || lang
}

function getEmotionDisplay(emotion) {
  const emotionMap = {
    'neutral': '自然',
    'happy': '快乐',
    'sad': '悲伤',
    'angry': '愤怒',
    'surprised': '惊讶',
    'disgusted': '厌恶',
    'fearful': '害怕',
    'calm': '平静',
    'excited': '兴奋',
    'confident': '自信',
    'gentle': '温和',
    'cheerful': '愉快',
    'melancholy': '忧郁',
    'energetic': '精力充沛',
    'peaceful': '平和',
    'passionate': '热情',
    'serious': '严肃',
    'playful': '顽皮',
    'romantic': '浪漫',
    'mysterious': '神秘'
  }
  return emotionMap[emotion] || emotion
}

// 获取音频样本列表
async function fetchAudioSamples() {
  audioLoading.value = true
  try {
    const res = await userAPI.getUserUploads({ type: 'audio', per_page: 50 })
    audioList.value = res.data?.uploads || []
  } catch (error) {
    console.error('获取音频列表失败:', error)
    ElMessage.error('获取音频列表失败')
  } finally {
    audioLoading.value = false
  }
}

// 获取我的模型列表
async function fetchMyModels() {
  modelsLoading.value = true
  try {
    const res = await modelsAPI.getMyModels({ per_page: 50 })
    modelList.value = res.data?.models || []
  } catch (error) {
    console.error('获取模型列表失败:', error)
    ElMessage.error('获取模型列表失败')
  } finally {
    modelsLoading.value = false
  }
}

// 显示上传音频弹窗
function showUploadAudioDialog() {
  uploadAudioVisible.value = true
  audioFileList.value = []
}

// 显示上传模型弹窗
function showUploadModelDialog() {
  uploadModelVisible.value = true
  resetModelForm()
}

// 重置模型表单
function resetModelForm() {
  Object.assign(modelForm, {
    model_name: '',
    description: '',
    gpt_model_file: null,
    sovits_model_file: null,
    supported_languages: [],
    supported_emotions: [],
    is_public: false
  })
  gptFileList.value = []
  sovitsFileList.value = []
}

// 音频上传前验证
function beforeAudioUpload(file) {
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

// 音频上传成功
function handleAudioUploadSuccess(response, file) {
  if (response.success) {
    ElMessage.success('音频上传成功')
    uploadAudioVisible.value = false
    fetchAudioSamples()
  } else {
    ElMessage.error('音频上传失败: ' + response.message)
  }
  uploadingAudio.value = false
}

// 上传错误处理
function handleUploadError(error, file) {
  console.error('Upload error:', error)
  ElMessage.error('上传失败: ' + error.message)
  uploadingAudio.value = false
}

// 提交音频上传
function submitAudioUpload() {
  if (audioFileList.value.length === 0) {
    ElMessage.warning('请先选择音频文件')
    return
  }

  uploadingAudio.value = true
  audioUploadRef.value.submit()
}

// 处理GPT文件选择
function handleGptFileChange(file) {
  modelForm.gpt_model_file = file.raw
  gptFileList.value = [file]
}

// 处理SoVITS文件选择
function handleSovitsFileChange(file) {
  modelForm.sovits_model_file = file.raw
  sovitsFileList.value = [file]
}

// 提交模型上传
async function submitModelUpload() {
  if (!modelFormRef.value) return

  modelFormRef.value.validate(async (valid) => {
    if (!valid) return

    uploadingModel.value = true
    try {
      const formData = new FormData()
      formData.append('model_name', modelForm.model_name)
      formData.append('description', modelForm.description)
      formData.append('gpt_model_file', modelForm.gpt_model_file)
      formData.append('sovits_model_file', modelForm.sovits_model_file)

      // 逐个添加数组元素
      modelForm.supported_languages.forEach(lang => {
        formData.append('supported_languages', lang)
      })

      modelForm.supported_emotions.forEach(emotion => {
        formData.append('supported_emotions', emotion)
      })

      formData.append('is_public', modelForm.is_public)

      const res = await voiceCloneAPI.uploadModel(formData)

      ElMessage.success('模型上传成功，等待审核')
      uploadModelVisible.value = false
      fetchMyModels()
    } catch (error) {
      console.error('Model upload error:', error)
      ElMessage.error('模型上传失败: ' + (error?.response?.data?.message || '未知错误'))
    } finally {
      uploadingModel.value = false
    }
  })
}


// 播放音频
function playAudio(audio) {
  if (currentPlayingAudio.value === audio.id) {
    // 停止播放
    audioPlayer.value.pause()
    currentPlayingAudio.value = null
  } else {
    // 开始播放
    if (audio.file_url) {
      audioPlayer.value.src = audio.file_url
      audioPlayer.value.play()
      currentPlayingAudio.value = audio.id
    } else {
      ElMessage.warning('音频文件不可用')
    }
  }
}

function onAudioEnded() {
  currentPlayingAudio.value = null
}

// 下载音频
async function downloadAudio(audio) {
  try {
    if (audio.file_url) {
      const link = document.createElement('a')
      link.href = audio.file_url
      link.download = audio.filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      ElMessage.success('下载开始')
    } else {
      ElMessage.error('音频文件不可用')
    }
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

// 删除音频
async function deleteAudio(audio) {
  try {
    await ElMessageBox.confirm(`确定要删除 "${audio.filename}" 吗？`, '确认删除', {
      type: 'warning'
    })

    await userAPI.deleteUpload(audio.id)
    ElMessage.success('音频删除成功')
    fetchAudioSamples()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 查看模型详情
function viewModelDetail(model) {
  selectedModel.value = model
  modelDetailVisible.value = true
}

// 编辑模型
function editModel(model) {
  editingModelData.value = model
  Object.assign(editForm, {
    name: model.name,
    description: model.description,
    supported_languages: [...(model.supported_languages || [])],
    supported_emotions: [...(model.supported_emotions || [])],
    is_public: model.is_public
  })
  editModelVisible.value = true
}

// 提交模型编辑
async function submitModelEdit() {
  if (!editFormRef.value) return

  editFormRef.value.validate(async (valid) => {
    if (!valid) return

    editingModel.value = true
    try {
      await modelsAPI.updateModel(editingModelData.value.id, {
        name: editForm.name,
        description: editForm.description,
        supported_languages: editForm.supported_languages,
        supported_emotions: editForm.supported_emotions,
        is_public: editForm.is_public
      })

      ElMessage.success('模型更新成功')
      editModelVisible.value = false
      fetchMyModels()
    } catch (error) {
      console.error('Model update error:', error)
      ElMessage.error('模型更新失败: ' + (error?.response?.data?.message || '未知错误'))
    } finally {
      editingModel.value = false
    }
  })
}

// 切换模型公开状态
async function togglePublic(model) {
  try {
    await modelsAPI.toggleModelPublic(model.id)
    ElMessage.success(`模型已设为${model.is_public ? '私有' : '公开'}`)
    fetchMyModels()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 删除模型
async function deleteModel(model) {
  try {
    await ElMessageBox.confirm(`确定要删除模型 "${model.name}" 吗？`, '确认删除', {
      type: 'warning'
    })

    await modelsAPI.deleteModel(model.id)
    ElMessage.success('模型删除成功')
    fetchMyModels()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 使用模型进行TTS
function useModelInTTS(model) {
  router.push({
    name: 'TTSPlayground',
    query: { model_id: model.id }
  })
}

// 工具函数
function getStatusText(status) {
  const statusMap = {
    'pending': '待审核',
    'approved': '已通过',
    'rejected': '已驳回'
  }
  return statusMap[status] || status
}

function getStatusType(status) {
  const typeMap = {
    'pending': 'warning',
    'approved': 'success',
    'rejected': 'danger'
  }
  return typeMap[status] || ''
}

function formatTime(timeStr) {
  if (!timeStr) return ''
  return new Date(timeStr).toLocaleString()
}

function formatDuration(seconds) {
  if (!seconds) return '0s'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return mins > 0 ? `${mins}m${secs}s` : `${secs}s`
}

onMounted(() => {
  fetchAudioSamples()
  fetchMyModels()
})
</script>

<style lang="scss" scoped>
.creator-center {
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

.creator-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 32px;
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.creator-info h2 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.creator-info p {
  margin: 8px 0 0 0;
  color: #666;
  font-size: 16px;
  line-height: 1.5;
}

.creator-stats {
  display: flex;
  gap: 24px;
}

.stat-card {
  text-align: center;
  padding: 16px 24px;
  background: linear-gradient(135deg, #f8f9fb 0%, #e8f4f8 100%);
  border-radius: 12px;
  border: 1px solid #e4e7ed;
}

.stat-number {
  font-size: 24px;
  font-weight: 700;
  color: #333;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #666;
}

.upload-actions {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  justify-content: center;
}

.upload-actions .el-button {
  padding: 12px 24px;
  border-radius: 20px;
  font-weight: 600;
}

.content-section {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border-radius: 16px;
  height: fit-content;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #f0f0f0;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.audio-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.audio-card {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.audio-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.audio-cover {
  position: relative;
  height: 120px;
  background: linear-gradient(135deg, #f8f9fb 0%, #e8f4f8 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.audio-icon {
  color: #c0c4cc;
}

.audio-overlay {
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

.audio-card:hover .audio-overlay {
  opacity: 1;
}

.audio-overlay .el-button.playing {
  background: #67c23a;
  border-color: #67c23a;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }

  50% {
    transform: scale(1.1);
  }

  100% {
    transform: scale(1);
  }
}

.audio-info {
  padding: 16px;
}

.audio-name {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.audio-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
  margin-bottom: 12px;
}

.audio-actions {
  display: flex;
  gap: 8px;
}

.model-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.model-card {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.model-card:hover {
  border-color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.15);
}

.model-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.model-avatar {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  overflow: hidden;
}

.model-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.model-basic-info {
  flex: 1;
}

.model-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.model-id {
  font-size: 12px;
  color: #999;
}

.model-status {
  display: flex;
  gap: 8px;
}

.model-description {
  font-size: 14px;
  color: #666;
  line-height: 1.5;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.model-details {
  margin-bottom: 12px;
}

.detail-row {
  margin-bottom: 8px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-label {
  font-size: 12px;
  color: #999;
  min-width: 60px;
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.model-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.meta-item {
  font-size: 12px;
}

.meta-label {
  color: #999;
}

.meta-value {
  color: #333;
  font-weight: 500;
}

.model-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.model-detail {
  padding: 16px 0;
}

// 响应式设计
@media (max-width: 768px) {
  .creator-center {
    padding: 16px;
  }

  .creator-header {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }

  .creator-stats {
    gap: 16px;
  }

  .upload-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .audio-grid {
    grid-template-columns: 1fr;
  }

  .model-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .model-meta {
    flex-direction: column;
    gap: 4px;
  }

  .model-actions {
    justify-content: center;
  }
}

// Element Plus 样式覆盖
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

:deep(.el-dialog) {
  border-radius: 16px;
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
</style>