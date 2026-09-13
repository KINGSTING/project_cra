import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    // Force Vite to use Vercel's assigned port, otherwise fallback to 5173
    port: process.env.PORT ? parseInt(process.env.PORT) : 5173,
    // Expose the network host so Vercel's proxy can detect it
    host: true,
    strictPort: true
  }
})