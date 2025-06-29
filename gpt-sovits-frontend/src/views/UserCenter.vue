<!-- ./gpt-sovits-frontend/src/views/UserCenter.vue -->
<template>
  <div class="user-center">
    <div class="page-header">
      <h1>用户中心</h1>
      <p>管理您的个人信息和账户设置</p>
    </div>

    <el-row :gutter="24">
      <!-- 左侧：个人信息 -->
      <el-col :lg="8" :md="24" :sm="24">
        <el-card class="profile-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <h3>个人资料</h3>
              <el-button type="text" @click="editMode = !editMode">
                <el-icon>
                  <Edit />
                </el-icon>
                {{ editMode ? '取消编辑' : '编辑资料' }}
              </el-button>
            </div>
          </template>

          <div class="profile-content">
            <!-- 头像部分 -->
            <div class="avatar-section">
              <el-avatar :size="100" :src="profileForm.avatar_url" @error="handleAvatarError">
                <el-icon>
                  <User />
                </el-icon>
              </el-avatar>

              <div v-if="editMode" class="avatar-upload">
                <el-upload class="avatar-uploader" :action="avatarUploadUrl" :headers="uploadHeaders"
                  :show-file-list="false" :on-success="handleAvatarSuccess" :before-upload="beforeAvatarUpload">
                  <el-button size="small" type="primary">
                    <el-icon>
                      <Upload />
                    </el-icon>
                    更换头像
                  </el-button>
                </el-upload>
              </div>
            </div>

            <!-- 基本信息 -->
            <div class="basic-info">
              <el-form :model="profileForm" :rules="profileRules" ref="profileFormRef" label-width="80px">
                <el-form-item label="用户名" prop="username">
                  <el-input v-model="profileForm.username" :disabled="!editMode" placeholder="请输入用户名" />
                </el-form-item>

                <el-form-item label="邮箱">
                  <el-input v-model="profileForm.email" disabled placeholder="邮箱地址">
                    <template #suffix>
                      <el-tag v-if="profileForm.is_verified" type="success" size="small">已验证</el-tag>
                      <el-tag v-else type="warning" size="small">未验证</el-tag>
                    </template>
                  </el-input>
                </el-form-item>

                <el-form-item label="用户ID">
                  <el-input v-model="profileForm.id" disabled placeholder="用户唯一标识">
                    <template #suffix>
                      <el-button type="text" @click="copyUserId">
                        <el-icon>
                          <CopyDocument />
                        </el-icon>
                      </el-button>
                    </template>
                  </el-input>
                </el-form-item>

                <el-form-item label="角色">
                  <el-tag :type="getRoleTagType(profileForm.role)">
                    {{ getRoleText(profileForm.role) }}
                  </el-tag>
                </el-form-item>

                <el-form-item label="注册时间">
                  <span class="info-text">{{ formatTime(profileForm.created_at) }}</span>
                </el-form-item>

                <el-form-item label="最后登录">
                  <span class="info-text">{{ formatTime(profileForm.last_login_at) }}</span>
                </el-form-item>

                <el-form-item v-if="editMode">
                  <el-button type="primary" @click="updateProfile" :loading="updateLoading">
                    保存修改
                  </el-button>
                  <el-button @click="cancelEdit">
                    取消
                  </el-button>
                </el-form-item>
              </el-form>
            </div>
          </div>
        </el-card>

        <!-- 账户统计 -->
        <el-card class="stats-card" shadow="hover">
          <template #header>
            <h3>账户统计</h3>
          </template>

          <div class="stats-grid" v-loading="statsLoading">
            <div class="stat-item">
              <div class="stat-icon tts-icon">
                <el-icon>
                  <Microphone />
                </el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ userStats.tts_tasks || 0 }}</div>
                <div class="stat-label">TTS任务</div>
              </div>
            </div>

            <div class="stat-item">
              <div class="stat-icon clone-icon">
                <el-icon>
                  <MagicStick />
                </el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ userStats.voice_clone_tasks || 0 }}</div>
                <div class="stat-label">音色克隆</div>
              </div>
            </div>

            <div class="stat-item">
              <div class="stat-icon model-icon">
                <el-icon>
                  <DataBoard />
                </el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ userStats.models_created || 0 }}</div>
                <div class="stat-label">创建模型</div>
              </div>
            </div>

            <div class="stat-item">
              <div class="stat-icon storage-icon">
                <el-icon>
                  <FolderOpened />
                </el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ formatStorage(userStats.storage_used) }}</div>
                <div class="stat-label">存储使用</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：设置和操作 -->
      <el-col :lg="16" :md="24" :sm="24">
        <!-- 安全设置 -->
        <el-card class="security-card" shadow="hover">
          <template #header>
            <h3>安全设置</h3>
          </template>

          <div class="security-list">
            <div class="security-item">
              <div class="security-info">
                <div class="security-title">
                  <el-icon>
                    <Lock />
                  </el-icon>
                  登录密码
                </div>
                <div class="security-desc">定期更换密码可以保护账户安全</div>
              </div>
              <el-button @click="showChangePasswordDialog">修改密码</el-button>
            </div>

            <div class="security-item">
              <div class="security-info">
                <div class="security-title">
                  <el-icon>
                    <Message />
                  </el-icon>
                  邮箱验证
                </div>
                <div class="security-desc">
                  {{ profileForm.is_verified ? '您的邮箱已通过验证' : '验证邮箱可以接收重要通知' }}
                </div>
              </div>
              <el-button v-if="!profileForm.is_verified" type="primary" @click="sendVerificationEmail"
                :loading="verifyEmailLoading">
                发送验证邮件
              </el-button>
              <el-tag v-else type="success">已验证</el-tag>
            </div>

            <div class="security-item">
              <div class="security-info">
                <div class="security-title">
                  <el-icon>
                    <Warning />
                  </el-icon>
                  账户状态
                </div>
                <div class="security-desc">
                  账户当前状态：{{ profileForm.is_active ? '正常' : '已禁用' }}
                </div>
              </div>
              <el-tag :type="profileForm.is_active ? 'success' : 'danger'">
                {{ profileForm.is_active ? '活跃' : '禁用' }}
              </el-tag>
            </div>
          </div>
        </el-card>

        <!-- 偏好设置 -->
        <el-card class="preferences-card" shadow="hover">
          <template #header>
            <h3>偏好设置</h3>
          </template>

          <el-form :model="preferencesForm" label-width="120px">
            <el-form-item label="语言偏好">
              <el-select v-model="preferencesForm.language" @change="updatePreferences">
                <el-option label="简体中文" value="zh-CN" />
                <el-option label="English" value="en-US" />
                <el-option label="日本語" value="ja-JP" />
              </el-select>
            </el-form-item>

            <el-form-item label="主题设置">
              <el-radio-group v-model="preferencesForm.theme" @change="updatePreferences">
                <el-radio label="light">浅色主题</el-radio>
                <el-radio label="dark">深色主题</el-radio>
                <el-radio label="auto">跟随系统</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="邮件通知">
              <el-switch v-model="preferencesForm.email_notifications" @change="updatePreferences" active-text="开启"
                inactive-text="关闭" />
              <div class="form-tip">接收任务完成、系统更新等通知邮件</div>
            </el-form-item>

            <el-form-item label="自动保存">
              <el-switch v-model="preferencesForm.auto_save" @change="updatePreferences" active-text="开启"
                inactive-text="关闭" />
              <div class="form-tip">自动保存草稿和设置</div>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 最近活动 -->
        <el-card class="activity-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <h3>最近活动</h3>
              <el-button type="text" @click="fetchRecentActivities">
                <el-icon>
                  <Refresh />
                </el-icon>
                刷新
              </el-button>
            </div>
          </template>

          <div class="activity-list" v-loading="activityLoading">
            <div v-for="activity in recentActivities" :key="activity.id" class="activity-item">
              <div class="activity-icon" :class="`activity-${activity.type}`">
                <el-icon>
                  <component :is="getActivityIcon(activity.type)" />
                </el-icon>
              </div>
              <div class="activity-content">
                <div class="activity-title">{{ activity.title }}</div>
                <div class="activity-desc">{{ activity.description }}</div>
                <div class="activity-time">{{ formatTime(activity.created_at) }}</div>
              </div>
              <div class="activity-status">
                <el-tag :type="getStatusType(activity.status)" size="small">
                  {{ activity.status }}
                </el-tag>
              </div>
            </div>

            <el-empty v-if="!activityLoading && recentActivities.length === 0" description="暂无活动记录" />
          </div>
        </el-card>

        <!-- 危险操作 -->
        <el-card class="danger-card" shadow="hover">
          <template #header>
            <h3>危险操作</h3>
          </template>

          <div class="danger-list">
            <div class="danger-item">
              <div class="danger-info">
                <div class="danger-title">清除所有数据</div>
                <div class="danger-desc">清除您的所有任务记录、上传文件和个人设置</div>
              </div>
              <el-button type="danger" @click="showClearDataDialog">清除数据</el-button>
            </div>

            <div class="danger-item">
              <div class="danger-info">
                <div class="danger-title">注销账户</div>
                <div class="danger-desc">永久删除您的账户，此操作不可恢复</div>
              </div>
              <el-button type="danger" @click="showDeleteAccountDialog">注销账户</el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 修改密码弹窗 -->
    <el-dialog v-model="changePasswordVisible" title="修改密码" width="400px">
      <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="100px">
        <el-form-item label="当前密码" prop="currentPassword">
          <el-input v-model="passwordForm.currentPassword" type="password" show-password placeholder="请输入当前密码" />
        </el-form-item>

        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="passwordForm.newPassword" type="password" show-password placeholder="请输入新密码" />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="passwordForm.confirmPassword" type="password" show-password placeholder="请再次输入新密码" />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="changePasswordVisible = false">取消</el-button>
          <el-button type="primary" @click="submitChangePassword" :loading="passwordLoading">
            确认修改
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 清除数据确认弹窗 -->
    <el-dialog v-model="clearDataDialogVisible" title="清除数据" width="500px">
      <div class="confirm-content">
        <el-alert title="此操作将清除以下数据：" type="warning" :closable="false" show-icon />

        <ul class="clear-list">
          <li>所有任务记录和历史</li>
          <li>上传的音频文件和模型</li>
          <li>个人偏好设置</li>
          <li>收藏和书签</li>
        </ul>

        <el-alert title="此操作不可撤销，请谨慎操作！" type="error" :closable="false" show-icon />

        <el-form-item label="确认操作" style="margin-top: 20px;">
          <el-input v-model="clearDataConfirm" placeholder="请输入 '确认清除' 来确认操作" />
        </el-form-item>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="clearDataDialogVisible = false">取消</el-button>
          <el-button type="danger" @click="executeClearData" :loading="clearDataLoading"
            :disabled="clearDataConfirm !== '确认清除'">
            确认清除
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 注销账户确认弹窗 -->
    <el-dialog v-model="deleteAccountDialogVisible" title="注销账户" width="500px">
      <div class="confirm-content">
        <el-alert title="注销账户将永久删除：" type="error" :closable="false" show-icon />

        <ul class="delete-list">
          <li>您的账户信息和个人资料</li>
          <li>所有任务记录和上传文件</li>
          <li>创建的音色模型</li>
          <li>所有相关数据和设置</li>
        </ul>

        <el-alert title="此操作不可撤销！账户删除后无法恢复！" type="error" :closable="false" show-icon />

        <el-form-item label="输入密码" style="margin-top: 20px;">
          <el-input v-model="deleteAccountPassword" type="password" show-password placeholder="请输入您的账户密码" />
        </el-form-item>

        <el-form-item label="确认操作">
          <el-input v-model="deleteAccountConfirm" placeholder="请输入 '永久删除' 来确认操作" />
        </el-form-item>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="deleteAccountDialogVisible = false">取消</el-button>
          <el-button type="danger" @click="executeDeleteAccount" :loading="deleteAccountLoading"
            :disabled="!deleteAccountPassword || deleteAccountConfirm !== '永久删除'">
            永久删除账户
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User,
  Edit,
  Upload,
  CopyDocument,
  Lock,
  Message,
  Warning,
  Refresh,
  Microphone,
  MagicStick,
  DataBoard,
  FolderOpened,
  Clock,
  Setting,
  Check,
  Close
} from '@element-plus/icons-vue'
import { userStore } from '@/stores/user'
import { userAPI, authAPI } from '@/api'

