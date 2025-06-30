<!-- ./gpt-sovits-frontend/src/views/Status.vue -->
<template>
    <div class="status-page">
        <div class="page-header">
            <h1>任务状态</h1>
            <p>查看任务的执行状态和详细信息</p>
        </div>

        <el-card class="status-card" v-loading="loading">
            <template #header>
                <div class="card-header">
                    <div class="header-left">
                        <h3>任务详情</h3>
                        <el-tag :type="getTaskTypeTagType(taskData?.type)" size="large" v-if="taskData">
                            {{ getTaskTypeText(taskData.type) }}
                        </el-tag>
                    </div>
                    <el-button @click="goBack">返回</el-button>
                </div>
            </template>

            <div v-if="taskData" class="task-details">
                <!-- 任务基本信息 -->
                <div class="info-section">
                    <h4>基本信息</h4>
                    <el-descriptions :column="3" border>
                        <el-descriptions-item label="任务ID" label-align="right">
                            <span class="task-id">{{ taskData.id }}</span>
                            <el-button size="small" text @click="copyToClipboard(taskData.id)">复制</el-button>
                        </el-descriptions-item>
                        <el-descriptions-item label="任务名称" label-align="right">
                            {{ taskData.task_name || taskData.model_name || '未命名任务' }}
                        </el-descriptions-item>
                        <el-descriptions-item label="状态" label-align="right">
                            <el-tag :type="getStatusTagType(taskData.status)" size="small">
                                {{ getStatusText(taskData.status) }}
                            </el-tag>
                        </el-descriptions-item>
                        <el-descriptions-item label="创建时间" label-align="right">
                            {{ formatTime(taskData.created_at) }}
                        </el-descriptions-item>
                        <el-descriptions-item label="开始时间" label-align="right">
                            {{ taskData.started_at ? formatTime(taskData.started_at) : '未开始' }}
                        </el-descriptions-item>
                        <el-descriptions-item label="完成时间" label-align="right">
                            {{ taskData.completed_at ? formatTime(taskData.completed_at) : '未完成' }}
                        </el-descriptions-item>
                        <el-descriptions-item label="执行耗时" label-align="right">
                            {{ getDuration(taskData) }}
                        </el-descriptions-item>
                        <el-descriptions-item label="预计完成时间" label-align="right" v-if="taskData.estimated_completion">
                            {{ formatTime(taskData.estimated_completion) }}
                        </el-descriptions-item>
                        <el-descriptions-item label="用户ID" label-align="right">
                            {{ taskData.user_id }}
                        </el-descriptions-item>
                    </el-descriptions>
                </div>

                <!-- 进度显示 -->
                <div class="progress-section" v-if="!['completed', 'failed', 'cancelled'].includes(taskData.status)">
                    <h4>执行进度</h4>
                    <div class="progress-container">
                        <el-progress :percentage="getProgress(taskData.status, taskData.progress)"
                            :status="getProgressStatus(taskData.status)" :stroke-width="12" />
                        <p class="progress-text">{{ getProgressText(taskData.status) }}</p>
                        <p class="progress-detail" v-if="taskData.estimated_completion">
                            预计还需要：{{ getTimeRemaining(taskData.estimated_completion) }}
                        </p>
                    </div>
                </div>

                <!-- TTS任务详情 -->
                <div v-if="taskData.type === 'tts'" class="task-specific-details">
                    <h4>TTS 任务参数</h4>
                    <el-descriptions :column="2" border>
                        <el-descriptions-item label="文本内容" span="2" label-align="right">
                            <div class="text-content">
                                <el-input type="textarea" :model-value="taskData.text || '无'" readonly :rows="4"
                                    resize="none" />
                            </div>
                        </el-descriptions-item>
                        <el-descriptions-item label="文本长度" label-align="right">
                            {{ taskData.text_length || 0 }} 字符
                        </el-descriptions-item>
                        <el-descriptions-item label="预计音频时长" label-align="right">
                            {{ formatDuration(taskData.estimated_audio_duration) }}
                        </el-descriptions-item>
                        <el-descriptions-item label="语速" label-align="right">
                            {{ taskData.speed || 1.0 }}x
                        </el-descriptions-item>
                        <el-descriptions-item label="音调" label-align="right">
                            {{ taskData.pitch || 1.0 }}
                        </el-descriptions-item>
                        <el-descriptions-item label="音量" label-align="right">
                            {{ taskData.volume || 1.0 }}
                        </el-descriptions-item>
                        <el-descriptions-item label="情感" label-align="right">
                            <el-tag size="small">{{ taskData.emotion || 'neutral' }}</el-tag>
                        </el-descriptions-item>
                    </el-descriptions>

                    <!-- 模型信息 -->
                    <div class="model-info" v-if="taskData.model">
                        <h5>使用的模型信息</h5>
                        <el-descriptions :column="2" border>
                            <el-descriptions-item label="模型名称" label-align="right">
                                {{ taskData.model.name }}
                            </el-descriptions-item>
                            <el-descriptions-item label="模型类型" label-align="right">
                                <el-tag :type="taskData.model.model_type === 'official' ? 'success' : 'primary'"
                                    size="small">
                                    {{ taskData.model.model_type === 'official' ? '官方模型' : '用户模型' }}
                                </el-tag>
                            </el-descriptions-item>
                            <el-descriptions-item label="模型描述" span="2" label-align="right">
                                {{ taskData.model.description || '无描述' }}
                            </el-descriptions-item>
                            <el-descriptions-item label="支持语言" label-align="right">
                                <el-tag v-for="lang in taskData.model.supported_languages" :key="lang" size="small"
                                    style="margin-right: 5px;">
                                    {{ lang }}
                                </el-tag>
                            </el-descriptions-item>
                            <el-descriptions-item label="支持情感" label-align="right">
                                <el-tag v-for="emotion in taskData.model.supported_emotions" :key="emotion" size="small"
                                    style="margin-right: 5px;">
                                    {{ emotion }}
                                </el-tag>
                            </el-descriptions-item>
                            <el-descriptions-item label="质量评分" label-align="right">
                                <el-rate :model-value="taskData.model.quality_score / 2" disabled show-score />
                            </el-descriptions-item>
                            <el-descriptions-item label="使用次数" label-align="right">
                                {{ taskData.model.usage_count }}
                            </el-descriptions-item>
                            <el-descriptions-item label="模型标签" span="2" label-align="right">
                                <el-tag v-for="tag in taskData.model.tags" :key="tag.id" :color="tag.color" size="small"
                                    style="margin-right: 5px; color: white;">
                                    {{ tag.name }}
                                </el-tag>
                            </el-descriptions-item>
                        </el-descriptions>
                    </div>

                    <!-- TTS结果信息 -->
                    <div v-if="taskData.status === 'completed'" class="result-info">
                        <h5>生成结果</h5>
                        <el-descriptions :column="2" border>
                            <el-descriptions-item label="音频时长" label-align="right">
                                {{ formatDuration(taskData.audio_duration) }}
                            </el-descriptions-item>
                            <el-descriptions-item label="音频大小" label-align="right">
                                {{ formatFileSize(taskData.audio_size) }}
                            </el-descriptions-item>
                            <el-descriptions-item label="下载次数" label-align="right">
                                {{ taskData.download_count || 0 }}
                            </el-descriptions-item>
                            <el-descriptions-item label="质量评分" label-align="right">
                                <el-rate v-if="taskData.quality_score" :model-value="taskData.quality_score / 2"
                                    disabled show-score />
                                <span v-else>暂无评分</span>
                            </el-descriptions-item>
                        </el-descriptions>
                    </div>
                </div>

                <!-- 音色克隆任务详情 -->
                <div v-if="taskData.type === 'voice_clone'" class="task-specific-details">
                    <h4>音色克隆任务参数</h4>
                    <el-descriptions :column="2" border>
                        <el-descriptions-item label="模型名称" label-align="right">
                            {{ taskData.model_name || taskData.task_name || '未命名' }}
                        </el-descriptions-item>
                        <el-descriptions-item label="样本数量" label-align="right">
                            {{ taskData.sample_count || 0 }} 个
                        </el-descriptions-item>
                        <el-descriptions-item label="总音频时长" label-align="right">
                            {{ formatDuration(taskData.total_duration) }}
                        </el-descriptions-item>
                        <el-descriptions-item label="模型路径" label-align="right">
                            {{ taskData.model_path || '待生成' }}
                        </el-descriptions-item>
                        <el-descriptions-item label="结果模型ID" label-align="right">
                            {{ taskData.result_model_id || '待生成' }}
                        </el-descriptions-item>
                        <el-descriptions-item label="是否激活" label-align="right">
                            <el-tag :type="taskData.is_active ? 'success' : 'danger'" size="small">
                                {{ taskData.is_active ? '是' : '否' }}
                            </el-tag>
                        </el-descriptions-item>
                        <el-descriptions-item label="支持语言" span="2" label-align="right"
                            v-if="taskData.supported_languages">
                            <el-tag v-for="lang in taskData.supported_languages" :key="lang" size="small"
                                style="margin-right: 5px;">
                                {{ lang }}
                            </el-tag>
                        </el-descriptions-item>
                        <el-descriptions-item label="支持情感" span="2" label-align="right"
                            v-if="taskData.supported_emotions">
                            <el-tag v-for="emotion in taskData.supported_emotions" :key="emotion" size="small"
                                style="margin-right: 5px;">
                                {{ emotion }}
                            </el-tag>
                        </el-descriptions-item>
                    </el-descriptions>
                </div>

                <!-- 操作权限信息 -->
                <div class="permissions-section">
                    <h4>操作权限</h4>
                    <el-descriptions :column="3" border>
                        <el-descriptions-item label="可以取消" label-align="right">
                            <el-tag :type="taskData.can_be_cancelled ? 'success' : 'danger'" size="small">
                                {{ taskData.can_be_cancelled ? '是' : '否' }}
                            </el-tag>
                        </el-descriptions-item>
                        <el-descriptions-item label="可以重试" label-align="right">
                            <el-tag :type="taskData.can_be_retried ? 'success' : 'danger'" size="small">
                                {{ taskData.can_be_retried ? '是' : '否' }}
                            </el-tag>
                        </el-descriptions-item>
                        <el-descriptions-item label="任务状态" label-align="right">
                            <el-tag :type="taskData.is_active ? 'success' : 'info'" size="small">
                                {{ taskData.is_active ? '活跃' : '非活跃' }}
                            </el-tag>
                        </el-descriptions-item>
                    </el-descriptions>
                </div>

                <!-- 错误信息 -->
                <div v-if="taskData.status === 'failed' && taskData.error_message" class="error-section">
                    <h4>错误信息</h4>
                    <el-alert :title="taskData.error_message" type="error" :closable="false" show-icon>
                        <template #default>
                            <p>{{ taskData.error_message }}</p>
                            <p class="error-time">错误发生时间：{{ formatTime(taskData.updated_at || taskData.created_at) }}
                            </p>
                        </template>
                    </el-alert>
                </div>

                <!-- 结果展示 -->
                <div v-if="taskData.status === 'completed'" class="result-section">
                    <h4>任务结果</h4>
                    <div class="result-content">
                        <div class="result-actions">
                            <el-button v-if="hasDownloadUrl(taskData)" type="success" size="large"
                                @click="downloadResult">
                                <el-icon>
                                    <Download />
                                </el-icon>
                                下载结果
                                <span v-if="taskData.download_count">(已下载 {{ taskData.download_count }} 次)</span>
                            </el-button>
                            <el-button v-if="taskData.type === 'tts' && hasAudioUrl(taskData)" type="primary"
                                size="large" @click="playAudio">
                                <el-icon>
                                    <VideoPlay />
                                </el-icon>
                                {{ isPlaying ? '停止播放' : '播放音频' }}
                            </el-button>
                            <el-button v-if="taskData.type === 'voice_clone' && taskData.status === 'completed'"
                                type="info" size="large" @click="useModel">
                                <el-icon>
                                    <Star />
                                </el-icon>
                                使用模型
                            </el-button>
                        </div>

                        <!-- 音频播放控制 -->
                        <div v-if="taskData.type === 'tts' && hasAudioUrl(taskData)" class="audio-controls">
                            <div class="audio-info">
                                <p>音频文件：{{ getAudioFileName(taskData) }}</p>
                                <p v-if="taskData.audio_duration">时长：{{ formatDuration(taskData.audio_duration) }}</p>
                                <p v-if="taskData.audio_size">大小：{{ formatFileSize(taskData.audio_size) }}</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 操作按钮 -->
                <div class="action-buttons">
                    <el-button v-if="taskData.can_be_retried && taskData.status === 'failed'" type="warning"
                        size="large" @click="retryTask">
                        <el-icon>
                            <RefreshRight />
                        </el-icon>
                        重试任务
                    </el-button>
                    <el-button v-if="taskData.can_be_cancelled && canCancel(taskData)" type="danger" size="large"
                        @click="cancelTask">
                        <el-icon>
                            <Close />
                        </el-icon>
                        取消任务
                    </el-button>
                    <el-button type="primary" size="large" @click="refreshTask">
                        <el-icon>
                            <Refresh />
                        </el-icon>
                        刷新状态
                    </el-button>
                </div>
            </div>

            <el-empty v-else-if="!loading" description="任务不存在或已被删除">
                <el-button type="primary" @click="goBack">返回任务列表</el-button>
            </el-empty>
        </el-card>

        <!-- 音频播放器 -->
        <audio ref="audioPlayer" style="display: none" @ended="onAudioEnded" />
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, VideoPlay, Star, RefreshRight, Close, Refresh } from '@element-plus/icons-vue'
import { ttsAPI, voiceCloneAPI } from '@/api'

