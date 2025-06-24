import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    proxy: {
      // 👇 GPT-SoVITS 后端（端口 9880）
      '/api9880': {
        target: 'http://127.0.0.1:9880',
        changeOrigin: true,
        rewrite: path => path.replace(/^\/api9880/, '')
      },
      // 👇 Flask 主后端（端口 5000）
      '/api5000': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        rewrite: path => path.replace(/^\/api5000/, '')
      }
    }
  }
})
