<!-- ./gpt-sovits-frontend/src/views/WatermarkManagement.vue -->
<template>
    <div class="watermark-management">
        <div class="page-header">
            <div class="header-content">
                <div class="header-text">
                    <h1>🔐 水印检查</h1>
                    <p>检测音频是否由AI模型生成，保护您的知识产权</p>
                </div>
                <div class="header-actions">
                    <el-button type="primary" @click="showEmbedDialog">
                        <el-icon>
                            <Plus />
                        </el-icon>
                        嵌入水印
                    </el-button>
                    <el-button @click="showVerifyDialog">
                        <el-icon>
                            <Search />
                        </el-icon>
                        验证水印
                    </el-button>
                </div>
            </div>
        </div>

        <!-- 功能卡片区域 -->
        <el-row :gutter="24" class="feature-cards">
            <el-col :span="12">
                <el-card class="feature-card verify-card" @click="showVerifyDialog">
                    <div class="card-content">
                        <div class="card-icon">
                            <el-icon>
                                <Search />
                            </el-icon>
                        </div>
                        <div class="card-info">
                            <h3>水印验证</h3>
                            <p>上传音频文件，检测是否包含AI生成水印</p>
                        </div>
                    </div>
                </el-card>
            </el-col>
            <el-col :span="12">
                <el-card class="feature-card embed-card" @click="showEmbedDialog">
                    <div class="card-content">
                        <div class="card-icon">
                            <el-icon>
                                <Lock />
                            </el-icon>
                        </div>
                        <div class="card-info">
                            <h3>水印嵌入</h3>
                            <p>为您的音频添加数字水印，保护版权</p>
                        </div>
                    </div>
                </el-card>
            </el-col>
        </el-row>

        <!-- 验证记录 -->
        <el-card class="verification-history" v-if="isLoggedIn">
            <template #header>
                <div class="card-header">
                    <h3>最近验证记录</h3>
                    <el-button type="text" @click="fetchVerificationLogs">
                        <el-icon>
                            <Refresh />
                        </el-icon>
                        刷新
                    </el-button>
                </div>
            </template>

            <el-table :data="verificationLogs" v-loading="logsLoading">
                <el-table-column prop="created_at" label="验证时间" width="180">
                    <template #default="{ row }">
                        {{ formatTime(row.created_at) }}
                    </template>
                </el-table-column>

                <el-table-column prop="filename" label="文件名" min-width="200" />

                <el-table-column label="验证结果" width="120">
                    <template #default="{ row }">
                        <el-tag :type="row.success ? 'success' : 'danger'">
                            {{ row.success ? '检测到水印' : '未检测到水印' }}
                        </el-tag>
                    </template>
                </el-table-column>

                <el-table-column prop="watermark_code" label="水印码" width="150">
                    <template #default="{ row }">
                        <span v-if="row.watermark_code">{{ row.watermark_code }}</span>
                        <span v-else class="no-watermark">-</span>
                    </template>
                </el-table-column>

                <el-table-column label="操作" width="120">
                    <template #default="{ row }">
                        <el-button type="text" size="small" @click="viewLogDetail(row)" v-if="row.success">
                            查看详情
                        </el-button>
                    </template>
                </el-table-column>
            </el-table>

            <el-empty v-if="!logsLoading && verificationLogs.length === 0" description="暂无验证记录" />
        </el-card>

        <!-- 验证水印弹窗 -->
        <el-dialog v-model="verifyDialogVisible" title="验证音频水印" width="600px">
            <div class="verify-section">
                <h4>上传音频文件</h4>
                <el-upload ref="verifyUploadRef" class="upload-demo" drag :auto-upload="false"
                    :on-change="handleVerifyFileChange" :limit="1" accept="audio/*" :before-upload="beforeUpload">
                    <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                    <div class="el-upload__text">拖拽音频文件到此处，或<em>点击上传</em></div>
                    <div class="el-upload__tip">支持 WAV、MP3、M4A 等格式，文件大小不超过50MB</div>
                </el-upload>
            </div>

            <!-- 验证结果 -->
            <div v-if="verifyResult" class="verify-result">
                <el-alert :type="verifyResult.success ? 'success' : 'info'"
                    :title="verifyResult.success ? '检测到AI生成水印' : '未检测到水印'"
                    :description="getVerifyResultDescription(verifyResult)" show-icon :closable="false" />

                <div v-if="verifyResult.success && verifyResult.data" class="watermark-info">
                    <h4>水印信息：</h4>
                    <el-descriptions :column="2" border size="small">
                        <el-descriptions-item label="水印码">
                            {{ verifyResult.data.watermark_code }}
                        </el-descriptions-item>
                        <el-descriptions-item label="创建者">
                            {{ verifyResult.data.creator_name || '未知' }}
                        </el-descriptions-item>
                        <el-descriptions-item label="模型信息">
                            {{ verifyResult.data.model_name || '未知模型' }}
                        </el-descriptions-item>
                        <el-descriptions-item label="生成时间">
                            {{ formatTime(verifyResult.data.created_at) }}
                        </el-descriptions-item>
                        <el-descriptions-item label="描述" :span="2">
                            {{ verifyResult.data.description || '无描述信息' }}
                        </el-descriptions-item>
                    </el-descriptions>
                </div>
            </div>

            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="closeVerifyDialog">关闭</el-button>
                    <el-button type="primary" @click="submitVerifyWatermark" :loading="verifyLoading"
                        :disabled="!verifyForm.audio_file">
                        开始验证
                    </el-button>
                </span>
            </template>
        </el-dialog>

        <!-- 嵌入水印弹窗 -->
        <el-dialog v-model="embedDialogVisible" title="嵌入音频水印" width="700px">
            <div v-if="!isLoggedIn" class="login-prompt">
                <el-alert title="需要登录" description="水印嵌入功能需要登录后使用" type="warning" show-icon :closable="false" />
                <div style="text-align: center; margin-top: 20px;">
                    <el-button type="primary" @click="goToLogin">立即登录</el-button>
                </div>
            </div>

            <el-form v-else :model="embedForm" :rules="embedRules" ref="embedFormRef" label-width="100px">
                <el-form-item label="选择模型" prop="model_id">
                    <el-select v-model="embedForm.model_id" placeholder="请选择模型" style="width: 100%"
                        :loading="modelsLoading">
                        <el-option v-for="model in availableModels" :key="model.id" :label="model.name"
                            :value="model.id" />
                    </el-select>
                </el-form-item>

                <el-form-item label="音频文件" prop="audio_file">
                    <el-upload ref="embedUploadRef" class="upload-demo" drag :auto-upload="false"
                        :on-change="handleEmbedFileChange" :limit="1" accept="audio/*" :before-upload="beforeUpload">
                        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                        <div class="el-upload__text">拖拽音频文件到此处，或<em>点击上传</em></div>
                        <div class="el-upload__tip">支持 WAV、MP3 等格式</div>
                    </el-upload>
                </el-form-item>

                <el-form-item label="码长度" prop="code_length">
                    <el-slider v-model="embedForm.code_length" :min="32" :max="256" :step="32" show-input
                        style="width: 100%" />
                    <div class="code-length-tip">较短的码长度处理更快，较长的码长度更安全</div>
                </el-form-item>

                <el-form-item label="描述" prop="description">
                    <el-input v-model="embedForm.description" type="textarea" :rows="3" placeholder="请描述此水印的用途..."
                        maxlength="200" show-word-limit />
                </el-form-item>
            </el-form>

            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="embedDialogVisible = false">取消</el-button>
                    <el-button v-if="isLoggedIn" type="primary" @click="submitEmbedWatermark" :loading="embedLoading">
                        嵌入水印
                    </el-button>
                </span>
            </template>
        </el-dialog>

        <!-- 验证日志详情弹窗 -->
        <el-dialog v-model="logDetailDialogVisible" title="验证详情" width="600px">
            <div v-if="currentLog">
                <el-descriptions :column="2" border>
                    <el-descriptions-item label="文件名">
                        {{ currentLog.filename }}
                    </el-descriptions-item>
                    <el-descriptions-item label="验证时间">
                        {{ formatTime(currentLog.created_at) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="验证结果">
                        <el-tag :type="currentLog.success ? 'success' : 'danger'">
                            {{ currentLog.success ? '检测到水印' : '未检测到水印' }}
                        </el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="水印码" v-if="currentLog.watermark_code">
                        {{ currentLog.watermark_code }}
                    </el-descriptions-item>
                    <el-descriptions-item label="创建者" v-if="currentLog.creator_name">
                        {{ currentLog.creator_name }}
                    </el-descriptions-item>
                    <el-descriptions-item label="模型信息" v-if="currentLog.model_name">
                        {{ currentLog.model_name }}
                    </el-descriptions-item>
                </el-descriptions>
            </div>
        </el-dialog>
    </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
    Plus,
    Search,
    Lock,
    Refresh,
    UploadFilled
} from '@element-plus/icons-vue'
import { watermarkAPI, ttsAPI } from '@/api'
import { userStore } from '@/stores/user'

const router = useRouter()

// 响应式数据
const verifyDialogVisible = ref(false)
const embedDialogVisible = ref(false)
const logDetailDialogVisible = ref(false)
const verifyLoading = ref(false)
const embedLoading = ref(false)
const logsLoading = ref(false)
const modelsLoading = ref(false)

const verifyUploadRef = ref()
const embedUploadRef = ref()
const embedFormRef = ref()

const verificationLogs = ref([])
const availableModels = ref([])
const verifyResult = ref(null)
const currentLog = ref(null)

// 计算属性
const isLoggedIn = computed(() => userStore.isLoggedIn.value)

// 表单数据
const verifyForm = reactive({
    audio_file: null
})

const embedForm = reactive({
    model_id: '',
    audio_file: null,
    code_length: 64,
    description: ''
})

// 表单验证规则
const embedRules = {
    model_id: [
        { required: true, message: '请选择模型', trigger: 'change' }
    ],
    audio_file: [
        { required: true, message: '请上传音频文件', trigger: 'change' }
    ],
    description: [
        { required: true, message: '请输入描述', trigger: 'blur' }
    ]
}

// 方法
function showVerifyDialog() {
    verifyDialogVisible.value = true
    resetVerifyForm()
}

function showEmbedDialog() {
    if (!isLoggedIn.value) {
        embedDialogVisible.value = true
        return
    }

    embedDialogVisible.value = true
    resetEmbedForm()
    fetchAvailableModels()
}

function closeVerifyDialog() {
    verifyDialogVisible.value = false
    verifyResult.value = null
}

function goToLogin() {
    embedDialogVisible.value = false
    router.push({ name: 'Login' })
}

async function fetchVerificationLogs() {
    if (!isLoggedIn.value) return

    logsLoading.value = true
    try {
        const res = await watermarkAPI.getVerificationLogs({ per_page: 10 })
        verificationLogs.value = res.data?.logs || []
    } catch (error) {
        console.error('获取验证日志失败:', error)
    } finally {
        logsLoading.value = false
    }
}

async function fetchAvailableModels() {
    modelsLoading.value = true
    try {
        const res = await ttsAPI.getAvailableModels({ per_page: 100 })
        availableModels.value = res.data?.models || []
    } catch (error) {
        console.error('获取模型列表失败:', error)
    } finally {
        modelsLoading.value = false
    }
}

function handleVerifyFileChange(file) {
    verifyForm.audio_file = file.raw
    verifyResult.value = null
}

function handleEmbedFileChange(file) {
    embedForm.audio_file = file.raw
}

function beforeUpload(file) {
    const isAudio = file.type.startsWith('audio/')
    const isLt50M = file.size / 1024 / 1024 < 50

    if (!isAudio) {
        ElMessage.error('只能上传音频文件!')
        return false
    }
    if (!isLt50M) {
        ElMessage.error('上传文件大小不能超过 50MB!')
        return false
    }
    return true
}

async function submitVerifyWatermark() {
    if (!verifyForm.audio_file) {
        ElMessage.warning('请先上传音频文件')
        return
    }

    verifyLoading.value = true
    try {
        const formData = new FormData()
        formData.append('audio_file', verifyForm.audio_file)

        const res = await watermarkAPI.verifyWatermark(formData)
        verifyResult.value = res.data

        // 如果已登录，刷新验证日志
        if (isLoggedIn.value) {
            fetchVerificationLogs()
        }

    } catch (error) {
        ElMessage.error(error?.response?.data?.message || '水印验证失败')
        verifyResult.value = {
            success: false,
            message: error?.response?.data?.message || '验证失败'
        }
    } finally {
        verifyLoading.value = false
    }
}

async function submitEmbedWatermark() {
    if (!embedFormRef.value) return

    embedFormRef.value.validate(async (valid) => {
        if (!valid) return

        embedLoading.value = true
        try {
            const formData = new FormData()
            formData.append('audio_file', embedForm.audio_file)
            formData.append('model_id', embedForm.model_id)
            formData.append('code_length', embedForm.code_length.toString())
            formData.append('description', embedForm.description)

            const res = await watermarkAPI.embedWatermark(formData)

            ElMessage.success('水印嵌入成功')
            embedDialogVisible.value = false

            // 刷新验证日志
            fetchVerificationLogs()

        } catch (error) {
            ElMessage.error(error?.response?.data?.message || '水印嵌入失败')
        } finally {
            embedLoading.value = false
        }
    })
}

function viewLogDetail(log) {
    currentLog.value = log
    logDetailDialogVisible.value = true
}

function resetVerifyForm() {
    verifyForm.audio_file = null
    verifyResult.value = null

    if (verifyUploadRef.value) {
        verifyUploadRef.value.clearFiles()
    }
}

function resetEmbedForm() {
    embedForm.model_id = ''
    embedForm.audio_file = null
    embedForm.code_length = 64
    embedForm.description = ''

    if (embedUploadRef.value) {
        embedUploadRef.value.clearFiles()
    }
}

function getVerifyResultDescription(result) {
    if (result.success) {
        return '该音频文件包含AI生成水印，以下是详细信息'
    } else {
        return '该音频文件未检测到AI生成水印，可能是原创音频或使用了其他生成方式'
    }
}

function formatTime(timeStr) {
    if (!timeStr) return ''
    return new Date(timeStr).toLocaleString()
}

onMounted(() => {
    if (isLoggedIn.value) {
        fetchVerificationLogs()
    }
})
</script>

<style scoped>
.watermark-management {
    padding: 24px;
    background: #f8f9fb;
    min-height: 100vh;
}

.page-header {
    margin-bottom: 32px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px;
    padding: 32px;
    color: white;
    box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header-text h1 {
    margin: 0 0 8px 0;
    font-size: 32px;
    font-weight: 700;
}

.header-text p {
    margin: 0;
    font-size: 16px;
    opacity: 0.9;
}

.header-actions {
    display: flex;
    gap: 12px;
}

.feature-cards {
    margin-bottom: 32px;
}

.feature-card {
    cursor: pointer;
    transition: all 0.3s ease;
    border: none;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.feature-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}

.verify-card {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    color: white;
}

.embed-card {
    background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
    color: white;
}

.card-content {
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 24px;
}

.card-icon {
    width: 60px;
    height: 60px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
}

.card-info h3 {
    margin: 0 0 8px 0;
    font-size: 20px;
    font-weight: 600;
}

.card-info p {
    margin: 0;
    font-size: 14px;
    opacity: 0.9;
    line-height: 1.4;
}

.verification-history {
    border: none;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
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

.no-watermark {
    color: #999;
}

.verify-section {
    margin-bottom: 24px;
}

.verify-section h4 {
    margin: 0 0 16px 0;
    font-size: 16px;
    color: #333;
}

.verify-result {
    margin-top: 24px;
    padding-top: 20px;
    border-top: 1px solid #eee;
}

.watermark-info {
    margin-top: 16px;
}

.watermark-info h4 {
    margin: 0 0 12px 0;
    font-size: 14px;
    color: #333;
}

.login-prompt {
    text-align: center;
    padding: 20px;
}

.code-length-tip {
    margin-top: 8px;
    font-size: 12px;
    color: #666;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .watermark-management {
        padding: 16px;
    }

    .header-content {
        flex-direction: column;
        gap: 20px;
        text-align: center;
    }

    .header-actions {
        flex-direction: column;
        width: 100%;
    }

    .feature-cards .el-col {
        margin-bottom: 16px;
    }

    .card-content {
        flex-direction: column;
        text-align: center;
        gap: 16px;
    }
}

/* Element Plus 样式覆盖 */
:deep(.el-upload-dragger) {
    border: 2px dashed #d9d9d9;
    border-radius: 12px;
    background: #fafafa;
    transition: all 0.3s ease;
}

:deep(.el-upload-dragger:hover) {
    border-color: #409eff;
    background: #ecf5ff;
}

:deep(.el-table) {
    border-radius: 8px;
    overflow: hidden;
}

:deep(.el-dialog) {
    border-radius: 16px;
}

:deep(.el-card__header) {
    padding: 20px;
    border-bottom: 1px solid #f0f0f0;
}

:deep(.el-card__body) {
    padding: 20px;
}

:deep(.el-slider__runway) {
    height: 6px;
    background-color: #e4e7ed;
    border-radius: 3px;
}

:deep(.el-slider__bar) {
    background-color: #409eff;
    border-radius: 3px;
}

:deep(.el-slider__button) {
    width: 16px;
    height: 16px;
    border: 2px solid #409eff;
}
</style>