const route = useRoute()
const router = useRouter()
const audioPlayer = ref()

// 响应式数据
const loading = ref(false)
const taskData = ref(null)
const isPlaying = ref(false)
const pollingTimer = ref(null)

// 获取路由参数
const taskId = route.params.taskId
const taskType = route.query.type

// 方法
async function fetchTaskDetail() {
    loading.value = true
    try {
        let response = null

        if (taskType === 'tts') {
            response = await ttsAPI.getTTSTaskDetail(taskId)
        } else if (taskType === 'voice_clone') {
            response = await voiceCloneAPI.getTaskDetail(taskId)
        } else {
            try {
                response = await ttsAPI.getTTSTaskDetail(taskId)
                if (response && response.data) {
                    // 设置任务类型
                    response.data.task.type = 'tts'
                }
            } catch (error) {
                response = await voiceCloneAPI.getTaskDetail(taskId)
                if (response && response.data) {
                    response.data.task.type = 'voice_clone'
                }
            }
        }

        if (response && response.data) {
            taskData.value = response.data.task || response.data

            // 确保有任务类型
            if (!taskData.value.type) {
                taskData.value.type = taskType || (taskData.value.text ? 'tts' : 'voice_clone')
            }

            // 如果任务未完成，开始轮询
            if (!['completed', 'failed', 'cancelled'].includes(taskData.value.status)) {
                startPolling()
            } else {
                stopPolling()
            }
        } else {
            throw new Error('任务数据为空')
        }
    } catch (error) {
        console.error('获取任务详情失败:', error)
        ElMessage.error('获取任务详情失败')
        taskData.value = null
    } finally {
        loading.value = false
    }
}

