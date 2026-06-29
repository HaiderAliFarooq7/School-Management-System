import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Production-only build config — this app is deployed to Vercel and talks to
// the Render backend via VITE_API_URL (see src/api/client.ts). There is no
// dev-server proxy: the app is never run locally.
export default defineConfig({
  plugins: [react()],
})
