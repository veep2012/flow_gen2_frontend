#!/usr/bin/env bash
set -euo pipefail

PID_FILE="${PID_FILE:-.local/vite.pid}"
UI_PORT="${UI_PORT:-5558}"
STOP_TIMEOUT_SEC="${STOP_TIMEOUT_SEC:-10}"

stop_pid() {
  local pid="$1"
  if ! kill -0 "$pid" 2>/dev/null; then
    return 0
  fi
  kill "$pid" 2>/dev/null || true
  for _ in $(seq 1 "$STOP_TIMEOUT_SEC"); do
    if ! kill -0 "$pid" 2>/dev/null; then
      return 0
    fi
    sleep 1
  done
  kill -9 "$pid" 2>/dev/null || true
}

stop_port_processes() {
  local port="$1"
  if ! command -v lsof >/dev/null 2>&1; then
    return 0
  fi
  local pids
  pids="$(lsof -ti tcp:"$port" 2>/dev/null || true)"
  if [[ -z "$pids" ]]; then
    return 0
  fi
  for pid in $pids; do
    stop_pid "$pid"
  done
}

stop_port_processes "$UI_PORT"

if [[ -f "$PID_FILE" ]]; then
  PID="$(cat "$PID_FILE")"
  if kill -0 "$PID" 2>/dev/null; then
    stop_pid "$PID"
    echo "UI stopped (pid $PID)."
  else
    echo "UI process not running; removing PID file."
  fi
  rm -f "$PID_FILE"
else
  echo "UI PID file not found."
fi
