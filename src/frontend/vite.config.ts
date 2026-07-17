import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 4173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '/video_feed': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '/stream_notifications': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '/media': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
    },
  },
});
