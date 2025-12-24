#!/usr/bin/env bash
set -euo pipefail

PID_FILE="${PID_FILE:-.local/uvicorn.pid}"

if [[ ! -f "$PID_FILE" ]]; then
  echo "API PID file not found."
  exit 0
fi

PID="$(cat "$PID_FILE")"
if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  echo "API stopped (pid $PID)."
else
  echo "API process not running; removing PID file."
fi

rm -f "$PID_FILE"
