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
                    <h3>任务 #{{ taskId }}</h3>
                    <el-button @click="goBack">返回</el-button>
                </div>
            </template>

            <div v-if="taskData" class="task-details">
                <!-- 任务基本信息 -->
                <el-descriptions title="基本信息" :column="2" border>
                    <el-descriptions-item label="任务ID">{{ taskData.id }}</el-descriptions-item>
                    <el-descriptions-item label="任务类型">
                        <el-tag :type="getTaskTypeTagType(taskData.type)">
                            {{ getTaskTypeText(taskData.type) }}
                        </el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="状态">
                        <el-tag :type="getStatusTagType(taskData.status)">
                            {{ getStatusText(taskData.status) }}
                        </el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="创建时间">
                        {{ formatTime(taskData.created_at) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="完成时间" v-if="taskData.completed_at">
                        {{ formatTime(taskData.completed_at) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="耗时" v-if="taskData.completed_at">
                        {{ getDuration(taskData) }}
                    </el-descriptions-item>
                </el-descriptions>

                <!-- 进度显示 -->
                <div class="progress-section" v-if="!['completed', 'failed', 'cancelled'].includes(taskData.status)">
                    <h4>执行进度</h4>
                    <el-progress :percentage="getProgress(taskData.status, taskData.progress)"
                        :status="getProgressStatus(taskData.status)" :stroke-width="8" />
                    <p class="progress-text">{{ getProgressText(taskData.status) }}</p>
                </div>

                <!-- TTS任务详情 -->
                <div v-if="taskData.type === 'tts'" class="tts-details">
                    <h4>TTS参数</h4>
                    <el-descriptions :column="2" border>
                        <el-descriptions-item label="文本内容">
                            <div class="text-content">{{ taskData.text || '无' }}</div>
                        </el-descriptions-item>
                        <el-descriptions-item label="模型">{{ taskData.model_name || '未知' }}</el-descriptions-item>
                        <el-descriptions-item label="情感">{{ taskData.emotion || '自然' }}</el-descriptions-item>
                        <el-descriptions-item label="语速">{{ taskData.speed || 1.0 }}</el-descriptions-item>
                    </el-descriptions>
                </div>

                <!-- 音色克隆任务详情 -->
                <div v-if="taskData.type === 'voice_clone'" class="voice-clone-details">
                    <h4>克隆参数</h4>
                    <el-descriptions :column="2" border>
                        <el-descriptions-item label="模型名称">{{ taskData.model_name || '未命名' }}</el-descriptions-item>
                        <el-descriptions-item label="样本数量">{{ taskData.sample_count || 0 }}个</el-descriptions-item>
                        <el-descriptions-item label="总时长">{{ formatDuration(taskData.total_duration)
                            }}</el-descriptions-item>
                        <el-descriptions-item label="是否公开">
                            <el-tag :type="taskData.is_public ? 'success' : 'info'">
                                {{ taskData.is_public ? '是' : '否' }}
                            </el-tag>
                        </el-descriptions-item>
                    </el-descriptions>
                </div>

                <!-- 错误信息 -->
                <div v-if="taskData.status === 'failed' && taskData.error_message" class="error-section">
                    <h4>错误信息</h4>
                    <el-alert :title="taskData.error_message" type="error" :closable="false" show-icon />
                </div>

                <!-- 结果展示 -->
                <div v-if="taskData.status === 'completed'" class="result-section">
                    <h4>任务结果</h4>
                    <div class="result-actions">
                        <el-button v-if="taskData.result_url || taskData.audio_url" type="success"
                            @click="downloadResult">
                            <el-icon>
                                <Download />
                            </el-icon>
                            下载结果
                        </el-button>
                        <el-button v-if="taskData.type === 'tts' && (taskData.result_url || taskData.audio_url)"
                            type="primary" @click="playAudio">
                            <el-icon>
                                <VideoPlay />
                            </el-icon>
                            {{ isPlaying ? '停止播放' : '播放音频' }}
                        </el-button>
                        <el-button v-if="taskData.type === 'voice_clone'" type="info" @click="useModel">
                            使用模型
                        </el-button>
                    </div>
                </div>

                <!-- 操作按钮 -->
                <div class="action-buttons">
                    <el-button v-if="canRetry(taskData)" type="warning" @click="retryTask">
                        重试任务
                    </el-button>
                    <el-button v-if="canCancel(taskData)" type="danger" @click="cancelTask">
                        取消任务
                    </el-button>
                </div>
            </div>

            <el-empty v-else-if="!loading" description="任务不存在或已被删除" />
        </el-card>

        <!-- 音频播放器 -->
        <audio ref="audioPlayer" style="display: none" @ended="onAudioEnded" />
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Download, VideoPlay } from '@element-plus/icons-vue'

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
        // 模拟API调用
        const mockTaskData = {
            id: taskId,
            type: taskType || 'tts',
            status: 'completed',
            created_at: new Date(Date.now() - 300000).toISOString(),
            completed_at: new Date().toISOString(),
            progress: 100,
            text: '这是一个测试文本转语音的例子',
            model_name: '测试模型',
            emotion: '自然',
            speed: 1.0,
            result_url: 'https://example.com/result.wav',
            audio_url: 'https://example.com/audio.wav'
        }

        taskData.value = mockTaskData

        // 如果任务未完成，开始轮询
        if (!['completed', 'failed', 'cancelled'].includes(mockTaskData.status)) {
            startPolling()
        }
    } catch (error) {
        ElMessage.error('获取任务详情失败')
    } finally {
        loading.value = false
    }
}

function startPolling() {
    if (pollingTimer.value) return

    pollingTimer.value = setInterval(() => {
        fetchTaskDetail()
    }, 3000) // 每3秒轮询一次
}

function stopPolling() {
    if (pollingTimer.value) {
        clearInterval(pollingTimer.value)
        pollingTimer.value = null
    }
}

function goBack() {
    router.back()
}

async function downloadResult() {
    try {
        if (taskData.value?.result_url) {
            window.open(taskData.value.result_url, '_blank')
        } else {
            ElMessage.warning('暂无下载链接')
        }
    } catch (error) {
        ElMessage.error('下载失败')
    }
}

function playAudio() {
    if (isPlaying.value) {
        audioPlayer.value.pause()
        isPlaying.value = false
    } else {
        const audioUrl = taskData.value?.audio_url || taskData.value?.result_url
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
    router.push({
        name: 'TTSPlayground',
        query: { model_id: taskData.value?.model_id }
    })
}

async function retryTask() {
    try {
        ElMessage.success('任务已重新提交')
        // 这里应该调用重试API
        // await retryTaskAPI(taskId)
    } catch (error) {
        ElMessage.error('重试失败')
    }
}

async function cancelTask() {
    try {
        ElMessage.success('任务已取消')
        // 这里应该调用取消API
        // await cancelTaskAPI(taskId)
        fetchTaskDetail()
    } catch (error) {
        ElMessage.error('取消失败')
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
    if (progress) return progress

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
        'pending': '任务已提交，等待处理...',
        'processing': '正在处理中，请稍候...',
        'training': '模型训练中，请稍候...',
        'completed': '任务已完成',
        'failed': '任务执行失败',
        'cancelled': '任务已取消'
    }
    return textMap[status] || ''
}

function canRetry(task) {
    return task.status === 'failed'
}

function canCancel(task) {
    return ['pending', 'processing', 'training'].includes(task.status)
}

function formatTime(timeStr) {
    return new Date(timeStr).toLocaleString()
}

function formatDuration(seconds) {
    if (!seconds) return '0秒'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return mins > 0 ? `${mins}分${secs}秒` : `${secs}秒`
}

function getDuration(task) {
    if (!task.created_at || !task.completed_at) return '-'

    const start = new Date(task.created_at)
    const end = new Date(task.completed_at)
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
    max-width: 1000px;
    margin: 0 auto;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.card-header h3 {
    margin: 0;
    font-size: 20px;
    color: #333;
}

.task-details {
    padding: 20px 0;
}

.progress-section {
    margin: 24px 0;
    padding: 20px;
    background: #f8f9fb;
    border-radius: 8px;
}

.progress-section h4 {
    margin: 0 0 16px 0;
    font-size: 16px;
    color: #333;
}

.progress-text {
    text-align: center;
    margin: 12px 0 0 0;
    color: #666;
    font-size: 14px;
}

.tts-details,
.voice-clone-details {
    margin: 24px 0;
}

.tts-details h4,
.voice-clone-details h4 {
    margin: 0 0 16px 0;
    font-size: 16px;
    color: #333;
}

.text-content {
    max-width: 300px;
    word-break: break-all;
    line-height: 1.4;
}

.error-section {
    margin: 24px 0;
}

.error-section h4 {
    margin: 0 0 12px 0;
    font-size: 16px;
    color: #f56c6c;
}

.result-section {
    margin: 24px 0;
    padding: 20px;
    background: #f0f9ff;
    border-radius: 8px;
    border: 1px solid #e1f5fe;
}

.result-section h4 {
    margin: 0 0 16px 0;
    font-size: 16px;
    color: #333;
}

.result-actions {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}

.action-buttons {
    margin-top: 24px;
    padding-top: 20px;
    border-top: 1px solid #f0f0f0;
    display: flex;
    gap: 12px;
    justify-content: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .status-page {
        padding: 16px;
    }

    .result-actions,
    .action-buttons {
        flex-direction: column;
    }

    .text-content {
        max-width: 200px;
    }
}
</style>