<template>
  <div class="voice-library">
    <h2>音色库</h2>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="推荐音色" name="public">
        <el-row :gutter="20">
          <el-col :span="6" v-for="item in publicVoices" :key="item.id">
            <el-card :body-style="{ padding: '12px' }">
              <p><strong>{{ item.name }}</strong></p>
              <p>{{ item.description }}</p>
              <el-button type="primary" size="small">试听</el-button>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>
      <el-tab-pane label="我的收藏" name="favorite">
        <p>收藏功能开发中...</p>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const activeTab = ref('public')
const publicVoices = [
  { id: 1, name: 'AI小雅', description: '温柔女声，适合读书' },
  { id: 2, name: 'AI豪哥', description: '磁性男声，适合配音' }
]
</script>

<style scoped>
.voice-library {
  padding: 24px;
}
</style>
