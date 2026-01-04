/**
 * Normalize and validate API base URL
 * @param {string} raw - Raw API base URL
 * @returns {string} - Normalized API base URL
 */
export const normalizeApiBase = (raw) => {
  const fallback = "/api/v1";
  const value = (raw || fallback).toString().trim();
  if (!value) return fallback;
  const hasProtocol = /^https?:\/\//i.test(value);
  const prepared = hasProtocol || value.startsWith("/") ? value : `http://${value}`;
  const trimmed = prepared.replace(/\/+$/, "");
  try {
    new URL(trimmed, window.location.origin);
    return trimmed;
  } catch (_err) {
    console.warn("Invalid VITE_API_BASE_URL, falling back to default /api/v1");
    return fallback;
  }
};
