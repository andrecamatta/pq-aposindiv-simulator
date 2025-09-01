import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // Permite acesso de qualquer IP
    port: 5173,
    strictPort: true, // Falha se a porta estiver ocupada
    open: false, // Não abrir browser automaticamente
  },
})
