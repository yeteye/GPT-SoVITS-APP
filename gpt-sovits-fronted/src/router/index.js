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
        component: Login
    },
    {
        path: '/register',
        name: 'Register',
        component: Register
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach((to, from, next) => {
    const isLoggedIn = localStorage.getItem('isLoggedIn'); // 假设登录状态存储在 localStorage 中

    if (!isLoggedIn && to.name !== 'Login' && to.name !== 'Register') {
        next({ name: 'Login' }); // 未登录时跳转到登录页面
    } else {
        next(); // 已登录或访问登录/注册页面时继续导航
    }
});

export default router
