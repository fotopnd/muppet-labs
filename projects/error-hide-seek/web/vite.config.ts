/// <reference types="vitest/config" />
import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  server: {
    port: 5174,
    proxy: {
      '/sessions': 'http://localhost:8004',
      '/reviews': 'http://localhost:8004',
      '/experiments': 'http://localhost:8004',
      '/results': 'http://localhost:8004',
      '/papers': 'http://localhost:8004',
      '/health': 'http://localhost:8004',
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
  },
})
