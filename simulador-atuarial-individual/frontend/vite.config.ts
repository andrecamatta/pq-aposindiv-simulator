import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // Permite acesso de qualquer IP
    port: 5173,
    strictPort: false, // Permite usar próxima porta disponível
    open: false, // Não abrir browser automaticamente
    watch: {
      usePolling: true,
      interval: 300,
      ignored: ['**/node_modules/**', '**/.git/**'],
    },
  },
})
