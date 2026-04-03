#!/usr/bin/env bash
set -euo pipefail

COMMAND="${1:-}"

if [[ -z "$COMMAND" ]]; then
  echo "Usage: $0 <up|down|logs>" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

CONTAINER_ENGINE="${CONTAINER_ENGINE:-podman}"
API_CONTAINER_NAME="${API_CONTAINER_NAME:-flow_gen2_api_local}"
API_IMAGE="${API_IMAGE:-localhost/flow_gen2_api:latest}"
API_PORT="${API_PORT:-5556}"
API_WAIT_TIMEOUT="${API_WAIT_TIMEOUT:-30}"
APP_ENV="${APP_ENV:-local}"
APP_USER="${APP_USER:-KONI}"
ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-http://localhost,http://localhost:5558,http://127.0.0.1:5558}"
APP_DB_USER="${APP_DB_USER:-app_user}"
APP_DB_PASSWORD="${APP_DB_PASSWORD:-app_pass}"
POSTGRES_DB="${POSTGRES_DB:-flow_db}"
DB_PORT="${DB_PORT:-5432}"
MINIO_PORT="${MINIO_PORT:-9000}"
MINIO_BUCKET="${MINIO_BUCKET:-flow-default}"
MINIO_ROOT_USER="${MINIO_ROOT_USER:-flow_minio}"
MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD:-change_me_now}"
HOST_INTERNAL_NAME="${HOST_INTERNAL_NAME:-host.containers.internal}"

if [[ -f "$REPO_ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "$REPO_ROOT/.env"
  set +a
fi

container_exists() {
  "$CONTAINER_ENGINE" inspect "$API_CONTAINER_NAME" >/dev/null 2>&1
}

container_is_running() {
  [ "$("$CONTAINER_ENGINE" inspect -f '{{.State.Running}}' "$API_CONTAINER_NAME" 2>/dev/null || true)" = "true" ]
}

ensure_container_absent() {
  if container_exists; then
    "$CONTAINER_ENGINE" rm -f "$API_CONTAINER_NAME" >/dev/null 2>&1 || true
  fi
}

wait_for_health() {
  local health_url="http://127.0.0.1:${API_PORT}/health"

  for _ in $(seq 1 "$API_WAIT_TIMEOUT"); do
    if curl -fsS "$health_url" >/dev/null 2>&1; then
      echo "API ready: $health_url"
      return 0
    fi
    sleep 1
  done

  echo "API not ready after ${API_WAIT_TIMEOUT}s: $health_url" >&2
  "$CONTAINER_ENGINE" logs "$API_CONTAINER_NAME" || true
  return 1
}

case "$COMMAND" in
  up)
    if container_is_running; then
      echo "API container already running: $API_CONTAINER_NAME"
      exit 0
    fi

    ensure_container_absent

    "$CONTAINER_ENGINE" run -d \
      --name "$API_CONTAINER_NAME" \
      --pull=never \
      -p "${API_PORT}:5556" \
      -e PORT=5556 \
      -e APP_ENV="$APP_ENV" \
      -e APP_USER="$APP_USER" \
      -e ALLOWED_ORIGINS="$ALLOWED_ORIGINS" \
      -e APP_DB_USER="$APP_DB_USER" \
      -e APP_DB_PASSWORD="$APP_DB_PASSWORD" \
      -e APP_DATABASE_URL="postgresql+psycopg://${APP_DB_USER}:${APP_DB_PASSWORD}@${HOST_INTERNAL_NAME}:${DB_PORT}/${POSTGRES_DB}" \
      -e MINIO_ENDPOINT="http://${HOST_INTERNAL_NAME}:${MINIO_PORT}" \
      -e MINIO_BUCKET="$MINIO_BUCKET" \
      -e MINIO_ROOT_USER="$MINIO_ROOT_USER" \
      -e MINIO_ROOT_PASSWORD="$MINIO_ROOT_PASSWORD" \
      "$API_IMAGE" >/dev/null

    wait_for_health
    ;;
  down)
    if ! container_exists; then
      echo "API container not found: $API_CONTAINER_NAME"
      exit 0
    fi

    exec "$CONTAINER_ENGINE" rm -f "$API_CONTAINER_NAME"
    ;;
  logs)
    exec "$CONTAINER_ENGINE" logs -f "$API_CONTAINER_NAME"
    ;;
  *)
    echo "Unknown command: $COMMAND" >&2
    exit 1
    ;;
esac
