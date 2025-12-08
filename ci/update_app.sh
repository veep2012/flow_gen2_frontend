#!/usr/bin/env bash

# Exit on error, unset variable, or failed pipeline
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LAST_COMMIT_FILE="$SCRIPT_DIR/.last_commit"

cd "$REPO_ROOT"

last_recorded=""
if [ -f "$LAST_COMMIT_FILE" ]; then
  last_recorded="$(cat "$LAST_COMMIT_FILE")"
fi

before_pull="$(git rev-parse HEAD)"

git pull --ff-only

after_pull="$(git rev-parse HEAD)"

# If no history yet, fall back to the pre-pull commit for comparison
if [ -z "$last_recorded" ]; then
  last_recorded="$before_pull"
fi

if [ "$after_pull" = "$last_recorded" ]; then
  echo "No new commits detected; nothing to do."
  exit 0
fi

echo "New commit detected ($last_recorded -> $after_pull). Restarting app..."

make app-down
make rebuild
make app-up

echo "$after_pull" > "$LAST_COMMIT_FILE"