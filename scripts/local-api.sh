#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if [ ! -d ".venv" ]; then
  echo ".venv not found; run 'make local-venv' first." >&2
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate
export PYTHONPATH=api
exec uvicorn api.main:app --host 0.0.0.0 --port 5556 --reload
