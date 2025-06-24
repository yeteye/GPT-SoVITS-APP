<template>
  <div class="creator-center">
    <div class="creator-header">
      <img class="creator-avatar" src="@/assets/logo.svg" alt="avatar" />
      <div class="creator-info">
        <h2>创作者中心</h2>
        <p>欢迎上传和管理你的音频与音色模型，构建你的专属声音品牌。</p>
      </div>
    </div>

    <!-- 上传入口 -->
    <div class="upload-actions">
      <el-button type="primary" @click="uploadAudio">上传音频</el-button>
      <el-button type="success" @click="uploadModel">上传音色模型</el-button>
    </div>

    <!-- 我的音频 -->
    <section class="content-section">
      <h3>🎵 我的音频</h3>
      <el-table :data="audioList" style="width: 100%">
        <el-table-column prop="name" label="音频名称" />
        <el-table-column prop="duration" label="时长" width="100" />
        <el-table-column prop="upload_time" label="上传时间" width="180" />
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button type="text" @click="playAudio(scope.row)">播放</el-button>
            <el-button type="text" @click="deleteAudio(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <!-- 我的音色模型 -->
    <section class="content-section">
      <h3>🧬 我的音色模型</h3>
      <el-table :data="modelList" style="width: 100%">
        <el-table-column prop="name" label="模型名称" />
        <el-table-column prop="status" label="审核状态" width="120">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="upload_time" label="上传时间" width="180" />
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button type="text" @click="viewModel(scope.row)">查看</el-button>
            <el-button type="text" @click="deleteModel(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

// 示例数据
const audioList = ref([
  { name: '配音样本A', duration: '00:45', upload_time: '2025-06-24 10:00' },
  { name: '朗读作品B', duration: '01:12', upload_time: '2025-06-23 14:20' }
])

const modelList = ref([
  { name: '温柔女声V1', status: '审核中', upload_time: '2025-06-22 08:15' },
  { name: '少年音V2', status: '已通过', upload_time: '2025-06-21 17:30' }
])

// 状态标签颜色
const getStatusType = (status) => {
  switch (status) {
    case '已通过': return 'success'
    case '审核中': return 'warning'
    case '未通过': return 'danger'
    default: return ''
  }
}

// 操作函数占位
const uploadAudio = () => ElMessage.info('TODO: 上传音频')
const uploadModel = () => ElMessage.info('TODO: 上传模型')
const playAudio = (row) => ElMessage.info(`播放 ${row.name}`)
const deleteAudio = (row) => ElMessage.warning(`删除 ${row.name}`)
const viewModel = (row) => ElMessage.info(`查看 ${row.name}`)
const deleteModel = (row) => ElMessage.warning(`删除 ${row.name}`)
</script>

<style lang="css" scoped>
.creator-center {
  padding: 40px;
  background: #f9fafc;
}

.creator-header {
  display: flex;
  align-items: center;
  margin-bottom: 30px;
}

.creator-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  margin-right: 20px;
}

.creator-info h2 {
  margin: 0;
  font-size: 26px;
  font-weight: bold;
}

.upload-actions {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.content-section {
  background: #fff;
  padding: 24px;
  margin-top: 20px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
  border-radius: 8px;
}

.content-section h3 {
  margin-bottom: 16px;
}

</style>