<template>
  <div class="tts-playground">
    <!-- 顶部菜单栏，可选，如已有全局布局可移除 -->
    <header class="header">
      <div class="header-left">
        <img src="@/assets/logo.svg" class="logo" alt="logo" />
        <h1 class="title">GPT-SoVITS 文本转语音</h1>
      </div>
      <nav class="nav-menu">
        <el-menu mode="horizontal" :default-active="active" class="el-menu-demo" @select="onSelect">
          <el-menu-item index="Home">首页</el-menu-item>
          <el-menu-item index="VoiceClone">音色克隆</el-menu-item>
          <el-menu-item index="VoiceLibrary">音色库</el-menu-item>
          <el-menu-item index="TaskHistory">历史记录</el-menu-item>
        </el-menu>
      </nav>
    </header>

    <!-- 主体内容区域 -->
    <el-container class="main-content">
      <!-- 文本输入与配置面板 -->
      <el-aside class="editor-panel">
        <h2>文本输入与设置</h2>
        <!-- 文本语言选择 -->
        <el-select v-model="textLang" placeholder="选择文本语言" style="margin-bottom: 10px; width: 100%">
          <el-option label="中文" value="zh" />
          <el-option label="日语" value="ja" />
          <el-option label="英文" value="en" />
        </el-select>
        <!-- 模型选择 -->
        <el-select v-model="selectedModel" placeholder="选择模型" style="margin-bottom: 10px; width: 100%">
          <el-option v-for="m in models" :key="m.id" :label="m.name" :value="m.id" />
        </el-select>
        <!-- 情感选择 -->
        <el-select v-model="selectedEmotion" placeholder="选择情感" style="margin-bottom: 10px; width: 100%">
          <el-option v-for="e in emotions" :key="e.id" :label="e.name" :value="e.id" />
        </el-select>
        <!-- 文本输入 -->
        <el-input
          type="textarea"
          v-model="text"
          placeholder="请输入要合成的文本..."
          rows="12"
          resize="none"
        />
        <div class="control-buttons">
          <el-button type="primary" :loading="loading" @click="onSynthesize">合成语音</el-button>
          <el-button @click="resetAll">重置</el-button>
        </div>
        <!-- 播放合成结果 -->
        <audio
          v-if="audioUrl"
          :src="audioUrl"
          controls
          style="margin-top: 20px; width: 100%"
        />
      </el-aside>

      <!-- 音色库选择面板 -->
      <el-main class="voice-library">
        <h2>音色选择</h2>
        <el-row :gutter="20">
          <el-col :span="8" v-for="(voice, index) in voices" :key="voice.id">
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { synthesizeTTS } from '@/api/tts'

const router = useRouter()
const active = ref('TTSPlayground')
const text = ref('你好，欢迎使用 GPT-SoVITS 在线语音合成系统。')
const textLang = ref('zh')
const selectedModel = ref(null)
const selectedVoice = ref(null)
const selectedEmotion = ref(null)
const loading = ref(false)
const audioUrl = ref(null)
const models = ref([])

// 获取模型列表，从后端接口
async function fetchModels() {
  try {
    const res = await axios.get('/api/models') // 假设后端 GET /api/models 返回 [{id, name, t2s_path, vits_path}, ...]
    models.value = res.data
  } catch (err) {
    console.error('获取模型列表失败', err)
    ElMessage.error('无法获取模型列表')
  }
}
onMounted(() => {
  fetchModels()
})

// 情感配置列表，可以改为从后端动态获取
const emotions = [
  {
    id: 'jingyuan',
    name: '景元 - 正常',
    ref_audio_path: 'archive_jingyuan_1.wav',
    prompt_text: '我是「罗浮」云骑将军景元。',
    prompt_lang: 'zh'
  },
  {
    id: 'sad',
    name: '忧郁语气',
    ref_audio_path: 'sad_sample.wav',
    prompt_text: '我感觉今天一切都很糟糕……',
    prompt_lang: 'zh'
  },
  {
    id: 'anime',
    name: '动漫语气（JP）',
    ref_audio_path: 'anime_girl.wav',
    prompt_text: 'お前のことだから、少しかっこいいなーとか思って言ったのだろう。',
    prompt_lang: 'ja'
  }
]

// 音色库列表，可以改为从后端动态获取
const voices = [
  {id: 'v1', name: '官方音色 A', description: '适用于新闻播报风格'},
  {id: 'v2', name: '创作者音色 B', description: '更具感情的自然语调'},
  {id: 'v3', name: '官方音色 C', description: '适合客服语音应用'}
]

function selectVoice(id) {
  selectedVoice.value = id
}

function resetAll() {
  text.value = ''
  selectedModel.value = null
  selectedVoice.value = null
  selectedEmotion.value = null
  textLang.value = 'zh'
  audioUrl.value && URL.revokeObjectURL(audioUrl.value)
  audioUrl.value = null
}

async function onSynthesize() {
  if (!text.value || !selectedModel.value || !selectedVoice.value || !selectedEmotion.value) {
    ElMessage.warning('请填写文本、选择模型、音色和情感')
    return
  }

  const model = models.value.find(m => m.id === selectedModel.value)
  if (!model) {
    ElMessage.error('模型信息无效')
    return
  }
  const emotion = emotions.find(e => e.id === selectedEmotion.value)
  if (!emotion) {
    ElMessage.error('情感信息无效')
    return
  }

  loading.value = true
  audioUrl.value && URL.revokeObjectURL(audioUrl.value)
  audioUrl.value = null

  try {
    // 构造 payload，包括模型路径或 id
    const payload = {
      text: text.value,
      text_lang: textLang.value,
      ref_audio_path: emotion.ref_audio_path,
      prompt_text: emotion.prompt_text,
      prompt_lang: emotion.prompt_lang,
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
      aux_ref_audio_paths: [],
      model_id: selectedModel.value,
      // 若后端需要具体权重路径，可传 model.t2s_path, model.vits_path
      t2s_weights_path: model.t2s_path,
      vits_weights_path: model.vits_path
    }

    const response = await synthesizeTTS(payload, {responseType: 'blob'})
    const blob = new Blob([response.data], {type: 'audio/wav'})
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
  router.push({name: index})
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