function startPolling() {
    if (pollingTimer.value) return

    pollingTimer.value = setInterval(() => {
        fetchTaskDetail()
    }, 3000)
}

function stopPolling() {
    if (pollingTimer.value) {
        clearInterval(pollingTimer.value)
        pollingTimer.value = null
    }
}

function refreshTask() {
    fetchTaskDetail()
}

function goBack() {
    router.back()
}

async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text)
        ElMessage.success('已复制到剪贴板')
    } catch (error) {
        ElMessage.error('复制失败')
    }
}

async function downloadResult() {
    try {
        if (taskData.value.type === 'tts') {
            const res = await ttsAPI.downloadAudio(taskId)
            downloadBlob(res.data, `tts_${taskId}.wav`)
        } else if (taskData.value.type === 'voice_clone') {
            const res = await voiceCloneAPI.getTaskResult(taskId)
            if (res.data?.model_download_url) {
                window.open(res.data.model_download_url, '_blank')
            } else if (res.data?.download_url) {
                window.open(res.data.download_url, '_blank')
            } else {
                ElMessage.warning('暂无下载链接')
            }
        }
        ElMessage.success('下载开始')
    } catch (error) {
        console.error('下载失败:', error)
        ElMessage.error('下载失败')
    }
}

function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
}

function playAudio() {
    if (isPlaying.value) {
        audioPlayer.value.pause()
        isPlaying.value = false
    } else {
        const audioUrl = taskData.value?.audio_url
        if (audioUrl) {
            audioPlayer.value.src = audioUrl
            audioPlayer.value.play()
            isPlaying.value = true
        } else {
            ElMessage.warning('暂无音频文件')
        }
    }
}

