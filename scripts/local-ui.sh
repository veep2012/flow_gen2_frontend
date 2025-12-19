#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="${PID_FILE:-${ROOT}/.local/vite.pid}"
cd "$ROOT/ui"

export VITE_API_BASE_URL="${VITE_API_BASE_URL:-http://localhost:5556/api/v1}"

mkdir -p "$(dirname "$PID_FILE")"
npm run dev &
echo $! > "$PID_FILE"
disown
