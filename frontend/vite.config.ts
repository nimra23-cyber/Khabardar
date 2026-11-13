/// <reference types="vitest" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Vite + React config. The dev server binds to localhost only (local-only
// posture consistent with the backend); production build output goes to dist/.
export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    // Dev-only proxy: forward /api to the local backend so the SPA can call it
    // same-origin during development. Production uses VITE_API_BASE_URL.
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  test: {
    // Vitest runs in single-shot mode via `npm test` (vitest run).
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    css: true,
  },
});
