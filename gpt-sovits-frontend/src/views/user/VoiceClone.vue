<template>
  <div class="clone-container">
    <header class="page-header">
      <h2>🎙️ 音色克隆</h2>
      <p>上传你的语音样本，后台将自动训练专属音色模型。</p>
    </header>

    <el-card class="upload-card">
      <el-upload
        class="upload-demo"
        drag
        action="/api/upload-sample" 
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :show-file-list="false"
        accept="audio/*"
      >
        <i class="el-icon-upload"></i>
        <div class="el-upload__text">拖拽或点击上传音频文件</div>
        <div class="el-upload__tip">支持 wav/mp3/m4a 等格式，建议音频时长 ≥ 10 秒</div>
      </el-upload>

      <div v-if="uploaded" class="upload-result">
        <el-result
          icon="success"
          title="上传成功"
          sub-title="任务已提交训练队列，请耐心等待通知。"
        >
          <template #extra>
            <el-button type="primary" @click="goTaskHistory">查看任务记录</el-button>
          </template>
        </el-result>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
const router = useRouter()

const uploaded = ref(false)

function handleUploadSuccess(response) {
  // 模拟成功判断，真实可基于 response.code 判断
  uploaded.value = true
}

function handleUploadError(err) {
  console.error('上传失败', err)
  ElMessage.error('上传失败，请重试')
}

function goTaskHistory() {
  router.push({ name: 'TaskHistory' })
}
</script>

<style scoped>
.clone-container {
  max-width: 800px;
  margin: 40px auto;
  padding: 24px;
}
.page-header {
  text-align: center;
  margin-bottom: 32px;
}
.page-header h2 {
  font-size: 28px;
  margin-bottom: 8px;
}
.upload-card {
  padding: 40px;
  border-radius: 12px;
}
.upload-result {
  margin-top: 32px;
}
</style>