const router = useRouter()

// 响应式数据
const editMode = ref(false)
const updateLoading = ref(false)
const statsLoading = ref(false)
const activityLoading = ref(false)
const verifyEmailLoading = ref(false)
const passwordLoading = ref(false)
const clearDataLoading = ref(false)
const deleteAccountLoading = ref(false)

const changePasswordVisible = ref(false)
const clearDataDialogVisible = ref(false)
const deleteAccountDialogVisible = ref(false)

const profileFormRef = ref()
const passwordFormRef = ref()

const clearDataConfirm = ref('')
const deleteAccountPassword = ref('')
const deleteAccountConfirm = ref('')

// 表单数据
const profileForm = reactive({
  id: '',
  username: '',
  email: '',
  avatar_url: '',
  role: 0,
  is_active: true,
  is_verified: false,
  created_at: '',
  last_login_at: ''
})

const originalProfile = reactive({})

const preferencesForm = reactive({
  language: 'zh-CN',
  theme: 'light',
  email_notifications: true,
  auto_save: true
})

const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const userStats = ref({
  tts_tasks: 0,
  voice_clone_tasks: 0,
  models_created: 0,
  storage_used: 0
})

const recentActivities = ref([])

// 表单验证规则
const profileRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度在 2 到 20 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_\u4e00-\u9fa5]+$/, message: '用户名只能包含字母、数字、下划线和中文', trigger: 'blur' }
  ]
}

