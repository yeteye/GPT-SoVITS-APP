<template>
  <div class="admin-page">
    <h2>音色模型审核</h2>

    <!-- 搜索过滤 -->
    <el-form :inline="true" class="search-bar" @submit.prevent>
      <el-form-item label="模型类型">
        <el-select v-model="filters.type" placeholder="全部" clearable style="width: 150px">
          <el-option label="TTS" value="tts" />
          <el-option label="克隆" value="clone" />
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

    <!-- 模型表格 -->
    <el-table :data="models" v-loading="loading" border style="width: 100%; margin-top: 20px;">
      <el-table-column prop="id" label="模型ID" width="100" />
      <el-table-column prop="name" label="模型名称" />
      <el-table-column prop="creator" label="创建者邮箱" />
      <el-table-column prop="type" label="类型" width="100" />
      <el-table-column prop="status" label="状态" width="100" />
      <el-table-column prop="review_status" label="审核状态" width="120" />
      <el-table-column label="操作" width="240">
        <template #default="{ row }">
          <el-button type="success" size="small" @click="approve(row)">通过</el-button>
          <el-button type="warning" size="small" @click="reject(row)">驳回</el-button>
          <el-button type="info" size="small" @click="viewDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        layout="prev, pager, next, sizes, total"
        :total="pagination.total"
        :current-page="pagination.page"
        :page-size="pagination.per_page"
        :page-sizes="[10, 20, 50]"
        @current-change="handlePageChange"
        @size-change="handlePageSizeChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const models = ref([])
const loading = ref(false)

const filters = ref({
  type: null,
  status: null,
  review_status: null
})

const pagination = ref({
  page: 1,
  per_page: 10,
  total: 0
})

// 获取模型列表
function fetchModels() {
  loading.value = true
  request.get('/admin/models', {
    params: {
      page: pagination.value.page,
      per_page: pagination.value.per_page,
      type: filters.value.type,
      status: filters.value.status,
      review_status: filters.value.review_status
    }
  }).then(res => {
    models.value = res.data.models || res.data.data || []
    pagination.value.total = res.data.total || 0
  }).catch(err => {
    ElMessage.error(err?.response?.data?.message || '获取模型列表失败')
  }).finally(() => {
    loading.value = false
  })
}

// 操作
function approve(model) {
  console.log('审核通过:', model)
  // TODO: request.post('/admin/models/approve', { id: model.id })
}
function reject(model) {
  console.log('审核驳回:', model)
  // TODO: request.post('/admin/models/reject', { id: model.id })
}
function viewDetail(model) {
  console.log('查看详情:', model)
  // TODO: 跳转或弹窗显示详情
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

onMounted(fetchModels)
</script>

<style scoped>
.admin-page {
  padding: 20px;
}
.search-bar {
  margin-bottom: 10px;
}
.pagination {
  margin-top: 20px;
  text-align: right;
}
</style>
