import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "./",
  plugins: [react()],
  server: {
    allowedHosts: [".monkeycode-ai.online"],
    proxy: {
      "/api": process.env.VITE_API_PROXY_TARGET ?? "http://127.0.0.1:8010",
      },
  },
  build: {
    chunkSizeWarningLimit: 1500,
  },
});
