import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "/test_api/",
  server: {
    host: "0.0.0.0",
    port: 5557,
    allowedHosts: ["flow_ui", "flow_ui_test"],
  },
  preview: {
    allowedHosts: ["flow_ui", "flow_ui_test"],
  },
});
