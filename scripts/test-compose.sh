#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
NGINX_BASE_URL="${NGINX_BASE_URL:-http://localhost}"
KEYCLOAK_BASE_URL="${KEYCLOAK_BASE_URL:-http://localhost:8081}"
COMPOSE_TEST_USERNAME="${COMPOSE_TEST_USERNAME:-fdqc}"
COMPOSE_TEST_PASSWORD="${COMPOSE_TEST_PASSWORD:-fdqc}"
COMPOSE_TEST_EXPECTED_ACRONYM="${COMPOSE_TEST_EXPECTED_ACRONYM:-FDQC}"

log_step() {
  echo "[test-compose] $1"
}

wait_for_url() {
  local url="$1"
  local label="$2"

  log_step "Waiting for $label: $url"
  for _ in $(seq 1 60); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      log_step "$label is ready"
      return 0
    fi
    sleep 2
  done

  echo "$label did not become ready: $url" >&2
  exit 1
}

log_step "Starting compose auth smoke"
log_step "Using nginx base URL: $NGINX_BASE_URL"
log_step "Using Keycloak base URL: $KEYCLOAK_BASE_URL"

wait_for_url "$KEYCLOAK_BASE_URL/realms/flow-local/.well-known/openid-configuration" "Keycloak"
wait_for_url "$NGINX_BASE_URL/favicon.svg" "Nginx"

redirect_headers="$(mktemp)"
cleanup() {
  rm -f "$redirect_headers"
}
trap cleanup EXIT

log_step "Checking unauthenticated API ingress redirects into the auth flow"
curl -sS -D "$redirect_headers" -o /dev/null \
  "$NGINX_BASE_URL/api/v1/people/users/current_user"

if ! grep -Eqi '^location: .*/protocol/openid-connect/auth' "$redirect_headers"; then
  echo "Expected unauthenticated API ingress to redirect into the Keycloak auth flow" >&2
  exit 1
fi
log_step "Unauthenticated ingress redirect check passed"

log_step "Requesting Keycloak access token for test user '$COMPOSE_TEST_USERNAME'"
access_token="$(
  curl -fsS -X POST "$KEYCLOAK_BASE_URL/realms/flow-local/protocol/openid-connect/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data "grant_type=password" \
    --data "client_id=flow-ui" \
    --data "username=$COMPOSE_TEST_USERNAME" \
    --data "password=$COMPOSE_TEST_PASSWORD" |
    "$PYTHON_BIN" -c 'import json,sys; print(json.load(sys.stdin)["access_token"])'
)"
log_step "Access token acquired"

log_step "Checking bearer-token passthrough through nginx"
bearer_payload="$(
  curl -fsS -H "Authorization: Bearer $access_token" \
    "$NGINX_BASE_URL/api/v1/people/users/current_user"
)"
COMPOSE_TEST_EXPECTED_ACRONYM="$COMPOSE_TEST_EXPECTED_ACRONYM" \
"$PYTHON_BIN" -c 'import json, os, sys; assert json.load(sys.stdin)["user_acronym"] == os.environ["COMPOSE_TEST_EXPECTED_ACRONYM"]' \
  <<<"$bearer_payload"
log_step "Bearer-token passthrough check passed"

log_step "Checking invalid bearer token fails closed"
invalid_status="$(
  curl -sS -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer invalid-token" \
    "$NGINX_BASE_URL/api/v1/people/users/current_user"
)"
if [[ "$invalid_status" != "401" ]]; then
  echo "Expected invalid bearer token to return 401, got $invalid_status" >&2
  exit 1
fi
log_step "Invalid bearer token check passed"

log_step "Checking cookie-based login flow through oauth2-proxy and Keycloak"
NGINX_BASE_URL="$NGINX_BASE_URL" \
COMPOSE_TEST_USERNAME="$COMPOSE_TEST_USERNAME" \
COMPOSE_TEST_PASSWORD="$COMPOSE_TEST_PASSWORD" \
COMPOSE_TEST_EXPECTED_ACRONYM="$COMPOSE_TEST_EXPECTED_ACRONYM" \
"$PYTHON_BIN" <<'PY'
import html
import json
import os
import re
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar

base_url = os.environ["NGINX_BASE_URL"].rstrip("/")
username = os.environ["COMPOSE_TEST_USERNAME"]
password = os.environ["COMPOSE_TEST_PASSWORD"]
expected = os.environ["COMPOSE_TEST_EXPECTED_ACRONYM"]
protected_url = f"{base_url}/api/v1/people/users/current_user"

cookie_jar = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
response = opener.open(protected_url)
page = response.read().decode("utf-8", errors="replace")
match = re.search(r'action="([^"]*login-actions/authenticate[^"]*)"', page)
if not match:
    raise SystemExit("Could not locate Keycloak login form action")
action_url = urllib.parse.urljoin(response.geturl(), html.unescape(match.group(1)))
payload = urllib.parse.urlencode(
    {"username": username, "password": password, "credentialId": ""}
).encode()
final_response = opener.open(action_url, data=payload)
body = final_response.read().decode("utf-8", errors="replace")
if "application/json" not in final_response.headers.get("Content-Type", ""):
    raise SystemExit(f"Expected JSON after cookie login, got {final_response.geturl()}")
data = json.loads(body)
if data.get("user_acronym") != expected:
    raise SystemExit(f"Unexpected cookie-auth user payload: {data!r}")
PY
log_step "Cookie-based login flow check passed"

log_step "Compose auth smoke passed"
