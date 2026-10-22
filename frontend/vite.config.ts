import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
        configure: (proxy) => {
          proxy.on('error', (err: any) => {
            // Ignore transient disconnects during server reloads
            if (['ECONNRESET', 'EPIPE', 'ECONNABORTED', 'ECONNREFUSED'].includes(err?.code)) return;
          });
          proxy.on('proxyReqWs', (_proxyReq, _req, socket: any) => {
            socket.on('error', (err: any) => {
              if (['ECONNRESET', 'EPIPE', 'ECONNABORTED', 'ECONNREFUSED'].includes(err?.code)) return;
            });
          });
        },
      },
    },
  },
});