function onAudioEnded() {
    isPlaying.value = false
}

function useModel() {
    if (taskData.value?.result_model_id) {
        router.push({
            name: 'TTSPlayground',
            query: { model_id: taskData.value.result_model_id }
        })
    } else {
        ElMessage.warning('模型尚未生成')
    }
}

async function retryTask() {
    try {
        if (taskData.value.type === 'voice_clone') {
            await voiceCloneAPI.retryTask(taskId)
            ElMessage.success('任务已重新提交')
            fetchTaskDetail()
        } else {
            ElMessage.info('TTS任务无法重试，请重新生成')
        }
    } catch (error) {
        console.error('重试失败:', error)
        ElMessage.error('重试失败')
    }
}

async function cancelTask() {
    try {
        await ElMessageBox.confirm(
            '确定要取消这个任务吗？',
            '确认取消',
            { type: 'warning' }
        )

        if (taskData.value.type === 'voice_clone') {
            await voiceCloneAPI.cancelTask(taskId)
            ElMessage.success('任务已取消')
            fetchTaskDetail()
        } else {
            ElMessage.info('TTS任务无法取消')
        }
    } catch (error) {
        if (error !== 'cancel') {
            console.error('取消失败:', error)
            ElMessage.error('取消失败')
        }
    }
}

