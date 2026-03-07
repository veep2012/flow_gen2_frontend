#!/usr/bin/env sh
set -eu

COMMAND="${1:-}"
WORKDIR="${WORKDIR:-/workspace/ui}"
LOCKFILE="$WORKDIR/package-lock.json"
MARKER="$WORKDIR/node_modules/.package-lock.sha256"
LOCKDIR="$WORKDIR/node_modules/.install.lock"

if [ -z "$COMMAND" ]; then
  echo "Usage: $0 <install|dev|test|test-e2e|lint|build|audit>" >&2
  exit 1
fi

hash_file() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

has_script() {
  node -e "const scripts=require('./package.json').scripts||{}; process.exit(scripts['$1'] ? 0 : 1)"
}

ensure_deps() {
  mkdir -p "$WORKDIR/node_modules"

  while ! mkdir "$LOCKDIR" >/dev/null 2>&1; do
    sleep 1
  done
  trap 'rmdir "$LOCKDIR" >/dev/null 2>&1 || true' EXIT INT TERM

  current_hash="$(hash_file "$LOCKFILE")"
  saved_hash=""

  if [ -f "$MARKER" ]; then
    saved_hash="$(cat "$MARKER")"
  fi

  if [ ! -d "$WORKDIR/node_modules" ] || [ "$saved_hash" != "$current_hash" ]; then
    echo "Refreshing UI dependencies with npm ci"
    npm ci
    mkdir -p "$WORKDIR/node_modules"
    printf '%s\n' "$current_hash" > "$MARKER"
  fi

  rmdir "$LOCKDIR" >/dev/null 2>&1 || true
  trap - EXIT INT TERM
}

cd "$WORKDIR"

case "$COMMAND" in
  install)
    ensure_deps
    ;;
  dev)
    ensure_deps
    exec npm run dev
    ;;
  test)
    if has_script test; then
      ensure_deps
      exec npm test
    fi
    echo "Skipping local-ui-test: ui/package.json has no 'test' script"
    ;;
  test-e2e)
    if has_script test:e2e; then
      ensure_deps
      exec npm run test:e2e
    fi
    echo "Skipping test-ui-e2e: ui/package.json has no 'test:e2e' script"
    ;;
  lint)
    ensure_deps
    npm run lint
    exec npm run format
    ;;
  build)
    ensure_deps
    exec npm run build
    ;;
  audit)
    ensure_deps
    exec npm audit --package-lock-only
    ;;
  *)
    echo "Unknown command: $COMMAND" >&2
    exit 1
    ;;
esac
