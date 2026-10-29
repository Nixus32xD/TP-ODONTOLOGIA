import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// En desarrollo, /api se redirige al backend FastAPI (en Docker: http://backend:8000).
const backend = process.env.VITE_PROXY_TARGET ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: backend, changeOrigin: true, rewrite: (ruta) => ruta.replace(/^\/api/, '') },
    },
  },
})
