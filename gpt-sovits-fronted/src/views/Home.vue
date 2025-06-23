<template>
  <div class="home-container">
    <!-- 顶部横幅导航 + 菜单 -->
    <header class="header">
      <div class="header-left">
        <img src="@/assets/logo.svg" class="logo" alt="logo" />
        <h1 class="title">GPT-SoVITS 在线语音克隆平台</h1>
      </div>
      <nav class="nav-menu">
        <el-menu mode="horizontal" :default-active="active" class="el-menu-demo" @select="onSelect">
          <el-menu-item index="TTSPlayground">文本转语音</el-menu-item>
          <el-menu-item index="VoiceClone">音色克隆</el-menu-item>
          <el-menu-item index="CreatorCenter">创作者中心</el-menu-item>
          <el-menu-item index="VoiceLibrary">音色库</el-menu-item>
          <el-menu-item index="TaskHistory">历史记录</el-menu-item>
        </el-menu>
      </nav>
    </header>

    <!-- 顶部轮播图 -->
    <div class="carousel-wrapper">
      <el-carousel height="320px" autoplay>
        <el-carousel-item v-for="(item, index) in banners" :key="index">
          <div class="carousel-item" :style="{ backgroundImage: `url(${item.image})` }">
            <div class="carousel-text">
              <h2>{{ item.title }}</h2>
              <p>{{ item.description }}</p>
            </div>
          </div>
        </el-carousel-item>
      </el-carousel>
    </div>

    <!-- 功能展示页面列表 -->
    <section v-for="(section, index) in sections" :key="index" class="feature-section">
      <div class="feature-content">
        <img :src="section.image" class="feature-image" alt="feature image" />
        <div class="feature-text">
          <h2>{{ section.title }}</h2>
          <p>{{ section.description }}</p>
          <el-button type="primary" @click="() => router.push({ name: section.route })">
            {{ section.buttonText }}
          </el-button>
        </div>
      </div>
    </section>

    <!-- 页脚 -->
    <footer class="footer">
      <p>© 2025 GPT-SoVITS · <a href="#">用户协议</a> · <a href="#">隐私政策</a></p>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
const router = useRouter()
const active = ref('')

const onSelect = (index) => {
  router.push({ name: index })
}

const banners = [
  {
    image: new URL('@/assets/banner.jpg', import.meta.url).href,
    title: '高拟真语音生成体验',
    description: '依托 So-VITS 与 GPT 技术，支持多情感 TTS 与角色音色自定义'
  },
  {
    image: new URL('@/assets/banner.jpg', import.meta.url).href,
    title: '小样本音色克隆',
    description: '上传几秒音频，即可打造你的数字分身音色'
  }
]

const sections = [
  {
    title: '🗣️ 文本转语音',
    description: '将输入文本转为高拟人度语音，支持语速与情感调节。',
    image: new URL('@/assets/banner.jpg', import.meta.url).href,
    buttonText: '进入文本转语音',
    route: 'TTSPlayground'
  },
  {
    title: '🧬 音色克隆',
    description: '上传少量语音样本，快速生成专属音色模型。',
    image: new URL('@/assets/banner.jpg', import.meta.url).href,
    buttonText: '立即克隆音色',
    route: 'VoiceClone'
  },
  {
    title: '🎧 创作者中心',
    description: '上传、管理并发布你的音色模型，构建专属声音品牌。',
    image: new URL('@/assets/banner.jpg', import.meta.url).href,
    buttonText: '进入创作者中心',
    route: 'CreatorCenter'
  },
  {
    title: '📚 音色库',
    description: '浏览官方和创作者上传的音色，试听并使用语音合成。',
    image: new URL('@/assets/banner.jpg', import.meta.url).href,
    buttonText: '探索音色库',
    route: 'VoiceLibrary'
  },
  {
    title: '☁️ 云端部署',
    description: '基于高性能 GPU 云服务运行，保障响应速度与并发。',
    image: new URL('@/assets/banner.jpg', import.meta.url).href,
    buttonText: '了解部署方案',
    route: 'DeployIntro'
  },
  {
    title: '📜 历史记录',
    description: '查看你的音色克隆和语音合成历史记录与任务状态。',
    image: new URL('@/assets/banner.jpg', import.meta.url).href,
    buttonText: '查看任务记录',
    route: 'TaskHistory'
  }
]
</script>

<style scoped>
.home-container {
  display: flex;
  flex-direction: column;
  background: #f9fafc;
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
  font-size: 24px;
  font-weight: 600;
  color: #333;
}
.nav-menu {
  flex-grow: 1;
}
.carousel-wrapper {
  margin: 20px 0;
}
.carousel-item {
  height: 320px;
  background-size: cover;
  background-position: center;
  position: relative;
  display: flex;
  align-items: flex-end;
  padding: 24px;
  color: #fff;
}
.carousel-text {
  background: rgba(0, 0, 0, 0.5);
  padding: 16px 20px;
  border-radius: 8px;
}
.feature-section {
  padding: 60px 24px;
  background: #fff;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}
.feature-content {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 40px;
  max-width: 1080px;
  margin: 0 auto;
}
.feature-image {
  width: 400px;
  height: auto;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}
.feature-text {
  flex: 1;
}
.feature-text h2 {
  font-size: 28px;
  margin-bottom: 16px;
  color: #222;
}
.feature-text p {
  font-size: 16px;
  margin-bottom: 20px;
  color: #555;
}
.footer {
  text-align: center;
  padding: 24px;
  background: #f1f1f1;
  color: #888;
  font-size: 14px;
}
.footer a {
  color: #888;
  margin: 0 8px;
}
</style>
