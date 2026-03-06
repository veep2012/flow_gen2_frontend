const AUTH_ERROR_STATUSES = new Set([400, 401]);

export class AuthResponseError extends Error {
  constructor({ status, detail, requestId, url }) {
    super(detail || `Authentication request failed (${status})`);
    this.name = "AuthResponseError";
    this.status = status;
    this.detail = detail || "";
    this.requestId = requestId || "";
    this.url = url || "";
  }
}

async function extractAuthDetail(response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    const payload = await response
      .clone()
      .json()
      .catch(() => null);
    const detail = payload?.detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail.trim();
    }
  }

  const text = await response
    .clone()
    .text()
    .catch(() => "");
  return text.trim();
}

export async function fetchWithAuthHandling(input, init = {}, options = {}) {
  const response = await fetch(input, init);
  if (!AUTH_ERROR_STATUSES.has(response.status)) {
    return response;
  }

  const authError = {
    status: response.status,
    detail: await extractAuthDetail(response),
    requestId: response.headers.get("X-Request-Id") || "",
    url: typeof input === "string" ? input : input?.url || "",
  };

  options.onAuthFailure?.(authError);
  throw new AuthResponseError(authError);
}

export function isAuthResponseError(error) {
  return error instanceof AuthResponseError;
}
