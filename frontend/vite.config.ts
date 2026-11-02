import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

// En desarrollo, /api se redirige al backend FastAPI local.
const backend = process.env.VITE_PROXY_TARGET ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  test: {
    include: ['src/**/*.test.{ts,tsx}'],
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    clearMocks: true,
    restoreMocks: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: backend, changeOrigin: true, rewrite: (ruta) => ruta.replace(/^\/api/, '') },
    },
  },
})
