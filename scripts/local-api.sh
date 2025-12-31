#!/usr/bin/env bash
set -euo pipefail

PID_FILE="${PID_FILE:-.local/uvicorn.pid}"
LOG_FILE="${LOG_FILE:-.local/uvicorn.log}"

mkdir -p "$(dirname "$PID_FILE")"

if [[ -f "$PID_FILE" ]]; then
  if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "API already running (pid $(cat "$PID_FILE"))."
    exit 0
  fi
  rm -f "$PID_FILE"
fi

PRESET_DATABASE_URL="${DATABASE_URL:-}"
PRESET_API_HOST="${API_HOST:-}"
PRESET_API_PORT="${API_PORT:-}"
PRESET_MINIO_ENDPOINT="${MINIO_ENDPOINT:-}"
PRESET_MINIO_BUCKET="${MINIO_BUCKET:-}"
PRESET_MINIO_ROOT_USER="${MINIO_ROOT_USER:-}"
PRESET_MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD:-}"
PRESET_MINIO_SECURE="${MINIO_SECURE:-}"

if [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

if [[ -n "$PRESET_DATABASE_URL" ]]; then
  export DATABASE_URL="$PRESET_DATABASE_URL"
fi
if [[ -n "$PRESET_API_HOST" ]]; then
  export API_HOST="$PRESET_API_HOST"
fi
if [[ -n "$PRESET_API_PORT" ]]; then
  export API_PORT="$PRESET_API_PORT"
fi
if [[ -n "$PRESET_MINIO_ENDPOINT" ]]; then
  export MINIO_ENDPOINT="$PRESET_MINIO_ENDPOINT"
fi
if [[ -n "$PRESET_MINIO_BUCKET" ]]; then
  export MINIO_BUCKET="$PRESET_MINIO_BUCKET"
fi
if [[ -n "$PRESET_MINIO_ROOT_USER" ]]; then
  export MINIO_ROOT_USER="$PRESET_MINIO_ROOT_USER"
fi
if [[ -n "$PRESET_MINIO_ROOT_PASSWORD" ]]; then
  export MINIO_ROOT_PASSWORD="$PRESET_MINIO_ROOT_PASSWORD"
fi
if [[ -n "$PRESET_MINIO_SECURE" ]]; then
  export MINIO_SECURE="$PRESET_MINIO_SECURE"
fi

if [[ -n "${MINIO_ENDPOINT:-}" ]]; then
  MINIO_ENDPOINT="${MINIO_ENDPOINT/host.containers.internal/localhost}"
  export MINIO_ENDPOINT
fi

API_HOST="${API_HOST:-0.0.0.0}"
API_PORT="${API_PORT:-5556}"
API_WAIT_TIMEOUT="${API_WAIT_TIMEOUT:-30}"

if [[ -d ".venv" ]]; then
  # shellcheck disable=SC1091
  . .venv/bin/activate
  export PYTHONPATH=api
elif ! command -v uvicorn >/dev/null 2>&1; then
  echo "uvicorn not found; run 'make local-venv' first." >&2
  exit 1
fi

nohup uvicorn api.main:app --reload --host "$API_HOST" --port "$API_PORT" >"$LOG_FILE" 2>&1 &
echo $! >"$PID_FILE"
echo "API started (pid $(cat "$PID_FILE")), log: $LOG_FILE"

HOST_FOR_CHECK="${API_HOST}"
if [[ "$HOST_FOR_CHECK" == "0.0.0.0" ]]; then
  HOST_FOR_CHECK="127.0.0.1"
fi
HEALTH_URL="http://${HOST_FOR_CHECK}:${API_PORT}/health"
export API_BASE="http://${HOST_FOR_CHECK}:${API_PORT}"
# Reuse the same health-check logic as Makefile-driven workflows.
PYTHON_CMD="python"
if ! command -v "$PYTHON_CMD" >/dev/null 2>&1; then
  PYTHON_CMD="python3"
fi
"$PYTHON_CMD" "$(dirname "$0")/wait-for-api.py"
status=$?
if [[ $status -ne 0 ]]; then
  echo "API not ready after ${API_WAIT_TIMEOUT}s: $HEALTH_URL"
  tail -n 50 "$LOG_FILE" || true
fi
exit $status
