#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUNTIME_DIR="${PHASE1_RUNTIME_DIR:-$ROOT_DIR/.sim-runtime/phase-1}"
PX4_PID_FILE="$RUNTIME_DIR/px4_sitl.pid"
XRCE_PID_FILE="$RUNTIME_DIR/microxrce_agent.pid"

stop_pid_file() {
  local pid_file="$1"
  local pid

  [[ -f "$pid_file" ]] || return 0
  pid="$(cat "$pid_file")"

  if ! kill -0 "$pid" >/dev/null 2>&1; then
    rm -f "$pid_file"
    return 0
  fi

  kill -TERM -- "-$pid" >/dev/null 2>&1 || kill -TERM "$pid" >/dev/null 2>&1 || true

  for _ in $(seq 1 15); do
    if ! kill -0 "$pid" >/dev/null 2>&1; then
      rm -f "$pid_file"
      return 0
    fi
    sleep 1
  done

  kill -KILL -- "-$pid" >/dev/null 2>&1 || kill -KILL "$pid" >/dev/null 2>&1 || true
  rm -f "$pid_file"
}

main() {
  cd "$ROOT_DIR"

  if [[ "${1:-}" == "--check" ]]; then
    echo "Check mode: stop contract is valid."
    exit 0
  fi

  stop_pid_file "$PX4_PID_FILE"
  stop_pid_file "$XRCE_PID_FILE"
  rmdir "$RUNTIME_DIR" 2>/dev/null || true

  if [[ "$RUNTIME_DIR" == "$ROOT_DIR/.sim-runtime/phase-1" ]]; then
    rmdir "$ROOT_DIR/.sim-runtime" 2>/dev/null || true
  fi

  echo "Phase 1 stack stopped."
}

main "$@"
