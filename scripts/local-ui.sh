#!/usr/bin/env bash
set -euo pipefail

PID_FILE="${PID_FILE:-.local/vite.pid}"
LOG_FILE="${LOG_FILE:-.local/vite.log}"
PROJECT_PATH="${PROJECT_PATH:-ui}"

mkdir -p "$(dirname "$PID_FILE")"

if [[ -f "$PID_FILE" ]]; then
  if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "UI already running (pid $(cat "$PID_FILE"))."
    exit 0
  fi
  rm -f "$PID_FILE"
fi

if [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

UI_HOST="${UI_HOST:-0.0.0.0}"
UI_PORT="${UI_PORT:-5558}"
export VITE_API_BASE_URL="${VITE_API_BASE_URL:-http://localhost:5556}"

nohup npm --prefix "$PROJECT_PATH" run dev -- --host "$UI_HOST" --port "$UI_PORT" >"$LOG_FILE" 2>&1 &
echo $! >"$PID_FILE"
echo "UI started (pid $(cat "$PID_FILE")), log: $LOG_FILE"
