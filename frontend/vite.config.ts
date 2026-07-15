import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Direct CORS calls to the backend (no dev proxy) so dev and prod share
// the same networking model - see backend/.env's CORS_ALLOWED_ORIGINS.
// Port is pinned so the CORS allowlist (a literal string match) can
// never silently break by Vite picking 5174 instead.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
  },
});
