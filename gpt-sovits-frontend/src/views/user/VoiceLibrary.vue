<template>
  <div class="voice-library">
    <h2 class="title">音色库</h2>

    <!-- 搜索与标签过滤 -->
    <div class="filter-bar">
      <el-input v-model="searchText" placeholder="搜索音色名称..." clearable class="search-input" />
      <el-select v-model="selectedTag" placeholder="选择标签" clearable class="tag-select">
        <el-option v-for="tag in allTags" :key="tag" :label="tag" :value="tag" />
      </el-select>
    </div>

    <!-- 卡片展示区 -->
    <div class="voice-card-list">
      <div
        v-for="voice in filteredVoices"
        :key="voice.id"
        class="voice-card"
        @click="goToVoiceDetail(voice)"
      >
        <img :src="voice.avatar" class="voice-avatar" alt="avatar" />
        <div class="voice-info">
          <div class="voice-name">{{ voice.name }}</div>
          <div class="voice-desc">{{ voice.description }}</div>
          <div class="voice-tags">
            <el-tag
              v-for="tag in voice.tags"
              :key="tag"
              size="small"
              type="info"
              effect="plain"
            >
              {{ tag }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>


    <div v-if="filteredVoices.length === 0" class="empty">暂无符合条件的音色</div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
const router = useRouter()

function goToVoiceDetail(voice) {
  router.push({ name: 'VoiceDetail', query: { id: voice.id } })
}


const searchText = ref('')
const selectedTag = ref(null)
const allTags = ['男声', '女声', '温柔', '磁性', '播音', '童声', '机器人']

const publicVoices = ref([
  {
    id: 1,
    name: 'AI小雅',
    description: '温柔女声，适合读书场景',
    tags: ['女声', '温柔'],
    avatar: new URL('@/assets/voice.png', import.meta.url).href
  },
  {
    id: 2,
    name: 'AI豪哥',
    description: '磁性男声，适合配音',
    tags: ['男声', '磁性', '播音'],
    avatar: new URL('@/assets/voice.png', import.meta.url).href
  },
  {
    id: 3,
    name: '童音乐乐',
    description: '可爱童声，适合儿童读物',
    tags: ['童声', '女声'],
    avatar: new URL('@/assets/voice.png', import.meta.url).href
  },
  {
    id: 4,
    name: 'AI机器人',
    description: '机械声音，适合科幻场景',
    tags: ['男声', '机器人'],
    avatar: new URL('@/assets/voice.png', import.meta.url).href
  },
  {
    id: 5,
    name: 'AI小白',
    description: '清新女声，适合校园场景',
    tags: ['女声', '温柔'],
    avatar: new URL('@/assets/voice.png', import.meta.url).href
  },
  {
    id: 6,
    name: 'AI小刚',
    description: '阳光男声，适合运动场景',
    tags: ['男声', '磁性'],
    avatar: new URL('@/assets/voice.png', import.meta.url).href
  }
])

const filteredVoices = computed(() => {
  return publicVoices.value.filter(v => {
    const matchName = v.name.includes(searchText.value)
    const matchTag = selectedTag.value ? v.tags.includes(selectedTag.value) : true
    return matchName && matchTag
  })
})

function playVoice(voice) {
  // TODO: 播放音频 or 跳转
  console.log('试听:', voice.name)
}
</script>

<style scoped>
.voice-library {
  padding: 32px;
  background: #f9fafc;
}
.title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 20px;
}

.filter-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}
.search-input {
  width: 300px;
}
.tag-select {
  width: 180px;
}

.voice-card-list {
  display: grid;
  grid-template-columns: repeat(5, 1fr); /* 每行5个 */
  gap: 24px;
  justify-items: center;
}

.voice-card {
  width: 100%; /* 填满栅格单元格 */
  max-width: 200px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  cursor: pointer;
  overflow: hidden;
  transition: all 0.2s;
}

.voice-card:hover {
  transform: translateY(-4px);
}
.voice-avatar {
  width: 100%;
  height: 160px;
  object-fit: cover;
}
.voice-info {
  padding: 12px;
}
.voice-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}
.voice-desc {
  font-size: 13px;
  color: #777;
  margin: 6px 0;
}
.voice-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.empty {
  text-align: center;
  color: #888;
  margin-top: 40px;
  font-size: 16px;
}
</style>
