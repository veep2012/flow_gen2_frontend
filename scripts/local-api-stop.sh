#!/usr/bin/env bash
set -euo pipefail

PID_FILE="${PID_FILE:-.local/uvicorn.pid}"

if [ -f "$PID_FILE" ]; then
  PID=$(cat "$PID_FILE")
  if kill -0 "$PID" 2>/dev/null; then
    kill "$PID" || true
  fi
  rm -f "$PID_FILE"
else
  pkill -f "uvicorn api.main:app --host 0.0.0.0 --port 5556" || true
fi
