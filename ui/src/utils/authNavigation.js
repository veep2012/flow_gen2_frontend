export function resolveAuthStartBase(rawValue) {
  const value = String(rawValue || "").trim();
  if (!value) {
    return "/oauth2/start";
  }
  try {
    return new URL(value, window.location.origin).toString();
  } catch {
    console.warn("Invalid VITE_AUTH_START_URL, falling back to /oauth2/start");
    return "/oauth2/start";
  }
}

export function buildReauthUrl(authStartBase, redirectPath) {
  const target = new URL(authStartBase, window.location.origin);
  target.searchParams.set("rd", redirectPath || "/");
  return target.toString();
}

export function buildLogoutForUserSwitchUrl(authStartBase, redirectPath) {
  const authStartUrl = buildReauthUrl(authStartBase, redirectPath);
  const signOutUrl = new URL(authStartBase, window.location.origin);
  signOutUrl.pathname = "/oauth2/sign_out";
  signOutUrl.search = "";
  signOutUrl.hash = "";
  signOutUrl.searchParams.set("rd", authStartUrl);
  return signOutUrl.toString();
}
