<!-- ./gpt-sovits-frontend/src/views/CreatorCenter.vue - 修复版 -->
<template>
  <div class="creator-center">
    <div class="creator-header">
      <div class="creator-info">
        <h2>创作者中心</h2>
        <p>欢迎上传和管理你的音频与音色模型，构建你的专属声音品牌。</p>
      </div>
    </div>

    <!-- 上传入口 -->
    <div class="upload-actions">
      <el-button type="primary" @click="showUploadAudioDialog">
        <el-icon>
          <Upload />
        </el-icon>
        上传音频
      </el-button>
      <el-button type="success" @click="showUploadModelDialog">
        <el-icon>
          <Upload />
        </el-icon>
        上传音色模型
      </el-button>
    </div>

    <!-- 我的音频 -->
    <section class="content-section">
      <div class="section-header">
        <h3>🎵 我的音频</h3>
        <el-button @click="fetchAudioSamples" :loading="audioLoading">
          <el-icon>
            <Refresh />
          </el-icon>
          刷新
        </el-button>
      </div>
      <el-table :data="audioList" style="width: 100%" v-loading="audioLoading">
        <el-table-column prop="filename" label="音频名称" />
        <el-table-column label="时长" width="100">
          <template #default="{ row }">
            {{ formatDuration(row.file_metadata?.duration) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button type="text" @click="previewAudio(row)" size="small">
              <el-icon>
                <VideoPlay />
              </el-icon>
              播放
            </el-button>
            <el-button type="text" @click="deleteAudio(row)" size="small" style="color: #f56c6c;">
              <el-icon>
                <Delete />
              </el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!audioLoading && audioList.length === 0" description="暂无音频文件" />
    </section>

    <!-- 我的音色模型 -->
    <section class="content-section">
      <div class="section-header">
        <h3>🧬 我的音色模型</h3>
        <el-button @click="fetchMyModels" :loading="modelsLoading">
          <el-icon>
            <Refresh />
          </el-icon>
          刷新
        </el-button>
      </div>
      <el-table :data="modelList" style="width: 100%" v-loading="modelsLoading">
        <el-table-column prop="name" label="模型名称" />
        <el-table-column label="审核状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.review_status)">
              {{ getStatusText(row.review_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="公开状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_public ? 'success' : 'info'">
              {{ row.is_public ? '公开' : '私有' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button type="text" @click="viewModel(row)" size="small">
              <el-icon>
                <View />
              </el-icon>
              查看
            </el-button>
            <el-button type="text" @click="togglePublic(row)" size="small">
              <el-icon>
                <Switch />
              </el-icon>
              {{ row.is_public ? '设为私有' : '设为公开' }}
            </el-button>
            <el-button type="text" @click="deleteModel(row)" size="small" style="color: #f56c6c;">
              <el-icon>
                <Delete />
              </el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!modelsLoading && modelList.length === 0" description="暂无音色模型" />
    </section>

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
            <el-option label="中文" value="zh-CN" />
            <el-option label="英文" value="en-US" />
            <el-option label="日语" value="ja-JP" />
          </el-select>
        </el-form-item>

        <el-form-item label="支持情感" prop="supported_emotions">
          <el-select v-model="modelForm.supported_emotions" multiple placeholder="选择支持的情感">
            <el-option label="自然" value="neutral" />
            <el-option label="快乐" value="happy" />
            <el-option label="悲伤" value="sad" />
            <el-option label="愤怒" value="angry" />
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

    <!-- 音频预览 -->
    <audio ref="audioPlayer" style="display: none" @ended="onAudioEnded" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Upload,
  Refresh,
  VideoPlay,
  Delete,
  View,
  Switch,
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
const uploadingAudio = ref(false)
const uploadingModel = ref(false)
const audioFileList = ref([])
const gptFileList = ref([])
const sovitsFileList = ref([])
const currentPlayingAudio = ref(null)

// refs
const audioUploadRef = ref()
const gptUploadRef = ref()
const sovitsUploadRef = ref()
const modelFormRef = ref()

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

// 上传配置
const uploadAudioAction = import.meta.env.VITE_API_BASE_URL + '/voice-clone/upload-sample'
const uploadHeaders = {
  'Authorization': `Bearer ${localStorage.getItem('token')}`
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
}

// 上传错误处理
function handleUploadError(error, file) {
  console.error('Upload error:', error)
  ElMessage.error('上传失败: ' + error.message)
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
      formData.append('supported_languages', JSON.stringify(modelForm.supported_languages))
      formData.append('supported_emotions', JSON.stringify(modelForm.supported_emotions))
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
function previewAudio(audio) {
  if (currentPlayingAudio.value === audio.id) {
    audioPlayer.value.pause()
    currentPlayingAudio.value = null
  } else {
    // 这里需要根据实际API获取音频播放URL
    ElMessage.info('音频播放功能开发中')
    // audioPlayer.value.src = audio.file_url
    // audioPlayer.value.play()
    // currentPlayingAudio.value = audio.id
  }
}

function onAudioEnded() {
  currentPlayingAudio.value = null
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
function viewModel(model) {
  router.push({ name: 'Model', params: { id: model.id } })
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
  padding: 40px;
  background: #f9fafc;
  min-height: 100vh;
}

.creator-header {
  display: flex;
  align-items: center;
  margin-bottom: 30px;
}

.creator-info h2 {
  margin: 0;
  font-size: 26px;
  font-weight: bold;
  color: #333;
}

.creator-info p {
  margin: 8px 0 0 0;
  color: #666;
  font-size: 16px;
}

.upload-actions {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.content-section {
  background: #fff;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-radius: 12px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

// Element Plus 样式覆盖
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

:deep(.el-dialog) {
  border-radius: 16px;
}

:deep(.el-table) {
  border-radius: 8px;
  overflow: hidden;
}
</style>