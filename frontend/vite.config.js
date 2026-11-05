import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// En desarrollo, las llamadas a /api se reenvían al backend FastAPI (puerto 8000).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
})
