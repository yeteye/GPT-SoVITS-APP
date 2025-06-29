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
            <el-tag v-for="lang in selectedVoice.supported_languages" :key="lang" size="small"
              style="margin-right: 4px">
              {{ lang }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="支持情感" :span="2">
            <el-tag v-for="emotion in selectedVoice.supported_emotions" :key="emotion" size="small"
              style="margin-right: 4px">
              {{ emotion }}
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

// 方法
async function fetchVoices() {
  loading.value = true
  try {
    // 修复：使用正确的API参数，不超过后端限制
    const res = await ttsAPI.getAvailableModels({
      per_page: 100, // 不超过后端限制的最大值
      // 移除可能导致错误的参数
    })

    if (res.data?.models) {
      voices.value = res.data.models
        .filter(model => model.is_public) // 客户端过滤公开模型
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
          supported_languages: model.supported_languages || ['中文'],
          supported_emotions: model.supported_emotions || ['自然'],
          is_favorited: false // 需要从后端获取收藏状态
        }))

      // 获取用户收藏状态
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
  // 获取用户收藏的音色列表
  try {
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
    // 停止播放
    audioPlayer.value.pause()
    currentPlayingVoice.value = null
    return
  }

  try {
    // 这里应该调用API获取预览音频
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
  background: #f8f9fb;
  min-height: 100vh;
}

.page-header {
  text-align: center;
  margin-bottom: 24px;
}

.title {
  font-size: 28px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #303133;
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
  font-size: 14px;
  color: #666;
}

.voice-card-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.voice-card {
  background: #fff;
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.voice-card:hover {
  border-color: #409eff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.voice-card.selected {
  border-color: #409eff;
  background: linear-gradient(135deg, #ecf5ff 0%, #fff 100%);
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
  background: rgba(0, 0, 0, 0.3);
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
  padding: 16px;
}

.voice-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.voice-desc {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.voice-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
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
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 24px;
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
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .voice-card-list {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
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
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
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
}

:deep(.el-dialog) {
  border-radius: 16px;
}
</style>