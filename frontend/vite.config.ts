import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Direct CORS calls to the backend (no dev proxy) so dev and prod share
// the same networking model - see backend/.env's CORS_ALLOWED_ORIGINS.
// Port is pinned so the CORS allowlist (a literal string match) can
// never silently break by Vite picking 5174 instead.
//
// Host is pinned to the IPv4 loopback (matching uvicorn's default
// bind) rather than left to resolve "localhost" - Vite's default
// otherwise binds IPv6-only ([::1]), which is unreachable via
// http://127.0.0.1:5173 and, on hosts where IPv6 loopback isn't
// usable (some container/sandboxed networks), unreachable via
// "localhost" too. The browser's Origin header still reports whatever
// hostname is in the address bar, so this doesn't affect the
// CORS_ALLOWED_ORIGINS match above.
export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
  },
});