// 工具函数
function getTaskTypeText(type) {
    const typeMap = {
        'tts': '语音合成',
        'voice_clone': '音色克隆'
    }
    return typeMap[type] || type
}

function getTaskTypeTagType(type) {
    const typeMap = {
        'tts': 'primary',
        'voice_clone': 'success'
    }
    return typeMap[type] || ''
}

function getStatusText(status) {
    const statusMap = {
        'pending': '等待中',
        'processing': '处理中',
        'training': '训练中',
        'completed': '已完成',
        'failed': '失败',
        'cancelled': '已取消'
    }
    return statusMap[status] || status
}

function getStatusTagType(status) {
    const typeMap = {
        'pending': 'info',
        'processing': 'warning',
        'training': 'warning',
        'completed': 'success',
        'failed': 'danger',
        'cancelled': 'info'
    }
    return typeMap[status] || ''
}

function getProgress(status, progress) {
    if (progress && typeof progress === 'number') return progress

    const progressMap = {
        'pending': 10,
        'processing': 50,
        'training': 70,
        'completed': 100,
        'failed': 0,
        'cancelled': 0
    }
    return progressMap[status] || 0
}

function getProgressStatus(status) {
    if (status === 'completed') return 'success'
    if (status === 'failed') return 'exception'
    return null
}

function getProgressText(status) {
    const textMap = {
        'pending': '任务已提交，等待系统处理...',
        'processing': '正在处理中，请稍候...',
        'training': '模型训练中，这可能需要几分钟...',
        'completed': '任务已完成',
        'failed': '任务执行失败',
        'cancelled': '任务已取消'
    }
    return textMap[status] || ''
}

function getTimeRemaining(estimatedCompletion) {
    if (!estimatedCompletion) return '未知'

    const now = new Date()
    const completion = new Date(estimatedCompletion)
    const diff = completion - now

    if (diff <= 0) return '即将完成'

    const minutes = Math.floor(diff / 60000)
    const seconds = Math.floor((diff % 60000) / 1000)

    if (minutes > 0) {
        return `${minutes}分${seconds}秒`
    } else {
        return `${seconds}秒`
    }
}

function hasDownloadUrl(task) {
    return task.audio_url || task.result_url || task.model_download_url
}

function hasAudioUrl(task) {
    return task.audio_url
}

function canCancel(task) {
    return ['pending', 'processing', 'training'].includes(task.status)
}

function getAudioFileName(task) {
    if (task.audio_url) {
        return task.audio_url.split('/').pop() || 'audio.wav'
    }
    return `tts_${task.id}.wav`
}

function formatTime(timeStr) {
    if (!timeStr) return '-'
    return new Date(timeStr).toLocaleString('zh')
}

function formatDuration(seconds) {
    if (!seconds) return '0秒'
    if (seconds < 60) {
        return `${Math.round(seconds)}秒`
    }
    const mins = Math.floor(seconds / 60)
    const secs = Math.round(seconds % 60)
    return `${mins}分${secs}秒`
}

