import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
plugins: [react()],
  server: {
    proxy: {
      // Any request starting with /api will be forwarded
      '/api': {
        target: 'http://localhost:5000', // Python Flask server
        changeOrigin: true,
        // Do not rewrite; Flask expects the /api prefix
      },
    },
  },
})
