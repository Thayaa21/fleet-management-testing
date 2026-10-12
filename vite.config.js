import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// The app is served from the domain root. The previous '/Load-Lorry/' base
// (a project-pages subpath) was removed in Batch 1; re-add `base` here only if
// the app is later deployed under a subpath.
export default defineConfig({
  plugins: [react()],
  server: {
    // Proxy API calls to the FastAPI backend during development. The frontend
    // calls '/api/...' (see src/api/client.js) and Vite forwards to :8000,
    // stripping the /api prefix.
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['src/test/setup.js'],
  },
})