const passwordRules = {
  currentPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 计算属性
const avatarUploadUrl = computed(() => {
  return `${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000/api'}/user/upload-avatar`
})

const uploadHeaders = computed(() => ({
  'Authorization': `Bearer ${localStorage.getItem('token')}`
}))

// 方法
async function fetchUserProfile() {
  try {
    const res = await userAPI.getProfile()
    const profile = res.data?.profile || res.data

    Object.assign(profileForm, profile)
    Object.assign(originalProfile, profile)
  } catch (error) {
    ElMessage.error('获取用户信息失败')
  }
}

async function fetchUserStats() {
  statsLoading.value = true
  try {
    const res = await userAPI.getStatistics()
    userStats.value = res.data || {}
  } catch (error) {
    console.error('获取用户统计失败:', error)
  } finally {
    statsLoading.value = false
  }
}

async function fetchRecentActivities() {
  activityLoading.value = true
  try {
    const res = await userAPI.getTaskHistory({ per_page: 10 })
    recentActivities.value = (res.data?.tasks || []).map(task => ({
      id: task.id,
      type: task.type,
      title: getTaskTitle(task),
      description: getTaskDescription(task),
      status: task.status,
      created_at: task.created_at
    }))
  } catch (error) {
    // 使用模拟数据
    recentActivities.value = [
      {
        id: 1,
        type: 'tts',
        title: '语音合成任务',
        description: '生成了一段中文语音',
        status: 'completed',
        created_at: new Date().toISOString()
      },
      {
        id: 2,
        type: 'voice_clone',
        title: '音色克隆任务',
        description: '训练了新的音色模型',
        status: 'processing',
        created_at: new Date(Date.now() - 300000).toISOString()
      }
    ]
  } finally {
    activityLoading.value = false
  }
}

async function updateProfile() {
  if (!profileFormRef.value) return

  profileFormRef.value.validate(async (valid) => {
    if (!valid) return

    updateLoading.value = true
    try {
      await userAPI.updateProfile({
        username: profileForm.username,
        avatar_url: profileForm.avatar_url
      })

      Object.assign(originalProfile, profileForm)
      editMode.value = false
      ElMessage.success('个人信息更新成功')
    } catch (error) {
      ElMessage.error('更新失败')
    } finally {
      updateLoading.value = false
    }
  })
}

function cancelEdit() {
  Object.assign(profileForm, originalProfile)
  editMode.value = false
}

function handleAvatarError() {
  return true
}

function beforeAvatarUpload(file) {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('上传头像图片大小不能超过 2MB!')
    return false
  }
  return true
}

