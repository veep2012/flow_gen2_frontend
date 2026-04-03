import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

const DEFAULT_ALLOWED_HOSTS = [
  "flow_ui",
  "frontend",
  "flow_frontend",
  "localhost",
  "127.0.0.1",
];

function resolveAllowedHosts(rawValue) {
  if (!rawValue) {
    return DEFAULT_ALLOWED_HOSTS;
  }

  const configuredHosts = rawValue
    .split(",")
    .map((host) => host.trim())
    .filter(Boolean);

  return configuredHosts.length > 0 ? configuredHosts : DEFAULT_ALLOWED_HOSTS;
}

const allowedHosts = resolveAllowedHosts(process.env.VITE_ALLOWED_HOSTS);

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "happy-dom",
    setupFiles: "./src/test/setupTests.js",
  },
  server: {
    host: true,
    port: 5558,
    allowedHosts,
  },
  preview: {
    host: true,
    port: 5558,
    allowedHosts,
  },
});
