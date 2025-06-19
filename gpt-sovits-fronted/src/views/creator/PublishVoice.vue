<template>
  <div class="publish-voice">
    <h2>发布音色</h2>
    <el-form label-position="top">
      <el-form-item label="选择模型">
        <el-select placeholder="选择一个训练完成的模型">
          <el-option label="配音女声" value="1" />
        </el-select>
      </el-form-item>
      <el-form-item label="设置为公开">
        <el-switch v-model="isPublic" />
      </el-form-item>
      <el-button type="primary">确认发布</el-button>
    </el-form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const isPublic = ref(false)
</script>

<style scoped>
.publish-voice {
  padding: 24px;
  max-width: 600px;
}
</style>
