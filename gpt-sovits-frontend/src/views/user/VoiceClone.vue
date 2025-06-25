<template>
  <div class="clone-container">
    <header class="page-header">
      <h2>🎙️ 音色克隆</h2>
      <p>上传你的语音样本，后台将自动训练专属音色模型。</p>
    </header>

    <!-- 上传卡片 -->
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
          sub-title="任务已提交训练队列，请在下方查看进度。"
        />
      </div>
    </el-card>

    <!-- 历史任务状态展示 -->
    <div class="task-list-title">我的克隆任务</div>
    <div class="task-list">
      <el-card
        v-for="task in tasks"
        :key="task.id"
        class="task-card"
        @click="goToTaskDetail(task)"
      >
        <div class="task-header">
          <div class="task-name">{{ task.name }}</div>
          <el-tag :type="statusTagType(task.status)">
            {{ statusText(task.status) }}
          </el-tag>
        </div>
        <div class="task-desc">{{ task.description }}</div>
        <el-progress :percentage="task.progress" :status="progressStatus(task.status)" />
      </el-card>
    </div>
  </div>
</template>

<script setup>  
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const uploaded = ref(false)

function handleUploadSuccess() {
  uploaded.value = true
}

function handleUploadError(err) {
  console.error('上传失败', err)
  ElMessage.error('上传失败，请重试')
}

// 假设从后端获取的任务数据（建议用接口替换）
const tasks = ref([
  {
    id: 1,
    name: '李白音色模型',
    description: '上传时间：2025-06-20 15:00',
    status: 'training', // queued, training, completed, failed
    progress: 45
  },
  {
    id: 2,
    name: 'AI小雅专属音色',
    description: '上传时间：2025-06-19 12:00',
    status: 'completed',
    progress: 100
  },
  {
    id: 3,
    name: '测试失败任务',
    description: '上传时间：2025-06-18 10:00',
    status: 'failed',
    progress: 0
  }
])

function goToTaskDetail(task) {
  router.push({ name: 'TaskDetail', query: { id: task.id } })
}

function statusText(status) {
  switch (status) {
    case 'queued': return '排队中'
    case 'training': return '训练中'
    case 'completed': return '已完成'
    case 'failed': return '失败'
    default: return '未知'
  }
}

function statusTagType(status) {
  switch (status) {
    case 'queued': return 'info'
    case 'training': return 'warning'
    case 'completed': return 'success'
    case 'failed': return 'danger'
    default: return 'info'
  }
}

function progressStatus(status) {
  switch (status) {
    case 'completed': return 'success'
    case 'failed': return 'exception'
    default: return 'active'
  }
}
</script>

<style scoped>
.clone-container {
  max-width: 960px;
  margin: 40px auto;
  padding: 24px;
}
.page-header {
  text-align: center;
  margin-bottom: 32px;
}
.upload-card {
  padding: 40px;
  border-radius: 12px;
  margin-bottom: 40px;
}
.upload-result {
  margin-top: 24px;
}
.task-list-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 16px;
}
.task-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.task-card {
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
}
.task-card:hover {
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.task-name {
  font-weight: 600;
  font-size: 16px;
}
.task-desc {
  font-size: 13px;
  color: #777;
  margin-bottom: 10px;
}
</style>