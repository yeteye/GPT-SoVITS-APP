<template>
  <div class="tts-playground">
    <!-- 顶部菜单栏 -->
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
          <el-button type="primary" @click="onSynthesize">合成语音</el-button>
          <el-button @click="text = ''">清空</el-button>
        </div>
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

const router = useRouter()
const active = ref('TTSPlayground')
const text = ref('你好，欢迎使用 GPT-SoVITS 在线语音合成系统。')
const selectedVoice = ref(null)

const voices = [
  { id: 'v1', name: '官方音色 A', description: '适用于新闻播报风格' },
  { id: 'v2', name: '创作者音色 B', description: '更具感情的自然语调' },
  { id: 'v3', name: '官方音色 C', description: '适合客服语音应用' }
]

function selectVoice(id) {
  selectedVoice.value = id
}

function onSynthesize() {
  if (!text.value || !selectedVoice.value) {
    ElMessage.warning('请填写文本并选择一个音色')
    return
  }
  // 模拟跳转或发起合成任务
  console.log('提交合成任务:', text.value, selectedVoice.value)
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
