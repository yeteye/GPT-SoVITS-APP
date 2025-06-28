<!-- ./gpt-sovits-frontend/src/components/FloatingCart.vue -->
<template>
    <transition name="fade-slide">
        <div v-if="show" class="floating-cart">
            <div class="cart-content">
                <el-icon class="cart-icon">
                    <SuccessFilled />
                </el-icon>
                <span class="cart-message">{{ message }}</span>
                <el-button text class="close-btn" @click="close" size="small">
                    <el-icon>
                        <Close />
                    </el-icon>
                </el-button>
            </div>
        </div>
    </transition>
</template>

<script setup>
import { ref, watch } from 'vue'
import { SuccessFilled, Close } from '@element-plus/icons-vue'

const props = defineProps({
    message: {
        type: String,
        default: ''
    },
    duration: {
        type: Number,
        default: 3000
    }
})

const show = ref(false)
let timer = null

const close = () => {
    show.value = false
    clearTimer()
}

const clearTimer = () => {
    if (timer) {
        clearTimeout(timer)
        timer = null
    }
}

watch(() => props.message, (newMessage) => {
    if (newMessage) {
        show.value = true
        clearTimer()

        if (props.duration > 0) {
            timer = setTimeout(() => {
                show.value = false
            }, props.duration)
        }
    }
})

// 鼠标悬停时暂停自动关闭
const handleMouseEnter = () => {
    clearTimer()
}

const handleMouseLeave = () => {
    if (show.value && props.duration > 0) {
        timer = setTimeout(() => {
            show.value = false
        }, 1000) // 悬停后1秒关闭
    }
}
</script>

<style scoped>
.floating-cart {
    position: fixed;
    top: 80px;
    right: 20px;
    z-index: 2000;
    max-width: 400px;
    min-width: 200px;
    pointer-events: auto;
}

.cart-content {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    background: var(--success-color);
    color: white;
    padding: var(--spacing-md) var(--spacing-lg);
    border-radius: var(--radius-large);
    box-shadow: var(--shadow-medium);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.cart-icon {
    font-size: 18px;
    flex-shrink: 0;
}

.cart-message {
    font-size: 14px;
    font-weight: 500;
    flex: 1;
    line-height: 1.4;
}

.close-btn {
    color: white;
    padding: 4px;
    margin: -4px;
    flex-shrink: 0;
}

.close-btn:hover {
    background: rgba(255, 255, 255, 0.2);
}

/* 动画效果 */
.fade-slide-enter-active,
.fade-slide-leave-active {
    transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.fade-slide-enter-from {
    opacity: 0;
    transform: translateX(100%) scale(0.9);
}

.fade-slide-leave-to {
    opacity: 0;
    transform: translateX(100%) scale(0.9);
}

.fade-slide-enter-to,
.fade-slide-leave-from {
    opacity: 1;
    transform: translateX(0) scale(1);
}

/* 响应式设计 */
@media (max-width: 768px) {
    .floating-cart {
        right: 10px;
        left: 10px;
        top: 70px;
        max-width: none;
    }

    .cart-content {
        padding: var(--spacing-sm) var(--spacing-md);
    }

    .cart-message {
        font-size: 13px;
    }
}

/* 暗色主题适配 */
[data-theme="dark"] .cart-content {
    background: var(--success-color);
    border-color: rgba(255, 255, 255, 0.15);
}
</style>
