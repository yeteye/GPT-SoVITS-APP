<template>
  <el-container direction="vertical" class="home-container">
    <!-- 顶部横幅 -->
    <el-header class="header">
      <img src="@/assets/logo.svg" class="logo" alt="logo" />
      <h1>GPT-SoVITS 在线语音克隆平台</h1>
    </el-header>

    <!-- 轮播图区域 -->
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

      <!-- 核心功能展示 -->
      <div class="features">
        <el-row :gutter="20">
          <el-col :span="8" v-for="(feature, index) in features" :key="index">
            <el-card shadow="hover">
              <h3>{{ feature.icon }} {{ feature.title }}</h3>
              <p>{{ feature.description }}</p>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 其他模块入口 -->
      <div class="entry-cards">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card shadow="hover" class="entry-card" @click="goToCreator">
              <h3>🎧 创作者中心</h3>
              <p>上传管理音色模型，打造你的数字声音品牌。</p>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="hover" class="entry-card" @click="goToLibrary">
              <h3>📚 音色库</h3>
              <p>探索热门音色，试听并一键合成语音。</p>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- CTA 行动按钮 -->
      <div class="cta">
        <el-button type="primary" size="large" @click="goGenerate">立即体验</el-button>
      </div>
    </el-main>

    <!-- 页脚 -->
    <el-footer class="footer">
      <p>© 2025 GPT-SoVITS · <a href="#">用户协议</a> · <a href="#">隐私政策</a></p>
    </el-footer>
  </el-container>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const banners = [
  {
    image: new URL('/banner.png', import.meta.url).href,
    title: '高质量语音合成',
    description: '基于 So-VITS 与 GPT 模型，支持高拟人度 TTS。'
  },
  {
    image: new URL('/banner.png', import.meta.url).href,
    title: '小样本音色克隆',
    description: '上传少量语音样本即可生成专属音色。'
  },
  {
    image: new URL('/banner.png', import.meta.url).href,
    title: '多角色支持',
    description: '适用于创作、配音、教学等多种场景。'
  }
]

const features = [
  { icon: '🗣️', title: '文本转语音', description: '输入文本快速合成自然语音，支持多语种语速调节。' },
  { icon: '🧬', title: '音色克隆', description: '上传语音样本，自定义角色音色并克隆个性模型。' },
  { icon: '☁️', title: '云端推理', description: '基于 GPU 云部署，保障性能与并发效率。' }
]

function goGenerate() {
  router.push({ name: 'Generate' })
}
function goToCreator() {
  router.push({ name: 'CreatorCenter' })
}
function goToLibrary() {
  router.push({ name: 'VoiceLibrary' })
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: #f7f9fc;
  display: flex;
  flex-direction: column;
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
.entry-cards {
  margin: 24px 0;
}
.entry-card {
  cursor: pointer;
  transition: transform 0.2s ease;
}
.entry-card:hover {
  transform: translateY(-4px);
}
.footer {
  text-align: center;
  padding: 16px;
  font-size: 14px;
  color: #888;
}
.footer a {
  margin: 0 8px;
  color: #888;
  text-decoration: none;
}
</style>
