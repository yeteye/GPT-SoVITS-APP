<template>
  <div class="my-voices">
    <h2 class="title">我的音色</h2>

    <el-alert type="info" :closable="false" show-icon>
      你可以在这里查看和管理自己上传训练的私有音色，支持设为公开、克隆训练和删除。
    </el-alert>

    <div class="voice-card-list">
      <div
        v-for="voice in myVoices"
        :key="voice.id"
        class="voice-card"
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
          <div class="voice-actions">
            <el-button size="small" type="primary" plain @click="cloneVoice(voice)">克隆训练</el-button>
            <el-button size="small" type="success" plain @click="makePublic(voice)" :disabled="voice.isPublic">
              {{ voice.isPublic ? '已公开' : '设为公开' }}
            </el-button>
            <el-button size="small" type="danger" plain @click="deleteVoice(voice.id)">删除</el-button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="myVoices.length === 0" class="empty">暂无音色，请上传样本训练后管理。</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'

const myVoices = ref([])

onMounted(() => {
  fetchMyVoices()
})

function fetchMyVoices() {
  // 模拟 API 拉取，真实应改为 axios.get('/api/my-voices')
  myVoices.value = [
    {
      id: 101,
      name: 'AI小雅（测试）',
      description: '温柔女声，适合叙述场景',
      tags: ['女声', '温柔'],
      isPublic: false,
      avatar: new URL('@/assets/voice.png', import.meta.url).href
    },
    {
      id: 102,
      name: '朗读助手-浩然',
      description: '沉稳男声，适合播报新闻',
      tags: ['男声', '磁性', '播音'],
      isPublic: true,
      avatar: new URL('@/assets/voice.png', import.meta.url).href
    }
  ]
}

function cloneVoice(voice) {
  ElMessage.success(`已提交 ${voice.name} 的克隆训练任务`)
  // TODO: 调用 API 发起克隆任务
}

function makePublic(voice) {
  // TODO: 调用接口 /api/voice/:id/public
  voice.isPublic = true
  ElMessage.success(`${voice.name} 已设为公开`)
}

function deleteVoice(id) {
  ElMessageBox.confirm('确定删除该音色？操作不可撤回', '警告', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    myVoices.value = myVoices.value.filter(v => v.id !== id)
    ElMessage.success('音色已删除')
    // TODO: 调用接口删除
  })
}
</script>

<style scoped>
.my-voices {
  padding: 32px;
  background: #f9fafc;
}
.title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 20px;
}
.voice-card-list {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  justify-content: center;
}
.voice-card {
  width: 220px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
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
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.voice-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}
.voice-desc {
  font-size: 13px;
  color: #777;
}
.voice-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.voice-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 8px;
}
.empty {
  text-align: center;
  color: #888;
  margin-top: 40px;
  font-size: 16px;
}
</style>
