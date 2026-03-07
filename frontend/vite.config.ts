import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  
  const frontendHost = env.VITE_FRONTEND_HOST || '::'
  const frontendPort = parseInt(env.VITE_FRONTEND_PORT || '5174', 10)
  const apiBaseUrl = env.VITE_API_BASE_URL || 'http://localhost:8000'
  const wsUrl = env.VITE_WS_URL || 'ws://localhost:8000'
  
  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    build: {
      // 添加内容哈希，确保文件更新时 URL 变化
      rollupOptions: {
        output: {
          entryFileNames: 'js/[name]-[hash].js',
          chunkFileNames: 'js/[name]-[hash].js',
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name.split('.');
            const ext = info[info.length - 1];
            if (/\.(png|jpe?g|gif|svg|webp|ico)$/i.test(assetInfo.name)) {
              return 'img/[name]-[hash][extname]';
            }
            if (/\.css$/i.test(assetInfo.name)) {
              return 'css/[name]-[hash][extname]';
            }
            return '[name]-[hash][extname]';
          },
        },
      },
    },
    server: {
      host: frontendHost,
      port: frontendPort,
      allowedHosts: true,
      hmr: {
        clientPort: frontendPort,
        // 允许所有网络接口的热更新
        host: frontendHost,
      },
      proxy: {
        '/api': {
          target: apiBaseUrl,
          changeOrigin: true,
          ws: true,
        },
        '/ws': {
          target: wsUrl,
          ws: true,
        },
      },
    },
  }
})
