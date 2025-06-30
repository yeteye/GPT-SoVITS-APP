<!-- ./gpt-sovits-frontend/src/views/admin/ModelAudit.vue -->
<template>
  <div class="admin-page">
    <h2>音色模型审核</h2>

    <!-- 搜索过滤 -->
    <el-form :inline="true" class="search-bar" @submit.prevent>
      <el-form-item label="模型类型">
        <el-select v-model="filters.type" placeholder="全部" clearable style="width: 150px">
          <el-option label="官方" value="official" />
          <el-option label="用户训练" value="user_trained" />
        </el-select>
      </el-form-item>

      <el-form-item label="模型状态">
        <el-select v-model="filters.status" placeholder="全部" clearable style="width: 150px">
          <el-option label="已启用" value="active" />
          <el-option label="已禁用" value="inactive" />
        </el-select>
      </el-form-item>

      <el-form-item label="审核状态">
        <el-select v-model="filters.review_status" placeholder="全部" clearable style="width: 150px">
          <el-option label="待审核" value="pending" />
          <el-option label="已通过" value="approved" />
          <el-option label="已驳回" value="rejected" />
        </el-select>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="fetchModels">搜索</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-number">{{ stats.pending_review || 0 }}</div>
          <div class="stat-label">待审核</div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-number">{{ stats.approved_today || 0 }}</div>
          <div class="stat-label">今日已审核</div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-number">{{ stats.total || 0 }}</div>
          <div class="stat-label">总模型数</div>
        </div>
      </el-card>
    </div>

    <!-- 模型表格 -->
    <el-table :data="models" v-loading="loading" border style="width: 100%; margin-top: 20px;">
      <el-table-column prop="id" label="模型ID" width="120" />
      <el-table-column prop="name" label="模型名称" min-width="150" />
      <el-table-column label="创建者" width="200">
        <template #default="{ row }">
          <div v-if="row.owner">
            <div>{{ row.owner.username }}</div>
            <div class="text-gray-500 text-sm">{{ row.owner.email }}</div>
          </div>
          <span v-else class="text-gray-400">系统</span>
        </template>
      </el-table-column>
      <el-table-column prop="model_type" label="类型" width="100">
        <template #default="{ row }">
          <el-tag :type="row.model_type === 'official' ? 'success' : 'info'">
            {{ row.model_type === 'official' ? '官方' : '用户' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'danger'">
            {{ row.status === 'active' ? '已启用' : '已禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="review_status" label="审核状态" width="120">
        <template #default="{ row }">
          <el-tag :type="getReviewStatusType(row.review_status)" effect="dark">
            {{ getReviewStatusText(row.review_status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="150">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button type="success" size="small" @click="approve(row)" :disabled="row.review_status === 'approved'"
            :loading="reviewLoading[row.id]">
            通过
          </el-button>
          <el-button type="warning" size="small" @click="reject(row)" :disabled="row.review_status === 'rejected'"
            :loading="reviewLoading[row.id]">
            驳回
          </el-button>
          <el-button type="info" size="small" @click="viewDetail(row)">
            详情
          </el-button>
          <el-button type="primary" size="small" @click="validateModel(row)" :loading="validateLoading[row.id]">
            验证
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination layout="prev, pager, next, sizes, total" :total="pagination.total" :current-page="pagination.page"
        :page-size="pagination.per_page" :page-sizes="[10, 20, 50, 100]" @current-change="handlePageChange"
        @size-change="handlePageSizeChange" />
    </div>

    <!-- 审核对话框 -->
    <el-dialog v-model="reviewDialogVisible" :title="reviewAction === 'approve' ? '审核通过' : '审核驳回'" width="500px">
      <el-form :model="reviewForm" label-width="80px">
        <el-form-item label="模型名称">
          <span>{{ currentModel?.name }}</span>
        </el-form-item>
        <el-form-item label="审核意见" required>
          <el-input v-model="reviewForm.message" type="textarea" :rows="4"
            :placeholder="reviewAction === 'approve' ? '请输入通过理由（可选）' : '请输入驳回理由'" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmReview" :loading="confirmLoading">
          确认{{ reviewAction === 'approve' ? '通过' : '驳回' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 模型详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="模型详情" width="800px">
      <div v-if="currentModel" class="model-detail">
        <el-descriptions border column="2">
          <el-descriptions-item label="模型ID">{{ currentModel.id }}</el-descriptions-item>
          <el-descriptions-item label="模型名称">{{ currentModel.name }}</el-descriptions-item>
          <el-descriptions-item label="类型">
            <el-tag :type="currentModel.model_type === 'official' ? 'success' : 'info'">
              {{ currentModel.model_type === 'official' ? '官方' : '用户' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentModel.status === 'active' ? 'success' : 'danger'">
              {{ currentModel.status === 'active' ? '已启用' : '已禁用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="审核状态">
            <el-tag :type="getReviewStatusType(currentModel.review_status)">
              {{ getReviewStatusText(currentModel.review_status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="质量评分">{{ currentModel.quality_score || 0 }}</el-descriptions-item>
          <el-descriptions-item label="使用次数">{{ currentModel.usage_count || 0 }}</el-descriptions-item>
          <el-descriptions-item label="下载次数">{{ currentModel.download_count || 0 }}</el-descriptions-item>
          <el-descriptions-item label="创建时间" span="2">{{ formatTime(currentModel.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间" span="2">{{ formatTime(currentModel.updated_at) }}</el-descriptions-item>
          <el-descriptions-item label="描述" span="2">{{ currentModel.description || '暂无描述' }}</el-descriptions-item>
        </el-descriptions>

        <div class="mt-4">
          <h4>支持的语言</h4>
          <div class="tags-container">
            <el-tag v-for="lang in currentModel.supported_languages" :key="lang" class="mr-2 mb-2">
              {{ getLanguageText(lang) }}
            </el-tag>
          </div>
        </div>

        <div class="mt-4">
          <h4>支持的情感</h4>
          <div class="tags-container">
            <el-tag v-for="emotion in currentModel.supported_emotions" :key="emotion" type="success" class="mr-2 mb-2">
              {{ getEmotionText(emotion) }}
            </el-tag>
          </div>
        </div>

        <div class="mt-4" v-if="currentModel.tags && currentModel.tags.length > 0">
          <h4>标签</h4>
          <div class="tags-container">
            <el-tag v-for="tag in currentModel.tags" :key="tag.id" :color="tag.color" class="mr-2 mb-2">
              {{ tag.name }}
            </el-tag>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

const models = ref([])
const loading = ref(false)
const reviewLoading = ref({})
const validateLoading = ref({})
const confirmLoading = ref(false)

const filters = ref({
  type: null,
  status: null,
  review_status: null
})

const pagination = ref({
  page: 1,
  per_page: 20,
  total: 0
})

const stats = ref({
  pending_review: 0,
  approved_today: 0,
  total: 0
})

// 审核相关
const reviewDialogVisible = ref(false)
const reviewAction = ref('approve') // 'approve' or 'reject'
const currentModel = ref(null)
const reviewForm = reactive({
  message: ''
})

// 详情对话框
const detailDialogVisible = ref(false)

// 获取模型列表
async function fetchModels() {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      per_page: pagination.value.per_page,
      type: filters.value.type,
      status: filters.value.status,
      review_status: filters.value.review_status
    }

    // 移除空值参数
    Object.keys(params).forEach(key => {
      if (params[key] === null || params[key] === undefined || params[key] === '') {
        delete params[key]
      }
    })

    const res = await request.get('/admin/models', { params })

    // 添加调试日志
    console.log('API响应数据:', res.data)
    console.log('响应状态:', res.status)

    // 根据实际API响应结构调整数据处理
    if (res.data) {
      let modelsData = []
      let totalCount = 0

      // 检查不同的响应格式
      if (res.data.success && res.data.data) {
        // 标准格式：{ success: true, data: { models: [], pagination: {} } }
        modelsData = res.data.data.models || []
        totalCount = res.data.data.pagination?.total || 0
        console.log('使用标准格式解析数据')
      } else if (res.data.models && res.data.pagination) {
        // 直接格式：{ models: [], pagination: {} }
        modelsData = res.data.models || []
        totalCount = res.data.pagination.total || 0
        console.log('使用直接格式解析数据')
      } else {
        // 其他格式
        modelsData = []
        totalCount = 0
        console.log('未识别的数据格式，设置为空')
      }

      models.value = modelsData
      pagination.value.total = totalCount

      console.log('解析后的模型数据:', models.value)
      console.log('总数:', pagination.value.total)
    } else {
      throw new Error('API返回数据为空')
    }
  } catch (err) {
    console.error('获取模型列表失败:', err)
    console.error('错误详情:', err?.response?.data)
    ElMessage.error(err?.response?.data?.message || err.message || '获取模型列表失败')
  } finally {
    loading.value = false
  }
}

// 获取统计信息
async function fetchStats() {
  try {
    const res = await request.get('/admin/statistics')

    // 添加调试日志
    console.log('统计API响应:', res.data)
    console.log('统计响应状态:', res.status)

    if (res.data) {
      // 根据实际响应结构调整
      if (res.data.models) {
        // 如果有 models 字段，说明是 { models: {...}, users: {...}, ... } 格式
        stats.value = res.data.models || {}
      } else if (res.data.data && res.data.data.models) {
        // 如果是 { success: true, data: { models: {...} } } 格式
        stats.value = res.data.data.models || {}
      } else {
        // 直接返回统计数据
        stats.value = res.data || {}
      }

      console.log('解析后的统计数据:', stats.value)
    }
  } catch (err) {
    console.error('获取统计信息失败:', err)
    console.error('统计错误详情:', err?.response?.data)
    // 设置默认值，避免页面显示错误
    stats.value = {
      pending_review: 0,
      approved_today: 0,
      total: 0
    }
  }
}

// 审核操作
function approve(model) {
  reviewAction.value = 'approve'
  currentModel.value = model
  reviewForm.message = ''
  reviewDialogVisible.value = true
}

function reject(model) {
  reviewAction.value = 'reject'
  currentModel.value = model
  reviewForm.message = ''
  reviewDialogVisible.value = true
}

// 确认审核
async function confirmReview() {
  if (reviewAction.value === 'reject' && !reviewForm.message.trim()) {
    ElMessage.warning('驳回时必须填写驳回理由')
    return
  }

  confirmLoading.value = true
  try {
    const status = reviewAction.value === 'approve' ? 'approved' : 'rejected'
    const res = await request.post(`/admin/models/${currentModel.value.id}/review`, {
      status: status,
      message: reviewForm.message.trim()
    })

    console.log('审核API响应:', res.data)

    // 根据实际API响应格式处理
    if (res.data) {
      ElMessage.success(`模型${reviewAction.value === 'approve' ? '通过' : '驳回'}成功`)
      reviewDialogVisible.value = false

      // 更新本地数据
      const modelIndex = models.value.findIndex(m => m.id === currentModel.value.id)
      if (modelIndex !== -1) {
        // 检查不同的数据结构
        let updatedModel = null

        if (res.data.data && res.data.data.model) {
          // 标准格式：{ success: true, data: { model: {...} } }
          updatedModel = res.data.data.model
        } else if (res.data.model) {
          // 直接格式：{ model: {...} }
          updatedModel = res.data.model
        }

        if (updatedModel) {
          // 使用返回的完整模型数据更新
          models.value[modelIndex] = updatedModel
          console.log('使用完整模型数据更新列表')
        } else {
          // 否则只更新审核状态
          models.value[modelIndex].review_status = status
          console.log('只更新审核状态')
        }
      }

      // 刷新统计信息
      fetchStats()
    } else {
      throw new Error('API返回数据为空')
    }
  } catch (err) {
    console.error('审核失败:', err)
    console.error('审核错误详情:', err?.response?.data)
    ElMessage.error(err?.response?.data?.message || err.message || '审核失败')
  } finally {
    confirmLoading.value = false
  }
}

// 查看详情
function viewDetail(model) {
  currentModel.value = model
  detailDialogVisible.value = true
}

// 验证模型
async function validateModel(model) {
  try {
    await ElMessageBox.confirm('确定要验证此模型的文件有效性吗？', '确认验证', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    })

    validateLoading.value[model.id] = true

    const res = await request.post(`/admin/models/${model.id}/validate-files`)

    console.log('验证API响应:', res.data)

    // 兼容不同的响应格式
    if (res.data && (res.data.success !== false)) {
      ElMessage.success('模型验证成功')
    } else {
      throw new Error(res.data?.message || '验证失败')
    }
  } catch (err) {
    if (err !== 'cancel') {
      console.error('模型验证失败:', err)
      console.error('验证错误详情:', err?.response?.data)
      ElMessage.error(err?.response?.data?.message || err.message || '模型验证失败')
    }
  } finally {
    validateLoading.value[model.id] = false
  }
}

// 工具函数
function getReviewStatusType(status) {
  switch (status) {
    case 'pending': return 'warning'
    case 'approved': return 'success'
    case 'rejected': return 'danger'
    default: return 'info'
  }
}

function getReviewStatusText(status) {
  switch (status) {
    case 'pending': return '待审核'
    case 'approved': return '已通过'
    case 'rejected': return '已驳回'
    default: return '未知'
  }
}

function getLanguageText(lang) {
  const langMap = {
    'zh-CN': '中文',
    'en-US': '英文',
    'ja-JP': '日语'
  }
  return langMap[lang] || lang
}

function getEmotionText(emotion) {
  const emotionMap = {
    'neutral': '自然',
    'happy': '快乐',
    'sad': '悲伤',
    'angry': '愤怒',
    'surprised': '惊讶'
  }
  return emotionMap[emotion] || emotion
}

function formatTime(timeString) {
  if (!timeString) return ''

  const date = new Date(timeString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  })
}

function handlePageChange(page) {
  pagination.value.page = page
  fetchModels()
}

function handlePageSizeChange(size) {
  pagination.value.per_page = size
  pagination.value.page = 1
  fetchModels()
}

function resetFilters() {
  filters.value = { type: null, status: null, review_status: null }
  pagination.value.page = 1
  fetchModels()
}

onMounted(() => {
  fetchModels()
  fetchStats()
})
</script>

<style scoped>
.admin-page {
  padding: 20px;
}

.search-bar {
  margin-bottom: 20px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-content {
  padding: 20px;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.model-detail h4 {
  margin: 16px 0 8px 0;
  color: #303133;
  font-size: 16px;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.text-gray-500 {
  color: #6b7280;
}

.text-gray-400 {
  color: #9ca3af;
}

.text-sm {
  font-size: 12px;
}

.mr-2 {
  margin-right: 8px;
}

.mb-2 {
  margin-bottom: 8px;
}

.mt-4 {
  margin-top: 16px;
}

:deep(.el-table .cell) {
  word-break: break-word;
}

:deep(.el-descriptions__label) {
  font-weight: bold;
}
</style>