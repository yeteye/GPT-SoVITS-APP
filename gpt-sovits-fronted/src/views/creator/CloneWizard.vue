<template>
  <div class="clone-wizard">
    <h2>创建音色模型</h2>
    <el-form :model="form" label-position="top">
      <el-form-item label="音色名称">
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item label="上传语音样本">
        <el-upload
          drag
          multiple
          :auto-upload="false"
          :file-list="form.samples"
        >
          <el-icon><upload-filled /></el-icon>
          <div>拖拽或点击上传音频</div>
        </el-upload>
      </el-form-item>
      <el-button type="primary" @click="submit">提交训练</el-button>
    </el-form>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'

const form = reactive({
  name: '',
  samples: []
})

function submit() {
  console.log('提交音色训练', form)
}
</script>

<style scoped>
.clone-wizard {
  padding: 24px;
  max-width: 600px;
}
</style>
