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
    server: {
      host: frontendHost,
      port: frontendPort,
      allowedHosts: true,
      hmr: {
        clientPort: frontendPort,
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
