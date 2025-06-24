<template>
  <div class="tts-playground">

    <!-- 主体内容区域 -->
    <el-container class="main-content">
      <!-- 文本输入编辑器 -->
      <el-aside class="editor-panel">
        <h2>文本输入</h2>
        <el-input
          type="textarea"
          v-model="text"
          placeholder="请输入要合成的文本..."
          rows="12"
          resize="none"
        />
        <div class="control-buttons">
          <el-button type="primary" :loading="loading" @click="onSynthesize">合成语音</el-button>
          <el-button @click="text = ''">清空</el-button>
        </div>
        <audio
          v-if="audioUrl"
          :src="audioUrl"
          controls
          style="margin-top: 20px; width: 100%"
        />
      </el-aside>

      <!-- 音色库展示 -->
      <el-main class="voice-library">
        <h2>音色选择</h2>
        <el-row :gutter="20">
          <el-col :span="8" v-for="(voice, index) in voices" :key="index">
            <el-card :class="{ selected: selectedVoice === voice.id }" @click="selectVoice(voice.id)" shadow="hover">
              <div class="voice-name">{{ voice.name }}</div>
              <p>{{ voice.description }}</p>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { synthesizeTTS } from '@/api/tts'

const router = useRouter()
const active = ref('TTSPlayground')
const text = ref('你好，欢迎使用 GPT-SoVITS 在线语音合成系统。')
const selectedVoice = ref(null)
const loading = ref(false)
const audioUrl = ref(null)

const voices = [u
  { id: 'v1', name: '官方音色 A', description: '适用于新闻播报风格' },
  { id: 'v2', name: '创作者音色 B', description: '更具感情的自然语调' },
  { id: 'v3', name: '官方音色 C', description: '适合客服语音应用' }
]

function selectVoice(id) {
  selectedVoice.value = id
}

async function onSynthesize() {
  if (!text.value || !selectedVoice.value) {
    ElMessage.warning('请填写文本并选择一个音色')
    return
  }

  loading.value = true
  audioUrl.value = null

  try {
    const payload = {
      text: text.value,
      text_lang: 'zh',
      ref_audio_path: `${selectedVoice.value}.wav`, // 实际需匹配后端已有音色路径
      prompt_text: '',
      prompt_lang: 'zh',
      text_split_method: 'cut5',
      batch_size: 1,
      media_type: 'wav',
      streaming_mode: false,
      top_k: 5,
      top_p: 1,
      temperature: 1,
      batch_threshold: 0.75,
      split_bucket: true,
      speed_factor: 1,
      fragment_interval: 0.3,
      seed: -1,
      parallel_infer: true,
      repetition_penalty: 1.35,
      sample_steps: 32,
      super_sampling: false,
      aux_ref_audio_paths: []
    }

    const response = await synthesizeTTS(payload, { responseType: 'blob' })

    const blob = new Blob([response.data], { type: 'audio/wav' })
    audioUrl.value = URL.createObjectURL(blob)

    ElMessage.success('语音合成成功，点击播放试听')

  } catch (err) {
    ElMessage.error('语音合成失败，请检查后端接口或输入内容')
    console.error(err)
  } finally {
    loading.value = false
  }
}

function onSelect(index) {
  router.push({ name: index })
}
</script>

<style scoped>
.tts-playground {
  min-height: 100vh;
  background: #f8f9fb;
  display: flex;
  flex-direction: column;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}
.header-left {
  display: flex;
  align-items: center;
}
.logo {
  height: 40px;
  margin-right: 16px;
}
.title {
  font-size: 22px;
  font-weight: 600;
  color: #333;
}
.nav-menu {
  flex-grow: 1;
}
.main-content {
  display: flex;
  flex-direction: row;
  height: calc(100vh - 72px);
  overflow: hidden;
}
.editor-panel {
  width: 400px;
  background: #fff;
  padding: 24px;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.04);
}
.editor-panel h2 {
  margin-bottom: 16px;
  font-size: 18px;
}
.control-buttons {
  margin-top: 16px;
  display: flex;
  gap: 10px;
}
.voice-library {
  padding: 24px;
  overflow-y: auto;
}
.voice-library h2 {
  margin-bottom: 16px;
}
.voice-name {
  font-weight: 600;
  font-size: 16px;
  margin-bottom: 8px;
}
.selected {
  border: 2px solid #409eff;
}
</style>
