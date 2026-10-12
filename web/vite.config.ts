import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // In development, forward /api/* to the FastAPI server, so the browser
    // talks to one origin (no CORS issues) — same idea as Angular's proxy.conf.json
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
