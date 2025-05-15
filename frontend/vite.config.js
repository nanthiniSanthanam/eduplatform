// File: vite.config.js
// This file configures the Vite development server and build process
// The server.proxy setting forwards API requests to the Django backend

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173, // Match the port specified in CORS settings
    open: true, // Open browser on start
    proxy: {
      // Forward any request starting with /api to the Django backend
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      },
      // Forward any request starting with /media to the Django backend
      '/media': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  }
});