function formatFileSize(bytes) {
    if (!bytes) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function getDuration(task) {
    if (task.duration_seconds && task.duration_seconds > 0) {
        return formatDuration(task.duration_seconds)
    }

    if (!task.created_at) return '-'

    const start = new Date(task.created_at)
    const end = task.completed_at ? new Date(task.completed_at) :
        task.started_at ? new Date() : null

    if (!end) return '未开始'

    const diff = Math.floor((end - start) / 1000)
    return formatDuration(diff)
}

onMounted(() => {
    fetchTaskDetail()
})

onUnmounted(() => {
    stopPolling()
})
</script>

<style scoped>
.status-page {
    padding: 24px;
    background: #f8f9fb;
    min-height: 100vh;
}

.page-header {
    text-align: center;
    margin-bottom: 24px;
}

.page-header h1 {
    font-size: 28px;
    margin: 0 0 8px 0;
    color: #303133;
}

.page-header p {
    font-size: 16px;
    color: #606266;
    margin: 0;
}

.status-card {
    max-width: 1200px;
    margin: 0 auto;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header-left {
    display: flex;
    align-items: center;
    gap: 16px;
}

.header-left h3 {
    margin: 0;
    font-size: 20px;
    color: #333;
}

.task-details {
    padding: 20px 0;
}

.info-section,
.task-specific-details,
.permissions-section {
    margin-bottom: 32px;
}

.info-section h4,
.task-specific-details h4,
.permissions-section h4 {
    margin: 0 0 16px 0;
    font-size: 18px;
    color: #333;
    padding-bottom: 8px;
    border-bottom: 2px solid #409eff;
}

.task-specific-details h5 {
    margin: 24px 0 12px 0;
    font-size: 16px;
    color: #666;
    font-weight: 600;
}

.task-id {
    font-family: monospace;
    font-size: 12px;
    color: #666;
}

.progress-section {
    margin: 24px 0;
    padding: 24px;
    background: linear-gradient(135deg, #f8f9fb 0%, #e3f2fd 100%);
    border-radius: 12px;
    border: 1px solid #e1f5fe;
}

.progress-section h4 {
    margin: 0 0 20px 0;
    font-size: 18px;
    color: #333;
}

.progress-container {
    text-align: center;
}

.progress-text {
    margin: 16px 0 8px 0;
    color: #666;
    font-size: 16px;
    font-weight: 500;
}

.progress-detail {
    margin: 8px 0 0 0;
    color: #999;
    font-size: 14px;
}

.text-content {
    width: 100%;
}

.model-info,
.result-info {
    margin-top: 24px;
    padding: 16px;
    background: #f9f9f9;
    border-radius: 8px;
    border-left: 4px solid #409eff;
}

.error-section {
    margin: 24px 0;
}

.error-section h4 {
    margin: 0 0 12px 0;
    font-size: 18px;
    color: #f56c6c;
}

.error-time {
    margin-top: 8px;
    font-size: 12px;
    color: #999;
}

.result-section {
    margin: 24px 0;
    padding: 24px;
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f7fa 100%);
    border-radius: 12px;
    border: 1px solid #b3e5fc;
}

.result-section h4 {
    margin: 0 0 20px 0;
    font-size: 18px;
    color: #333;
}

.result-content {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.result-actions {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    justify-content: center;
}

.audio-controls {
    padding: 16px;
    background: white;
    border-radius: 8px;
    border: 1px solid #e0e0e0;
}

.audio-info p {
    margin: 4px 0;
    color: #666;
    font-size: 14px;
}

.action-buttons {
    margin-top: 32px;
    padding-top: 24px;
    border-top: 2px solid #f0f0f0;
    display: flex;
    gap: 16px;
    justify-content: center;
    flex-wrap: wrap;
}

/* 自定义描述列表样式 */
:deep(.el-descriptions__body) {
    background: white;
}

:deep(.el-descriptions__label) {
    font-weight: 600;
    color: #333;
    background: #fafafa;
}

:deep(.el-descriptions__content) {
    color: #666;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .status-page {
        padding: 16px;
    }

    .header-left {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
    }

    .result-actions,
    .action-buttons {
        flex-direction: column;
    }

    .result-actions .el-button,
    .action-buttons .el-button {
        width: 100%;
    }

    :deep(.el-descriptions) {
        --el-descriptions-item-bordered-label-vertical-align: top;
    }
}

@media (max-width: 480px) {
    .card-header {
        flex-direction: column;
        gap: 16px;
        align-items: stretch;
    }

    .header-left h3 {
        font-size: 18px;
    }

    .info-section h4,
    .task-specific-details h4,
    .permissions-section h4 {
        font-size: 16px;
    }

    :deep(.el-descriptions) {
        --el-descriptions-table-border: 1px solid var(--el-border-color-lighter);
        --el-descriptions-item-bordered-label-background: var(--el-fill-color-blank);
    }
}
</style>