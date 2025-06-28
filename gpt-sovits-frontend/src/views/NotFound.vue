<!-- ./gpt-sovits-frontend/src/views/NotFound.vue -->
<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <div class="error-animation">
        <div class="error-code">404</div>
        <div class="error-particles">
          <div class="particle" v-for="i in 6" :key="i"></div>
        </div>
      </div>

      <div class="error-message">
        <h2>页面走丢了</h2>
        <p>抱歉，您访问的页面不存在或已被移除</p>
      </div>

      <div class="error-actions">
        <el-button type="primary" size="large" @click="goHome">
          <el-icon>
            <House />
          </el-icon>
          返回首页
        </el-button>
        <el-button size="large" @click="goBack">
          <el-icon>
            <ArrowLeft />
          </el-icon>
          返回上页
        </el-button>
      </div>

      <div class="helpful-links">
        <h3>您可能想要：</h3>
        <div class="link-grid">
          <router-link to="/tts-playground" class="help-link">
            <el-icon>
              <Microphone />
            </el-icon>
            <span>文本转语音</span>
          </router-link>
          <router-link to="/voice-clone" class="help-link">
            <el-icon>
              <Magic />
            </el-icon>
            <span>音色克隆</span>
          </router-link>
          <router-link to="/voice-library" class="help-link">
            <el-icon>
              <Microphone />
            </el-icon>
            <span>音色库</span>
          </router-link>
          <router-link to="/help" class="help-link">
            <el-icon>
              <QuestionFilled />
            </el-icon>
            <span>帮助中心</span>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { House, ArrowLeft, Microphone, Magic, Microphone, QuestionFilled } from '@element-plus/icons-vue'

const router = useRouter()

function goHome() {
  router.push({ name: 'Home' })
}

function goBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push({ name: 'Home' })
  }
}
</script>

<style scoped>
.not-found-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-color) 100%);
  padding: var(--spacing-lg);
}

.not-found-content {
  text-align: center;
  max-width: 600px;
  width: 100%;
}

.error-animation {
  position: relative;
  margin-bottom: var(--spacing-xl);
}

.error-code {
  font-size: 120px;
  font-weight: 900;
  background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  animation: bounce 2s infinite;
}

.error-particles {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 300px;
  height: 300px;
  pointer-events: none;
}

.particle {
  position: absolute;
  width: 8px;
  height: 8px;
  background: var(--primary-color);
  border-radius: 50%;
  animation: float 3s infinite;
}

.particle:nth-child(1) {
  top: 20%;
  left: 20%;
  animation-delay: 0s;
}

.particle:nth-child(2) {
  top: 20%;
  right: 20%;
  animation-delay: 0.5s;
}

.particle:nth-child(3) {
  bottom: 20%;
  left: 20%;
  animation-delay: 1s;
}

.particle:nth-child(4) {
  bottom: 20%;
  right: 20%;
  animation-delay: 1.5s;
}

.particle:nth-child(5) {
  top: 50%;
  left: 10%;
  animation-delay: 2s;
}

.particle:nth-child(6) {
  top: 50%;
  right: 10%;
  animation-delay: 2.5s;
}

.error-message {
  margin-bottom: var(--spacing-xl);
}

.error-message h2 {
  font-size: 28px;
  color: var(--text-color);
  margin: 0 0 var(--spacing-md) 0;
  font-weight: 600;
}

.error-message p {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.6;
}

.error-actions {
  display: flex;
  gap: var(--spacing-md);
  justify-content: center;
  margin-bottom: var(--spacing-xxl);
  flex-wrap: wrap;
}

.helpful-links {
  margin-top: var(--spacing-xl);
}

.helpful-links h3 {
  font-size: 18px;
  color: var(--text-color);
  margin: 0 0 var(--spacing-lg) 0;
  font-weight: 600;
}

.link-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: var(--spacing-md);
  max-width: 400px;
  margin: 0 auto;
}

.help-link {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  background: var(--bg-color);
  border: 1px solid var(--border-lighter);
  border-radius: var(--radius-large);
  text-decoration: none;
  color: var(--text-secondary);
  transition: var(--transition-normal);
  box-shadow: var(--shadow-light);
}

.help-link:hover {
  color: var(--primary-color);
  border-color: var(--primary-color);
  transform: translateY(-2px);
  box-shadow: var(--shadow-medium);
}

.help-link .el-icon {
  font-size: 24px;
}

.help-link span {
  font-size: 14px;
  font-weight: 500;
}

/* 动画 */
@keyframes bounce {

  0%,
  20%,
  50%,
  80%,
  100% {
    transform: translateY(0);
  }

  40% {
    transform: translateY(-10px);
  }

  60% {
    transform: translateY(-5px);
  }
}

@keyframes float {

  0%,
  100% {
    transform: translateY(0) scale(1);
    opacity: 0.7;
  }

  50% {
    transform: translateY(-20px) scale(1.1);
    opacity: 1;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .error-code {
    font-size: 80px;
  }

  .error-message h2 {
    font-size: 24px;
  }

  .error-message p {
    font-size: 14px;
  }

  .error-actions {
    flex-direction: column;
    align-items: center;
  }

  .error-actions .el-button {
    width: 200px;
  }

  .link-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--spacing-sm);
  }

  .help-link {
    padding: var(--spacing-md);
  }
}

@media (max-width: 480px) {
  .error-code {
    font-size: 60px;
  }

  .link-grid {
    grid-template-columns: 1fr;
  }
}

/* 暗色主题适配 */
[data-theme="dark"] .help-link {
  background: var(--bg-secondary);
  border-color: var(--border-color);
}

[data-theme="dark"] .help-link:hover {
  border-color: var(--primary-color);
  background: var(--bg-color);
}
</style>