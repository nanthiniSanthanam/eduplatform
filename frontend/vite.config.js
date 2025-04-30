// File: vite.config.js
// This file configures the Vite development server and build process
// The server.proxy setting forwards API requests to the Django backend

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      // Forward any request starting with /api to the Django backend
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      // Forward any request starting with /media to the Django backend
      '/media': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  }
});