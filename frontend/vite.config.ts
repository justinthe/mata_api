import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/health": "http://api:8000",
      "/weeks": "http://api:8000",
      "/boundaries": "http://api:8000",
      "/fire": "http://api:8000",
      "/landslide": "http://api:8000",
      "/alerts": "http://api:8000",
      "/cells": "http://api:8000",
      "/generated": "http://api:8000",
      "/reports": "http://api:8000",
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/vitest.setup.ts"],
    globals: true,
  },
});
