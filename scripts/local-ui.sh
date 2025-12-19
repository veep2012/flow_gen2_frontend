#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/ui"

export VITE_API_BASE_URL="${VITE_API_BASE_URL:-http://localhost:5556/api/v1}"
exec npm run dev
