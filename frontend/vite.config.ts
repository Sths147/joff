import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    // Makes the Vite dev server (browser-facing) proxy API calls to the
    // directly-run backend, so the browser only ever talks to one origin —
    // same trick nginx does in the containerized stack. Needed for the
    // httpOnly session cookie, which only round-trips same-origin.
    proxy: {
      '/jo': 'http://localhost:5001',
      '/profile': 'http://localhost:5001',
      '/auth': 'http://localhost:5001',
    },
  },
})
