import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5100,
    strictPort: true,
    proxy: {
      // 开发时把 /api 转发到共用后端
      '/api': 'http://localhost:3040',
    },
  },
});
