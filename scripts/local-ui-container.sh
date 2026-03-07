#!/usr/bin/env bash
set -euo pipefail

COMMAND="${1:-}"
SUBCOMMAND="${2:-}"

if [[ -z "$COMMAND" ]]; then
  echo "Usage: $0 <up|down|logs|reset|hard-reset|run> [subcommand]" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

CONTAINER_ENGINE="${CONTAINER_ENGINE:-podman}"
UI_CONTAINER_NAME="${UI_CONTAINER_NAME:-flow_gen2_ui_local}"
UI_NODE_IMAGE="${UI_NODE_IMAGE:-node:22.14.0-alpine}"
UI_NODE_MODULES_VOLUME="${UI_NODE_MODULES_VOLUME:-flow_gen2_ui_node_modules}"
UI_PORT="${UI_PORT:-5558}"
UI_HOST="${UI_HOST:-0.0.0.0}"
WORKSPACE_PATH="/workspace"

if [[ -f "$REPO_ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "$REPO_ROOT/.env"
  set +a
fi

container_exists() {
  "$CONTAINER_ENGINE" inspect "$UI_CONTAINER_NAME" >/dev/null 2>&1
}

container_is_running() {
  [ "$("$CONTAINER_ENGINE" inspect -f '{{.State.Running}}' "$UI_CONTAINER_NAME" 2>/dev/null || true)" = "true" ]
}

ensure_container_absent() {
  if container_exists; then
    "$CONTAINER_ENGINE" rm -f "$UI_CONTAINER_NAME" >/dev/null 2>&1 || true
  fi
}

runtime_env_args=(
  -e "UI_HOST=$UI_HOST"
  -e "UI_PORT=$UI_PORT"
)

if [[ -n "${VITE_API_BASE_URL:-}" ]]; then
  runtime_env_args+=(-e "VITE_API_BASE_URL=$VITE_API_BASE_URL")
fi

if [[ -n "${VITE_AUTH_START_URL:-}" ]]; then
  runtime_env_args+=(-e "VITE_AUTH_START_URL=$VITE_AUTH_START_URL")
fi

if [[ -n "${PLAYWRIGHT_PORT:-}" ]]; then
  runtime_env_args+=(-e "PLAYWRIGHT_PORT=$PLAYWRIGHT_PORT")
fi

if [[ -n "${TEST_API_PORT:-}" ]]; then
  runtime_env_args+=(-e "TEST_API_PORT=$TEST_API_PORT")
fi

case "$COMMAND" in
  up)
    if container_is_running; then
      echo "UI container already running: $UI_CONTAINER_NAME"
      exit 0
    fi

    ensure_container_absent

    exec "$CONTAINER_ENGINE" run -d \
      --name "$UI_CONTAINER_NAME" \
      -p "$UI_PORT:$UI_PORT" \
      -w "$WORKSPACE_PATH/ui" \
      -v "$REPO_ROOT:$WORKSPACE_PATH" \
      -v "$UI_NODE_MODULES_VOLUME:$WORKSPACE_PATH/ui/node_modules" \
      "${runtime_env_args[@]}" \
      "$UI_NODE_IMAGE" \
      sh "$WORKSPACE_PATH/scripts/local-ui-runtime.sh" dev
    ;;
  down)
    if ! container_exists; then
      echo "UI container not found: $UI_CONTAINER_NAME"
      exit 0
    fi

    exec "$CONTAINER_ENGINE" rm -f "$UI_CONTAINER_NAME"
    ;;
  logs)
    exec "$CONTAINER_ENGINE" logs -f "$UI_CONTAINER_NAME"
    ;;
  reset)
    ensure_container_absent
    "$CONTAINER_ENGINE" volume rm "$UI_NODE_MODULES_VOLUME" >/dev/null 2>&1 || true
    echo "Reset UI container and dependency volume."
    ;;
  hard-reset)
    ensure_container_absent
    "$CONTAINER_ENGINE" volume rm "$UI_NODE_MODULES_VOLUME" >/dev/null 2>&1 || true
    "$CONTAINER_ENGINE" image rm "$UI_NODE_IMAGE" >/dev/null 2>&1 || true
    echo "Removed UI container, dependency volume, and image."
    ;;
  run)
    if [[ -z "$SUBCOMMAND" ]]; then
      echo "Usage: $0 run <install|test|test-e2e|lint|build|audit>" >&2
      exit 1
    fi

    exec "$CONTAINER_ENGINE" run --rm \
      -w "$WORKSPACE_PATH/ui" \
      -v "$REPO_ROOT:$WORKSPACE_PATH" \
      -v "$UI_NODE_MODULES_VOLUME:$WORKSPACE_PATH/ui/node_modules" \
      "${runtime_env_args[@]}" \
      "$UI_NODE_IMAGE" \
      sh "$WORKSPACE_PATH/scripts/local-ui-runtime.sh" "$SUBCOMMAND"
    ;;
  *)
    echo "Unknown command: $COMMAND" >&2
    exit 1
    ;;
esac
