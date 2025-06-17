<template>
  <el-container direction="vertical" class="home-container">
    <!-- 顶部横幅标题 -->
    <el-header class="header">
      <img src="@/assets/logo.svg" class="logo" alt="logo" />
      <h1>GPT-SoVITS 在线语音克隆平台</h1>
    </el-header>

    <!-- 轮播图（核心功能广告） -->
    <el-main>
      <el-carousel height="320px" autoplay>
        <el-carousel-item v-for="(item, index) in banners" :key="index">
          <div class="banner" :style="{ backgroundImage: `url(${item.image})` }">
            <div class="banner-text">
              <h2>{{ item.title }}</h2>
              <p>{{ item.description }}</p>
            </div>
          </div>
        </el-carousel-item>
      </el-carousel>

      <!-- 功能展示卡片 -->
      <div class="features">
        <el-row :gutter="20">
          <el-col :span="8" v-for="(feature, index) in features" :key="index">
            <el-card shadow="hover">
              <h3>{{ feature.title }}</h3>
              <p>{{ feature.description }}</p>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- CTA 按钮 -->
      <div class="cta">
        <el-button type="primary" size="large" @click="goGenerate">立即体验</el-button>
      </div>
    </el-main>
  </el-container>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()

const banners = [
  {
    image: '/banner.png',
    title: '高质量语音合成',
    description: '基于 So-VITS 与 GPT 模型，支持高拟人度 TTS。'
  },
  {
    image: '/banner.png',
    title: '小样本音色克隆',
    description: '上传少量语音样本即可生成专属音色。'
  },
  {
    image: '/banner.png',
    title: '多角色支持',
    description: '适用于创作、配音、教学等多种场景。'
  }
]

const features = [
  { title: '一键文本转语音', description: '快速生成自然语音，支持多语言、语速调节。' },
  { title: '角色管理与克隆', description: '支持上传语音自定义角色，灵活管理。' },
  { title: '云端部署', description: '支持 GPU 云推理，高效快速响应。' }
]

function goGenerate() {
  router.push({ name: 'Generate' })
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: #f7f9fc;
}
.header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #ffffff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}
.logo {
  height: 40px;
}
.el-carousel {
  margin: 24px 0;
  border-radius: 12px;
  overflow: hidden;
}
.banner {
  height: 100%;
  background-size: cover;
  background-position: center;
  position: relative;
  display: flex;
  align-items: flex-end;
  padding: 20px;
  color: #fff;
}
.banner-text {
  background: rgba(0, 0, 0, 0.4);
  padding: 12px 16px;
  border-radius: 8px;
}
.features {
  margin: 32px 0;
}
.cta {
  text-align: center;
  margin: 40px 0;
}
</style>
