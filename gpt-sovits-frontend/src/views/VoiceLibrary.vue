<!-- ./gpt-sovits-frontend/src/views/VoiceLibrary.vue - 修复版 -->
<template>
  <div class="voice-library">
    <div class="page-header">
      <h2 class="title">🎧 音色库</h2>
      <p class="subtitle">浏览和试听公开的音色模型</p>
    </div>

    <!-- 搜索与标签过滤 -->
    <div class="filter-bar">
      <div class="search-section">
        <el-input v-model="searchText" placeholder="搜索音色名称..." clearable class="search-input" @input="onSearch">
          <template #prefix>
            <el-icon>
              <Search />
            </el-icon>
          </template>
        </el-input>
        <el-select v-model="selectedTag" placeholder="选择标签" clearable class="tag-select" @change="onTagChange">
          <el-option v-for="tag in allTags" :key="tag" :label="tag" :value="tag" />
        </el-select>
        <el-select v-model="selectedType" placeholder="模型类型" clearable class="type-select" @change="onTypeChange">
          <el-option label="官方模型" value="official" />
          <el-option label="用户模型" value="user" />
        </el-select>
      </div>

      <div class="view-controls">
        <el-button-group>
          <el-button :type="viewMode === 'grid' ? 'primary' : ''" @click="viewMode = 'grid'" size="small">
            <el-icon>
              <Grid />
            </el-icon>
            网格
          </el-button>
          <el-button :type="viewMode === 'list' ? 'primary' : ''" @click="viewMode = 'list'" size="small">
            <el-icon>
              <List />
            </el-icon>
            列表
          </el-button>
        </el-button-group>
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="stats-bar">
      <span>共找到 {{ filteredVoices.length }} 个音色</span>
      <el-button v-if="isLoggedIn" type="primary" size="small" @click="goToMyVoices">
        查看我的音色
      </el-button>
    </div>

    <!-- 网格视图 -->
    <div v-if="viewMode === 'grid'" class="voice-card-list" v-loading="loading">
      <div v-for="voice in paginatedVoices" :key="voice.id" class="voice-card" @click="selectVoice(voice)"
        :class="{ 'selected': selectedVoice?.id === voice.id }">
        <div class="voice-avatar">
          <img :src="voice.avatar || defaultAvatar" :alt="voice.name" />
          <div class="voice-overlay">
            <el-button type="primary" size="small" circle @click.stop="previewVoice(voice)">
              <el-icon>
                <VideoPlay />
              </el-icon>
            </el-button>
          </div>
          <div class="voice-type-badge">
            <el-tag :type="voice.model_type === 'official' ? 'warning' : 'info'" size="small">
              {{ voice.model_type === 'official' ? '官方' : '用户' }}
            </el-tag>
          </div>
        </div>

        <div class="voice-info">
          <div class="voice-name">{{ voice.name }}</div>
          <div class="voice-desc">{{ voice.description }}</div>

          <!-- 重要信息显示 -->
          <div class="voice-details">
            <div class="detail-section">
              <div class="detail-label">支持语言</div>
              <div class="detail-content">
                <el-tag v-for="lang in voice.supported_languages" :key="lang" size="small" type="primary"
                  effect="plain">
                  {{ getLanguageDisplay(lang) }}
                </el-tag>
              </div>
            </div>
            <div class="detail-section">
              <div class="detail-label">支持情感</div>
              <div class="detail-content">
                <el-tag v-for="emotion in voice.supported_emotions" :key="emotion" size="small" type="success"
                  effect="plain">
                  {{ getEmotionDisplay(emotion) }}
                </el-tag>
              </div>
            </div>
          </div>

          <div class="voice-tags">
            <el-tag v-for="tag in voice.tags" :key="tag" size="small" type="info" effect="plain">
              {{ tag }}
            </el-tag>
          </div>
          <div class="voice-stats">
            <span class="rating">
              <el-icon>
                <Star />
              </el-icon>
              {{ voice.rating || 5.0 }}
            </span>
            <span class="usage">
              <el-icon>
                <Microphone />
              </el-icon>
              {{ voice.usage_count || 0 }}
            </span>
          </div>
          <div class="voice-actions">
            <el-button type="primary" size="small" @click.stop="useTTS(voice)" :disabled="!isLoggedIn">
              {{ isLoggedIn ? '使用TTS' : '登录后使用' }}
            </el-button>
            <el-button v-if="isLoggedIn" size="small" @click.stop="toggleFavorite(voice)"
              :type="voice.is_favorited ? 'danger' : ''">
              <el-icon>
                <component :is="voice.is_favorited ? 'StarFilled' : 'Star'" />
              </el-icon>
              {{ voice.is_favorited ? '取消收藏' : '收藏' }}
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 列表视图 -->
    <div v-else class="voice-table-container" v-loading="loading">
      <el-table :data="paginatedVoices" style="width: 100%">
        <el-table-column width="80">
          <template #default="{ row }">
            <el-avatar :size="50" :src="row.avatar || defaultAvatar" />
          </template>
        </el-table-column>

        <el-table-column prop="name" label="名称" min-width="150" />

        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />

        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.model_type === 'official' ? 'warning' : 'info'" size="small">
              {{ row.model_type === 'official' ? '官方' : '用户' }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 新增：支持语言列 -->
        <el-table-column label="支持语言" min-width="120">
          <template #default="{ row }">
            <el-tag v-for="lang in row.supported_languages?.slice(0, 2)" :key="lang" size="small" type="primary"
              style="margin-right: 4px">
              {{ getLanguageDisplay(lang) }}
            </el-tag>
            <span v-if="row.supported_languages?.length > 2" class="more-tags">
              +{{ row.supported_languages.length - 2 }}
            </span>
          </template>
        </el-table-column>

        <!-- 新增：支持情感列 -->
        <el-table-column label="支持情感" min-width="120">
          <template #default="{ row }">
            <el-tag v-for="emotion in row.supported_emotions?.slice(0, 2)" :key="emotion" size="small" type="success"
              style="margin-right: 4px">
              {{ getEmotionDisplay(emotion) }}
            </el-tag>
            <span v-if="row.supported_emotions?.length > 2" class="more-tags">
              +{{ row.supported_emotions.length - 2 }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="标签" min-width="150">
          <template #default="{ row }">
            <el-tag v-for="tag in row.tags?.slice(0, 2)" :key="tag" size="small" style="margin-right: 4px">
              {{ tag }}
            </el-tag>
            <span v-if="row.tags?.length > 2" class="more-tags">
              +{{ row.tags.length - 2 }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="评分" width="80">
          <template #default="{ row }">
            <span class="rating">
              <el-icon>
                <Star />
              </el-icon>
              {{ row.rating || 5.0 }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="使用次数" width="100">
          <template #default="{ row }">
            {{ row.usage_count || 0 }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="text" size="small" @click="previewVoice(row)">
              试听
            </el-button>
            <el-button type="text" size="small" @click="useTTS(row)" :disabled="!isLoggedIn">
              使用TTS
            </el-button>
            <el-button v-if="isLoggedIn" type="text" size="small" @click="toggleFavorite(row)">
              {{ row.is_favorited ? '取消收藏' : '收藏' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 空状态 -->
    <el-empty v-if="!loading && filteredVoices.length === 0" description="暂无符合条件的音色" />

    <!-- 分页 -->
    <div v-if="filteredVoices.length > 0" class="pagination-wrapper">
      <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize" :page-sizes="[12, 24, 48, 96]"
        :total="filteredVoices.length" layout="total, sizes, prev, pager, next, jumper" @size-change="handleSizeChange"
        @current-change="handleCurrentChange" />
    </div>

    <!-- 音色详情弹窗 -->
    <el-dialog v-model="detailDialogVisible" :title="selectedVoice?.name" width="600px">
      <div v-if="selectedVoice">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="名称">
            {{ selectedVoice.name }}
          </el-descriptions-item>
          <el-descriptions-item label="类型">
            <el-tag :type="selectedVoice.model_type === 'official' ? 'warning' : 'info'">
              {{ selectedVoice.model_type === 'official' ? '官方模型' : '用户模型' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建者">
            {{ selectedVoice.creator_name || '未知' }}
          </el-descriptions-item>
          <el-descriptions-item label="评分">
            {{ selectedVoice.rating || 5.0 }}
          </el-descriptions-item>
          <el-descriptions-item label="使用次数">
            {{ selectedVoice.usage_count || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatTime(selectedVoice.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ selectedVoice.description || '暂无描述' }}
          </el-descriptions-item>
          <el-descriptions-item label="支持语言" :span="2">
            <el-tag v-for="lang in selectedVoice.supported_languages" :key="lang" size="small" type="primary"
              style="margin-right: 4px">
              {{ getLanguageDisplay(lang) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="支持情感" :span="2">
            <el-tag v-for="emotion in selectedVoice.supported_emotions" :key="emotion" size="small" type="success"
              style="margin-right: 4px">
              {{ getEmotionDisplay(emotion) }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="detailDialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="useTTS(selectedVoice)" :disabled="!isLoggedIn">
            使用此音色
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 音频预览播放器 -->
    <audio ref="audioPlayer" style="display: none" @ended="onAudioEnded" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Search,
  Grid,
  List,
  VideoPlay,
  Star,
  StarFilled,
  Microphone
} from '@element-plus/icons-vue'
import { ttsAPI } from '@/api'
import { userStore } from '@/stores/user'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const searchText = ref('')
const selectedTag = ref('')
const selectedType = ref('')
const viewMode = ref('grid')
const currentPage = ref(1)
const pageSize = ref(24)
const selectedVoice = ref(null)
const detailDialogVisible = ref(false)
const currentPlayingVoice = ref(null)
const audioPlayer = ref()

// 数据
const voices = ref([])
const allTags = ref(['男声', '女声', '温柔', '磁性', '播音', '童声', '机器人', '萝莉', '御姐', '少年'])

const defaultAvatar = new URL('@/assets/voice.png', import.meta.url).href

// 计算属性
const isLoggedIn = computed(() => userStore.isLoggedIn.value)

const filteredVoices = computed(() => {
  let result = voices.value

  // 文本搜索
  if (searchText.value.trim()) {
    const keyword = searchText.value.toLowerCase()
    result = result.filter(voice =>
      voice.name.toLowerCase().includes(keyword) ||
      voice.description.toLowerCase().includes(keyword) ||
      voice.creator_name?.toLowerCase().includes(keyword)
    )
  }

  // 标签筛选
  if (selectedTag.value) {
    result = result.filter(voice =>
      voice.tags?.includes(selectedTag.value)
    )
  }

  // 类型筛选
  if (selectedType.value) {
    result = result.filter(voice => voice.model_type === selectedType.value)
  }

  return result
})

const paginatedVoices = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredVoices.value.slice(start, end)
})

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
    'surprised': '惊讶'
  }
  return emotionMap[emotion] || emotion
}

// 方法
async function fetchVoices() {
  loading.value = true
  try {
    const res = await ttsAPI.getAvailableModels({
      per_page: 100,
    })

    if (res.data?.models) {
      voices.value = res.data.models
        .filter(model => model.is_public)
        .map(model => ({
          id: model.id,
          name: model.name,
          description: model.description || '暂无描述',
          avatar: model.avatar_url,
          model_type: model.model_type || 'user',
          tags: model.voice_characteristics || (model.tags ? model.tags.map(tag => tag.name) : []),
          rating: model.quality_score || 5.0,
          usage_count: model.usage_count || 0,
          creator_name: model.creator_name || model.owner_name,
          created_at: model.created_at,
          supported_languages: model.supported_languages || ['zh'],
          supported_emotions: model.supported_emotions || ['neutral'],
          is_favorited: false
        }))

      if (isLoggedIn.value) {
        await fetchFavoriteStatus()
      }
    } else {
      voices.value = []
    }
  } catch (error) {
    console.error('获取音色库失败:', error)
    ElMessage.error('获取音色库失败: ' + (error?.response?.data?.message || error.message))
    voices.value = []
  } finally {
    loading.value = false
  }
}

async function fetchFavoriteStatus() {
  try {
    // 获取用户收藏的音色列表
    // const res = await userAPI.getFavoriteVoices()
    // const favoriteIds = res.data?.favorite_ids || []
    // voices.value.forEach(voice => {
    //   voice.is_favorited = favoriteIds.includes(voice.id)
    // })
  } catch (error) {
    console.error('获取收藏状态失败:', error)
  }
}

function onSearch() {
  currentPage.value = 1
}

function onTagChange() {
  currentPage.value = 1
}

function onTypeChange() {
  currentPage.value = 1
}

function selectVoice(voice) {
  selectedVoice.value = voice
  detailDialogVisible.value = true
}

async function previewVoice(voice) {
  if (currentPlayingVoice.value === voice.id) {
    audioPlayer.value.pause()
    currentPlayingVoice.value = null
    return
  }

  try {
    ElMessage.info(`预览 ${voice.name} - 功能开发中`)

    // 模拟播放
    // if (voice.preview_url) {
    //   audioPlayer.value.src = voice.preview_url
    //   audioPlayer.value.play()
    //   currentPlayingVoice.value = voice.id
    // }
  } catch (error) {
    ElMessage.error('播放预览失败')
  }
}

function useTTS(voice) {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录')
    router.push({ name: 'Login' })
    return
  }

  router.push({
    name: 'TTSPlayground',
    query: { model_id: voice.id }
  })
}

async function toggleFavorite(voice) {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录')
    return
  }

  try {
    // 调用收藏/取消收藏API
    // if (voice.is_favorited) {
    //   await userAPI.removeFavoriteVoice(voice.id)
    //   voice.is_favorited = false
    //   ElMessage.success('已取消收藏')
    // } else {
    //   await userAPI.addFavoriteVoice(voice.id)
    //   voice.is_favorited = true
    //   ElMessage.success('已添加收藏')
    // }

    // 临时模拟
    voice.is_favorited = !voice.is_favorited
    ElMessage.success(voice.is_favorited ? '已添加收藏' : '已取消收藏')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

function goToMyVoices() {
  router.push({ name: 'CreatorCenter' })
}

function handleSizeChange(size) {
  pageSize.value = size
  currentPage.value = 1
}

function handleCurrentChange(page) {
  currentPage.value = page
}

function onAudioEnded() {
  currentPlayingVoice.value = null
}

function formatTime(timeStr) {
  if (!timeStr) return '未知'
  return new Date(timeStr).toLocaleDateString()
}

onMounted(() => {
  fetchVoices()
})
</script>

<style scoped>
.voice-library {
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

.page-header {
  text-align: center;
  margin-bottom: 24px;
  padding: 32px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.title {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 8px 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  font-size: 16px;
  color: #666;
  margin: 0;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  gap: 16px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.search-section {
  display: flex;
  gap: 12px;
  flex: 1;
}

.search-input {
  width: 300px;
}

.tag-select,
.type-select {
  width: 150px;
}

.view-controls {
  flex-shrink: 0;
}

.stats-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  font-size: 14px;
  color: #666;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.voice-card-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.voice-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 2px solid rgba(228, 231, 237, 0.6);
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.voice-card:hover {
  border-color: rgba(102, 126, 234, 0.8);
  transform: translateY(-4px);
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.2);
}

.voice-card.selected {
  border-color: #667eea;
  background: linear-gradient(135deg, rgba(236, 245, 255, 0.95) 0%, rgba(255, 255, 255, 0.95) 100%);
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.3);
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

.voice-type-badge {
  position: absolute;
  top: 8px;
  right: 8px;
}

.voice-info {
  padding: 20px;
}

.voice-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.voice-desc {
  font-size: 14px;
  color: #606266;
  margin-bottom: 16px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.voice-details {
  margin-bottom: 16px;
  padding: 12px;
  background: linear-gradient(135deg, #f8f9fb 0%, #e8f4f8 100%);
  border-radius: 8px;
  border: 1px solid rgba(228, 231, 237, 0.6);
}

.detail-section {
  margin-bottom: 8px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-label {
  font-size: 12px;
  color: #666;
  font-weight: 500;
  margin-bottom: 4px;
}

.detail-content {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.voice-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 12px;
  min-height: 24px;
}

.voice-stats {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
  margin-bottom: 12px;
}

.voice-stats span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.voice-actions {
  display: flex;
  gap: 8px;
}

.voice-actions .el-button {
  flex: 1;
}

.voice-table-container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.more-tags {
  font-size: 12px;
  color: #999;
}

.rating {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #f39c12;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .voice-card-list {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }
}

@media (max-width: 768px) {
  .voice-library {
    padding: 16px;
  }

  .filter-bar {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .search-section {
    flex-direction: column;
    gap: 8px;
  }

  .search-input,
  .tag-select,
  .type-select {
    width: 100%;
  }

  .voice-card-list {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 16px;
  }

  .voice-actions {
    flex-direction: column;
    gap: 6px;
  }
}

/* Element Plus 样式覆盖 */
:deep(.el-table) {
  border-radius: 8px;
  overflow: hidden;
  background: transparent;
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

:deep(.el-pagination) {
  --el-pagination-button-bg-color: rgba(255, 255, 255, 0.8);
  --el-pagination-hover-color: #667eea;
}
</style>