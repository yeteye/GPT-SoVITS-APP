<template>
  <header class="header">
    <div class="header-left" @click="goHome">
      <img src="@/assets/music.svg" class="logo" alt="logo" />
      <h1 class="title">GPT-SoVITS 在线语音克隆</h1>
    </div>
    <nav class="nav-menu">
      <el-menu mode="horizontal" :default-active="active" class="el-menu-demo" @select="onSelect">
        <el-menu-item index="TTSPlayground">文本转语音</el-menu-item>
        <el-menu-item index="VoiceClone">音色克隆</el-menu-item>
        <el-menu-item index="CreatorCenter">创作者中心</el-menu-item>
        <el-menu-item index="VoiceLibrary">音色库</el-menu-item>
        <el-menu-item index="TaskHistory">历史记录</el-menu-item>
        <el-menu-item index="UserCenter">用户中心</el-menu-item>
        <el-menu-item index="HelpCenter">帮助中心</el-menu-item>
      </el-menu>
    </nav>
  </header>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const router = useRouter()
const route = useRoute()
const active = ref(route.name)

watch(route, () => {
  active.value = route.name
})

const onSelect = (index) => {
  router.push({ name: index })
}

const goHome = () => {
  router.push({ name: 'Home' })
}
</script>

<style scoped>
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
  cursor: pointer;
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
</style>
