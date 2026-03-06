import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "happy-dom",
    setupFiles: "./src/test/setupTests.js",
  },
  server: {
    host: true,
    port: 5558,
    allowedHosts: ["flow_ui"],
  },
  preview: {
    host: true,
    port: 5558,
    allowedHosts: ["flow_ui"],
  },
});
