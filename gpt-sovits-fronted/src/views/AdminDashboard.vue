<template>
  <el-container class="admin-dashboard">
    <el-header class="header">
      <h2>后台管理中心</h2>
    </el-header>
    <el-main>
      <el-row :gutter="20">
        <el-col :span="8">
          <el-card>
            <h3>用户管理</h3>
            <p>查看、搜索和禁用用户。</p>
            <el-button type="primary" @click="goUserManage">进入</el-button>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card>
            <h3>模型审核</h3>
            <p>审批新上传的音色模型。</p>
            <el-button type="warning" @click="goModelAudit">进入</el-button>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card>
            <h3>系统日志</h3>
            <p>查看系统操作记录和异常信息。</p>
            <el-button @click="goLog">进入</el-button>
          </el-card>
        </el-col>
      </el-row>
    </el-main>
  </el-container>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()

function goUserManage() {
  router.push({ name: 'UserManage' })
}
function goModelAudit() {
  router.push({ name: 'ModelAudit' })
}
function goLog() {
  router.push({ name: 'SystemLog' })
}
</script>

<style scoped>
.admin-dashboard {
  padding: 20px;
  background: #f4f6f8;
}
.header {
  background: #fff;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
</style>
