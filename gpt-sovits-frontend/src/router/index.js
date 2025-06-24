// frontend/src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home.vue'
import Generate from '@/views/Generate.vue'
import Status from '@/views/Status.vue'
import History from '@/views/History.vue'
import Settings from '@/views/Settings.vue'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'

const routes = [
    {
        path: '/',
        name: 'Home',
        component: Home
    },
    {
    path: '/user',
    name: 'UserCenter',
    component: () => import('@/views/UserCenter.vue')
    },
    // 文本转语音体验
    {
        path: '/tts-playground',
        name: 'TTSPlayground',
        component: () => import('@/views/user/TTSPlayground.vue')
    },
    // 音色克隆
    {
        path: '/voice-clone',
        name: 'VoiceClone',
        component: () => import('@/views/user/VoiceClone.vue')
    },
    // 音色库
    {
        path: '/voice-library',
        name: 'VoiceLibrary',
        component: () => import('@/views/user/VoiceLibrary.vue')
    },

    // 任务与历史记录
    {
        path: '/task-history',
        name: 'TaskHistory',
        component: () => import('@/views/user/TaskHistory.vue')
    },

    // 创作者中心
    {
        path: '/creator',
        name: 'CreatorCenter',
        component: () => import('@/views/creator/CreatorCenter.vue')
    },
    // 音色克隆向导
    {
        path: '/creator/clone-wizard',
        name: 'CloneWizard',
        component: () => import('@/views/creator/CloneWizard.vue')
    },

    // 我的音色
    {
        path: '/creator/my-voices',
        name: 'MyVoices',
        component: () => import('@/views/creator/MyVoices.vue')
    },

    // 模型分析
    {
        path: '/creator/model-analytics',
        name: 'ModelAnalytics',
        component: () => import('@/views/creator/ModelAnalytics.vue')
    },

    // 音色发布
    {
        path: '/creator/publish-voice',
        name: 'PublishVoice',
        component: () => import('@/views/creator/PublishVoice.vue')
    },

    {
    path: '/admin',
    name: 'AdminDashboard',
    component: () => import('@/views/AdminDashboard.vue')
    },
    {
    path: '/admin/users',
    name: 'UserManage',
    component: () => import('@/views/admin/UserManage.vue') 
    },
    {
    path: '/admin/models',
    name: 'ModelAudit',
    component: () => import('@/views/admin/ModelAudit.vue')
    },
    {
    path: '/admin/logs',
    name: 'SystemLog',
    component: () => import('@/views/admin/SystemLog.vue')
    },
    {
        path: '/generate',
        name: 'Generate',
        component: Generate
    },
    {
        path: '/status/:taskId',
        name: 'Status',
        component: Status,
        props: true
    },
    {
        path: '/history',
        name: 'History',
        component: History
    },
    {
        path: '/settings',
        name: 'Settings',
        component: Settings
    },
    {
        path: '/login',
        name: 'Login',
        component: Login,
        meta: { hideHeader: true }
    },
    {
        path: '/register',
        name: 'Register',
        component: Register,
        meta: { hideHeader: true }
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// router.beforeEach((to, from, next) => {
//     const isLoggedIn = localStorage.getItem('isLoggedIn'); // 假设登录状态存储在 localStorage 中

//     if (!isLoggedIn && to.name !== 'Login' && to.name !== 'Register') {
//         next({ name: 'Login' }); // 未登录时跳转到登录页面
//     } else {
//         next(); // 已登录或访问登录/注册页面时继续导航
//     }
// });

export default router
