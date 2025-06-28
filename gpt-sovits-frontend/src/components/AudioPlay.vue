<!-- src/components/AudioPlayer.vue -->
<template>
    <div class="audio-player" :class="{ 'compact': compact }">
      <div class="player-controls">
        <el-button 
          :icon="isPlaying ? VideoPause : VideoPlay" 
          circle 
          :size="compact ? 'small' : 'default'"
          @click="togglePlay"
          :disabled="!audioUrl"
        />
        
        <div class="time-display" v-if="!compact">
          <span class="current-time">{{ formatTime(currentTime) }}</span>
          <span class="separator">/</span>
          <span class="total-time">{{ formatTime(duration) }}</span>
        </div>
      </div>
  
      <div class="progress-section">
        <el-slider
          v-model="progress"
          :max="100"
          :show-tooltip="false"
          @change="seekTo"
          :disabled="!audioUrl"
          size="small"
        />
      </div>
  
      <div class="volume-section" v-if="!compact">
        <el-button 
          :icon="isMuted ? Mute : VolumeUp" 
          text 
          @click="toggleMute"
        />
        <el-slider
          v-model="volume"
          :max="100"
          :show-tooltip="false"
          @change="changeVolume"
          style="width: 80px"
          size="small"
        />
      </div>
  
      <div class="player-actions" v-if="showActions">
        <el-button 
          :icon="Download" 
          text 
          @click="$emit('download')"
          :disabled="!audioUrl"
          size="small"
        >
          下载
        </el-button>
      </div>
  
      <audio
        ref="audioElement"
        :src="audioUrl"
        @loadedmetadata="onLoadedMetadata"
        @timeupdate="onTimeUpdate"
        @ended="onEnded"
        @error="onError"
        preload="metadata"
      />
    </div>
  </template>
  
  <script setup>
  import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
  import { ElMessage } from 'element-plus'
  import {
    VideoPlay,
    VideoPause,
    VolumeUp,
    Mute,
    Download
  } from '@element-plus/icons-vue'
  
  const props = defineProps({
    audioUrl: {
      type: String,
      default: ''
    },
    compact: {
      type: Boolean,
      default: false
    },
    showActions: {
      type: Boolean,
      default: true
    },
    autoPlay: {
      type: Boolean,
      default: false
    }
  })
  
  const emit = defineEmits(['play', 'pause', 'ended', 'download', 'error'])
  
  const audioElement = ref(null)
  const isPlaying = ref(false)
  const currentTime = ref(0)
  const duration = ref(0)
  const volume = ref(100)
  const isMuted = ref(false)
  
  const progress = computed({
    get() {
      return duration.value > 0 ? (currentTime.value / duration.value) * 100 : 0
    },
    set(value) {
      if (audioElement.value && duration.value > 0) {
        const time = (value / 100) * duration.value
        audioElement.value.currentTime = time
        currentTime.value = time
      }
    }
  })
  
  // 播放/暂停切换
  function togglePlay() {
    if (!audioElement.value || !props.audioUrl) return
  
    if (isPlaying.value) {
      pause()
    } else {
      play()
    }
  }
  
  // 播放
  function play() {
    if (!audioElement.value) return
  
    audioElement.value.play().then(() => {
      isPlaying.value = true
      emit('play')
    }).catch(error => {
      ElMessage.error('播放失败')
      emit('error', error)
    })
  }
  
  // 暂停
  function pause() {
    if (!audioElement.value) return
  
    audioElement.value.pause()
    isPlaying.value = false
    emit('pause')
  }
  
  // 停止
  function stop() {
    if (!audioElement.value) return
  
    audioElement.value.pause()
    audioElement.value.currentTime = 0
    isPlaying.value = false
    currentTime.value = 0
  }
  
  // 跳转到指定位置
  function seekTo(value) {
    if (!audioElement.value || !duration.value) return
  
    const time = (value / 100) * duration.value
    audioElement.value.currentTime = time
  }
  
  // 音量控制
  function changeVolume(value) {
    if (!audioElement.value) return
  
    audioElement.value.volume = value / 100
    isMuted.value = value === 0
  }
  
  // 静音切换
  function toggleMute() {
    if (!audioElement.value) return
  
    if (isMuted.value) {
      audioElement.value.volume = volume.value / 100
      isMuted.value = false
    } else {
      audioElement.value.volume = 0
      isMuted.value = true
    }
  }
  
  // 格式化时间
  function formatTime(seconds) {
    if (isNaN(seconds) || seconds < 0) return '00:00'
  
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  
  // 事件处理
  function onLoadedMetadata() {
    if (audioElement.value) {
      duration.value = audioElement.value.duration
      
      // 自动播放
      if (props.autoPlay) {
        play()
      }
    }
  }
  
  function onTimeUpdate() {
    if (audioElement.value) {
      currentTime.value = audioElement.value.currentTime
    }
  }
  
  function onEnded() {
    isPlaying.value = false
    currentTime.value = 0
    emit('ended')
  }
  
  function onError(error) {
    ElMessage.error('音频加载失败')
    emit('error', error)
  }
  
  // 监听音频URL变化
  watch(() => props.audioUrl, (newUrl) => {
    if (newUrl) {
      // 重置状态
      stop()
      duration.value = 0
      currentTime.value = 0
    }
  })
  
  // 暴露方法给父组件
  defineExpose({
    play,
    pause,
    stop,
    seekTo,
    isPlaying: () => isPlaying.value,
    getCurrentTime: () => currentTime.value,
    getDuration: () => duration.value
  })
  
  // 组件卸载时停止播放
  onUnmounted(() => {
    stop()
  })
  </script>
  
  <style scoped>
  .audio-player {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 12px 16px;
    background: #f8f9fb;
    border-radius: 12px;
    border: 1px solid #e4e7ed;
    min-width: 400px;
  }
  
  .audio-player.compact {
    gap: 8px;
    padding: 8px 12px;
    min-width: 200px;
  }
  
  .player-controls {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .time-display {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    color: #666;
    min-width: 80px;
  }
  
  .separator {
    color: #999;
  }
  
  .progress-section {
    flex: 1;
    min-width: 100px;
  }
  
  .volume-section {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .player-actions {
    display: flex;
    gap: 8px;
  }
  
  /* 响应式设计 */
  @media (max-width: 768px) {
    .audio-player {
      flex-direction: column;
      gap: 8px;
      min-width: auto;
    }
  
    .audio-player:not(.compact) {
      padding: 12px;
    }
  
    .player-controls {
      width: 100%;
      justify-content: center;
    }
  
    .progress-section {
      width: 100%;
    }
  
    .volume-section {
      width: 100%;
      justify-content: center;
    }
  
    .player-actions {
      width: 100%;
      justify-content: center;
    }
  }
  
  /* Element Plus 样式覆盖 */
  :deep(.el-slider__runway) {
    height: 4px;
    background-color: #dcdfe6;
  }
  
  :deep(.el-slider__bar) {
    background-color: #409eff;
  }
  
  :deep(.el-slider__button) {
    width: 12px;
    height: 12px;
    border: 2px solid #409eff;
  }
  </style>