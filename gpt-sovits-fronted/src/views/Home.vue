<template>
  <el-container direction="vertical" class="home-container">
    <el-header>
      <h2>欢迎使用 GPT-SoVITS 在线演示</h2>
    </el-header>
    <el-main>
      <p>这里可以简要介绍 GPT-SoVITS 的功能、使用流程等。</p>
      <el-button type="primary" @click="goGenerate">立即体验</el-button>
    </el-main>
  </el-container>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
function goGenerate() {
  router.push({ name: 'Generate' })
}
</script>

<style scoped>
.home-container {
  padding: 20px;
}
</style>
