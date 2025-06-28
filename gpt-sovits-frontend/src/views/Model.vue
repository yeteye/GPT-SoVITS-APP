<!-- ./gpt-sovits-frontend/src/views/Model.vue -->
<template>
  <el-card class="voice-model-detail-card" v-loading="loading">
    <template #header>
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <span>音色模型详情</span>
        <el-button type="primary" @click="goBack">返回列表</el-button>
      </div>
    </template>

    <div v-if="model">
      <el-descriptions title="基本信息" :column="2" border size="small" style="margin-bottom: 20px;">
        <el-descriptions-item label="ID">{{ model.id }}</el-descriptions-item>
        <el-descriptions-item label="名称">{{ model.name }}</el-descriptions-item>
        <el-descriptions-item label="模型类型">{{ model.model_type }}</el-descriptions-item>
        <el-descriptions-item label="拥有者">
          {{ model.owner_name || model.owner_id || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag v-if="model.status" type="info">{{ model.status }}</el-tag>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="公开">
          <el-tag :type="model.is_public ? 'success' : 'warning'">
            {{ model.is_public ? '是' : '否' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="精选">
          <el-tag :type="model.is_featured ? 'success' : 'info'">
            {{ model.is_featured ? '是' : '否' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="质量评分">
          {{ model.quality_score != null ? model.quality_score : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="下载次数">
          {{ model.download_count != null ? model.download_count : 0 }}
        </el-descriptions-item>
        <el-descriptions-item label="使用次数">
          {{ model.usage_count != null ? model.usage_count : 0 }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDate(model.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">
          {{ formatDate(model.updated_at) }}
        </el-descriptions-item>
      </el-descriptions>

      <el-descriptions title="审核信息" :column="2" border size="small" style="margin-bottom: 20px;">
        <el-descriptions-item label="审核状态">
          {{ model.review_status || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="审核人">
          {{ model.reviewed_by || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="审核时间">
          {{ formatDate(model.reviewed_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="审核信息">
          <el-tooltip v-if="model.review_message && model.review_message.length > 30" class="item" effect="dark"
            :content="model.review_message" placement="top">
            {{ model.review_message.slice(0, 30) + '...' }}
          </el-tooltip>
          <span v-else>{{ model.review_message || '-' }}</span>
        </el-descriptions-item>
      </el-descriptions>

      <el-descriptions title="扩展属性" :column="1" border size="small" style="margin-bottom: 20px;">
        <el-descriptions-item label="描述">
          <div v-if="model.description">{{ model.description }}</div>
          <div v-else>-</div>
        </el-descriptions-item>
        <el-descriptions-item label="支持的情感">
          <div v-if="model.supported_emotions">
            <el-tag v-for="(emo, idx) in parseList(model.supported_emotions)" :key="idx" size="small"
              style="margin: 2px;">{{ emo }}</el-tag>
          </div>
          <div v-else>-</div>
        </el-descriptions-item>
        <el-descriptions-item label="支持的语言">
          <div v-if="model.supported_languages">
            <el-tag v-for="(lang, idx) in parseList(model.supported_languages)" :key="idx" size="small"
              style="margin: 2px;">{{ lang }}</el-tag>
          </div>
          <div v-else>-</div>
        </el-descriptions-item>
        <el-descriptions-item label="声音特征">
          <div v-if="model.voice_characteristics">
            <el-tag v-for="(vc, idx) in parseList(model.voice_characteristics)" :key="idx" size="small"
              style="margin: 2px;">{{ vc }}</el-tag>
          </div>
          <div v-else>-</div>
        </el-descriptions-item>
      </el-descriptions>

      <el-card shadow="hover" class="paths-card" style="margin-bottom: 20px;">
        <template #header>
          <span>路径与操作</span>
        </template>
        <div style="display: flex; flex-direction: column; gap: 8px;">
          <div>
            <strong>模型文件路径：</strong>
            <el-link v-if="model.model_path" :underline="false" @click="downloadFile(model.model_path)">{{
              truncatePath(model.model_path) }}</el-link>
            <span v-else>-</span>
          </div>
          <div>
            <strong>配置文件路径：</strong>
            <el-link v-if="model.config_path" :underline="false" @click="downloadFile(model.config_path)">{{
              truncatePath(model.config_path) }}</el-link>
            <span v-else>-</span>
          </div>
          <div>
            <strong>索引文件路径：</strong>
            <el-link v-if="model.index_path" :underline="false" @click="downloadFile(model.index_path)">{{
              truncatePath(model.index_path) }}</el-link>
            <span v-else>-</span>
          </div>
          <!-- 如果不需要可移除 downloadFile 相关逻辑 -->
        </div>
      </el-card>

      <!-- 若需要其他操作按钮，可在此添加 -->
      <div style="text-align: right;">
        <!-- 例如编辑或删除，仅当有权限时显示 -->
        <el-button v-if="canEdit" type="primary" @click="goEdit">编辑</el-button>
        <el-button v-if="canDelete" type="danger" @click="confirmDelete">删除</el-button>
      </div>
    </div>

    <div v-else-if="!loading" style="text-align: center; margin: 20px 0;">
      <span>未找到该模型或加载失败</span>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

const route = useRoute()
const router = useRouter()
const model = ref(null)
const loading = ref(false)

// 获取路由参数 id
const id = route.params.id

// 判断权限：这里只是示例，按实际业务逻辑修改
// 假设从 localStorage 或全局 store 中拿 user 信息
const userInfo = ref(null)
try {
  userInfo.value = JSON.parse(localStorage.getItem('user'))
} catch {
}
const canEdit = computed(() => {
  // 例如：创建者或管理员可以编辑
  return userInfo.value && (userInfo.value.role === 2 || userInfo.value.id === model.value?.owner_id)
})
const canDelete = computed(() => {
  // 例如：管理员可以删除
  return userInfo.value && userInfo.value.role === 2
})

// 格式化日期
function formatDate(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  if (isNaN(d)) return '-'
  return d.toLocaleString()
}

// 将可能以逗号、分号或空格分隔的字符串转为数组
function parseList(str) {
  // 依据后端格式，若 JSON 数组字符串可用 JSON.parse
  try {
    const arr = JSON.parse(str)
    if (Array.isArray(arr)) return arr
  } catch {
  }
  // 否则按常见分隔符拆分
  return str.split(/[,;，；\s]+/).filter(Boolean)
}

// 下载文件示例：可改为打开新窗口或调用后端下载接口
function downloadFile(path) {
  // 假设后端能够通过某 URL 下载，比如 /api/files?path=...
  // window.open 或者 request.get 返回 blob 等做下载
  window.open(path, '_blank')
}

// 跳转回列表
function goBack() {
  router.back()
}

// 编辑
function goEdit() {
  router.push({ name: 'VoiceModelEdit', params: { id } })
}

// 删除
function confirmDelete() {
  ElMessageBox.confirm(
    '确认要删除该模型吗？此操作不可恢复。',
    '提示',
    { type: 'warning' }
  ).then(async () => {
    try {
      await request.delete(`/models/${id}`)
      ElMessage.success('删除成功')
      goBack()
    } catch (err) {
      ElMessage.error(err?.response?.data?.message || '删除失败')
    }
  }).catch(() => {
    // 取消
  })
}

// 拉取模型详情
async function fetchModel() {
  loading.value = true
  try {
    const res = await request.get(`/models/${id}`)
    // 假设 res.data.data 是对象
    const data = res.data && res.data.data
    if (data) {
      model.value = data
    } else {
      model.value = null
      ElMessage.warning('未获取到模型详情')
    }
  } catch (err) {
    console.error(err)
    ElMessage.error(err?.response?.data?.message || '加载模型详情失败')
    model.value = null
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchModel()
})
</script>

<style scoped>
.voice-model-detail-card {
  padding: 16px;
}

/* 根据需要可调整描述列表和卡片样式 */
</style>
