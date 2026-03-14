import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5004,
    proxy: {
      '/v1': 'http://localhost:3004',
      '/health': 'http://localhost:3004',
      '/auth': 'http://localhost:3004',
    },
  },
});
