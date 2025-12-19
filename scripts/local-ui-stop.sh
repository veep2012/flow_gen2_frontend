#!/usr/bin/env bash
set -euo pipefail

PID_FILE="${PID_FILE:-.local/vite.pid}"

if [ -f "$PID_FILE" ]; then
  PID=$(cat "$PID_FILE")
  if kill -0 "$PID" 2>/dev/null; then
    kill "$PID" || true
  fi
  rm -f "$PID_FILE"
else
  pkill -f "vite --host 0.0.0.0 --port 5558" || true
fi
