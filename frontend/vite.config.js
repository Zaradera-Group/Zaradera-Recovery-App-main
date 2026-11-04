import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In dev, requests to /api are proxied to the local FastAPI server so the
// frontend can just call fetch("/api/...") without hardcoding a host.
// In production, set VITE_API_BASE_URL (see .env.example) to the real API URL.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
