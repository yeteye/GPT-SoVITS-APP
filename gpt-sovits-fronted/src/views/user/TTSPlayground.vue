<template>
  <div class="tts-playground">
    <h2>文本转语音</h2>
    <el-form :model="form" label-position="top">
      <el-form-item label="选择音色">
        <el-select v-model="form.voice" placeholder="请选择音色">
          <el-option v-for="item in voices" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="输入文本">
        <el-input v-model="form.text" type="textarea" rows="4" />
      </el-form-item>
      <el-button type="primary" @click="synthesize">生成语音</el-button>
    </el-form>
  </div>
</template>

<script setup>
import { reactive } from 'vue'

const form = reactive({
  voice: '',
  text: ''
})

const voices = [
  { id: 1, name: 'AI小雅' },
  { id: 2, name: 'AI豪哥' }
]

function synthesize() {
  console.log('合成请求', form)
}
</script>

<style scoped>
.tts-playground {
  padding: 24px;
  max-width: 640px;
}
</style>
