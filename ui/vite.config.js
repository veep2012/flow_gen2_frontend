import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
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