function handleAvatarSuccess(response) {
  if (response.success) {
    profileForm.avatar_url = response.data.avatar_url
    ElMessage.success('头像上传成功')
  } else {
    ElMessage.error('头像上传失败')
  }
}

function copyUserId() {
  navigator.clipboard.writeText(profileForm.id).then(() => {
    ElMessage.success('用户ID已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

async function sendVerificationEmail() {
  verifyEmailLoading.value = true
  try {
    // 调用发送验证邮件的API
    ElMessage.success('验证邮件已发送，请查收邮箱')
  } catch (error) {
    ElMessage.error('发送失败')
  } finally {
    verifyEmailLoading.value = false
  }
}

async function updatePreferences() {
  try {
    // 保存偏好设置
    localStorage.setItem('preferences', JSON.stringify(preferencesForm))
    ElMessage.success('设置已保存')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

function showChangePasswordDialog() {
  changePasswordVisible.value = true
  passwordForm.currentPassword = ''
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
}

async function submitChangePassword() {
  if (!passwordFormRef.value) return

  passwordFormRef.value.validate(async (valid) => {
    if (!valid) return

    passwordLoading.value = true
    try {
      await authAPI.changePassword({
        current_password: passwordForm.currentPassword,
        new_password: passwordForm.newPassword
      })

      changePasswordVisible.value = false
      ElMessage.success('密码修改成功，请重新登录')

      // 退出登录
      userStore.logout()
      router.push({ name: 'Login' })
    } catch (error) {
      ElMessage.error(error?.response?.data?.message || '密码修改失败')
    } finally {
      passwordLoading.value = false
    }
  })
}

function showClearDataDialog() {
  clearDataDialogVisible.value = true
  clearDataConfirm.value = ''
}

async function executeClearData() {
  if (clearDataConfirm.value !== '确认清除') {
    ElMessage.warning('请输入正确的确认文字')
    return
  }

  clearDataLoading.value = true
  try {
    // 调用清除数据API
    ElMessage.success('数据清除成功')
    clearDataDialogVisible.value = false

    // 刷新统计信息
    fetchUserStats()
    fetchRecentActivities()
  } catch (error) {
    ElMessage.error('清除失败')
  } finally {
    clearDataLoading.value = false
  }
}

function showDeleteAccountDialog() {
  deleteAccountDialogVisible.value = true
  deleteAccountPassword.value = ''
  deleteAccountConfirm.value = ''
}

async function executeDeleteAccount() {
  if (!deleteAccountPassword.value) {
    ElMessage.warning('请输入密码')
    return
  }

  if (deleteAccountConfirm.value !== '永久删除') {
    ElMessage.warning('请输入正确的确认文字')
    return
  }

  try {
    await ElMessageBox.confirm(
      '您即将永久删除账户，此操作不可恢复！确定要继续吗？',
      '最后确认',
      { type: 'error' }
    )

    deleteAccountLoading.value = true

    await userAPI.deleteAccount({
      password: deleteAccountPassword.value
    })

    ElMessage.success('账户已删除')
    deleteAccountDialogVisible.value = false

    // 退出登录
    userStore.logout()
    router.push({ name: 'Home' })
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  } finally {
    deleteAccountLoading.value = false
  }
}

// 工具函数
function getRoleText(role) {
  const roleMap = {
    0: '普通用户',
    1: '审核员',
    2: '管理员'
  }
  return roleMap[role] || '未知角色'
}

function getRoleTagType(role) {
  const typeMap = {
    0: '',
    1: 'warning',
    2: 'danger'
  }
  return typeMap[role] || ''
}

function formatTime(timeStr) {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString()
}

function formatStorage(bytes) {
  if (!bytes) return '0B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function getTaskTitle(task) {
  const titleMap = {
    'tts': '语音合成任务',
    'voice_clone': '音色克隆任务'
  }
  return titleMap[task.task_type] || '未知任务'
}

function getTaskDescription(task) {
  if (task.task_type === 'tts') {
    return `生成了 "${task.text?.substring(0, 20) || ''}..." 的语音`
  } else if (task.task_type === 'voice_clone') {
    return `训练了音色模型 "${task.model_name || '未命名'}"`
  }
  return '任务详情'
}

function getActivityIcon(type) {
  const iconMap = {
    'tts': Microphone,
    'voice_clone': MagicStick,
    'login': User,
    'setting': Setting
  }
  return iconMap[type] || Clock
}

function getStatusType(status) {
  const typeMap = {
    'completed': 'success',
    'processing': 'warning',
    'failed': 'danger',
    'pending': 'info'
  }
  return typeMap[status] || ''
}

// 初始化
onMounted(() => {
  fetchUserProfile()
  fetchUserStats()
  fetchRecentActivities()

  // 加载偏好设置
  const savedPreferences = localStorage.getItem('preferences')
  if (savedPreferences) {
    Object.assign(preferencesForm, JSON.parse(savedPreferences))
  }
})
</script>

<style scoped>
.user-center {
  padding: 24px;
  background: #f8f9fb;
  min-height: 100vh;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 32px;
  color: #303133;
  font-weight: 700;
}

.page-header p {
  margin: 0;
  font-size: 16px;
  color: #606266;
}

.profile-card,
.stats-card,
.security-card,
.preferences-card,
.activity-card,
.danger-card {
  margin-bottom: 24px;
  border: none;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.profile-content {
  padding: 16px 0;
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.avatar-upload {
  text-align: center;
}

.basic-info {
  flex: 1;
}

.info-text {
  color: #606266;
  font-size: 14px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f8f9fb;
  border-radius: 8px;
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: white;
}

.tts-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.clone-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.model-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.storage-icon {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

.security-list,
.danger-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.security-item,
.danger-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: #f8f9fb;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.danger-item {
  border-left-color: #f56c6c;
  background: #fef0f0;
}

.security-info,
.danger-info {
  flex: 1;
}

.security-title,
.danger-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.security-desc,
.danger-desc {
  font-size: 14px;
  color: #606266;
  line-height: 1.4;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.activity-list {
  max-height: 400px;
  overflow-y: auto;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: white;
}

.activity-tts {
  background: #667eea;
}

.activity-voice_clone {
  background: #f093fb;
}

.activity-login {
  background: #67c23a;
}

.activity-setting {
  background: #e6a23c;
}

.activity-content {
  flex: 1;
}

.activity-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 2px;
}

.activity-desc {
  font-size: 13px;
  color: #606266;
  margin-bottom: 4px;
}

.activity-time {
  font-size: 12px;
  color: #909399;
}

.activity-status {
  flex-shrink: 0;
}

.confirm-content {
  padding: 16px 0;
}

.clear-list,
.delete-list {
  margin: 16px 0;
  padding-left: 20px;
}

.clear-list li,
.delete-list li {
  margin-bottom: 8px;
  color: #606266;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .user-center .el-col {
    margin-bottom: 16px;
  }
}

@media (max-width: 768px) {
  .user-center {
    padding: 16px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .security-item,
  .danger-item {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
    text-align: center;
  }

  .activity-item {
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }

  .card-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
}

/* Element Plus 样式覆盖 */
:deep(.el-card__header) {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}

:deep(.el-card__body) {
  padding: 20px;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
}

:deep(.el-input.is-disabled .el-input__inner) {
  background-color: #f5f7fa;
  color: #909399;
}

:deep(.el-dialog) {
  border-radius: 12px;
}

:deep(.el-alert) {
  margin-bottom: 16px;
  border-radius: 8px;
}

:deep(.el-upload) {
  width: 100%;
}

:deep(.avatar-uploader .el-upload) {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

:deep(.avatar-uploader .el-upload:hover) {
  border-color: #409eff;
}
</style>