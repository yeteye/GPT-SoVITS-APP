<template>
  <div class="my-voices">
    <h2>我的音色</h2>
    <el-table :data="models" style="width: 100%">
      <el-table-column prop="name" label="模型名称" />
      <el-table-column prop="status" label="状态" />
      <el-table-column label="操作" width="160">
        <template #default="scope">
          <el-button type="text" @click="preview(scope.row)">试听</el-button>
          <el-button type="text" @click="deleteModel(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
const models = [
  { name: '配音女声', status: '已部署' },
  { name: '旁白男声', status: '训练中' }
]

function preview(row) {
  console.log('试听模型', row)
}

function deleteModel(row) {
  console.log('删除模型', row)
}
</script>

<style scoped>
.my-voices {
  padding: 24px;
}
</style>
