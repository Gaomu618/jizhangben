import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(),
    // base 组件修改后强制 full reload（HMR 不靠谱，会让用户卡在旧版）
    {
      name: 'force-reload-base-components',
      handleHotUpdate({ file, server }) {
        if (file.includes('/components/base/')) {
          server.ws.send({ type: 'full-reload' })
        }
      },
    },
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5002',
        changeOrigin: true
      },
      '/uploads': {
        target: 'http://localhost:5002',
        changeOrigin: true
      }
    }
  }
})