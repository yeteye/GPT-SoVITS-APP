// frontend/src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home.vue'
import Generate from '@/views/Generate.vue'
import Status from '@/views/Status.vue'
import History from '@/views/History.vue'
import Settings from '@/views/Settings.vue'

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
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
