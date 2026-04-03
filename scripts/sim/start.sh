#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PX4_DIR="$ROOT_DIR/third_party/PX4-Autopilot"
RUNTIME_DIR="${PHASE1_RUNTIME_DIR:-$ROOT_DIR/.sim-runtime/phase-1}"
LOG_DIR="${PHASE1_LOG_DIR:-$ROOT_DIR/.sim-logs/phase-1}"
GZ_DISTRO="${PHASE1_GZ_DISTRO:-harmonic}"
GZ_PARTITION="${PHASE1_GZ_PARTITION:-drone-sim-phase1}"
XRCE_AGENT_BIN="${MICRO_XRCE_AGENT_BIN:-MicroXRCEAgent}"
XRCE_AGENT_ARGS="${MICRO_XRCE_AGENT_ARGS:-udp4 -p 8888}"
XRCE_AGENT_LD_LIBRARY_PATH="${MICRO_XRCE_AGENT_LD_LIBRARY_PATH:-}"
PX4_SITL_MAKE_ARGS="${PX4_SITL_MAKE_ARGS:-}"
PX4_PID_FILE="$RUNTIME_DIR/px4_sitl.pid"
XRCE_PID_FILE="$RUNTIME_DIR/microxrce_agent.pid"
PX4_LOG_FILE="$LOG_DIR/px4_sitl.log"
XRCE_LOG_FILE="$LOG_DIR/microxrce_agent.log"

mkdir -p "$RUNTIME_DIR" "$LOG_DIR"

die() {
  printf 'phase-1 start failed: %s\n' "$1" >&2
  exit 1
}

require_cmd() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || die "missing required command: $cmd"
}

require_binary() {
  local binary="$1"
  if [[ "$binary" == */* ]]; then
    [[ -x "$binary" ]] || die "missing executable binary: $binary"
  else
    require_cmd "$binary"
  fi
}

check_git_state() {
  [[ -d "$PX4_DIR" ]] || die "missing PX4 submodule directory: third_party/PX4-Autopilot"

  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git config -f "$ROOT_DIR/.gitmodules" --get submodule.third_party/PX4-Autopilot.path >/dev/null 2>&1 || die "third_party/PX4-Autopilot is not declared in .gitmodules"
  fi

  if [[ -d "$PX4_DIR/.git" ]] || git -C "$PX4_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    local tag
    tag="$(git -C "$PX4_DIR" describe --tags --exact-match 2>/dev/null || true)"
    [[ "$tag" == "v1.16.1" ]] || die "PX4 submodule must be pinned to v1.16.1"
  fi
}

check_runtime_clean() {
  [[ ! -e "$PX4_PID_FILE" ]] || die "runtime already active; stop it first with scripts/sim/stop.sh"
  [[ ! -e "$XRCE_PID_FILE" ]] || die "runtime already active; stop it first with scripts/sim/stop.sh"
}

print_plan() {
 cat <<EOF
Phase 1 startup plan:
1. Start Micro XRCE-DDS Agent on udp4 port 8888
2. Start PX4 SITL + Gazebo Harmonic in headless mode with GZ_DISTRO=$GZ_DISTRO GZ_PARTITION=$GZ_PARTITION HEADLESS=1 make px4_sitl gz_x500
3. Track PIDs in $RUNTIME_DIR
4. Capture logs in $LOG_DIR
EOF
}

ensure_alive() {
  local pid_file="$1"
  local label="$2"
  local pid
  [[ -f "$pid_file" ]] || die "$label did not create a pid file"
  pid="$(cat "$pid_file")"
  if ! kill -0 "$pid" >/dev/null 2>&1; then
    die "$label exited immediately; inspect logs in $LOG_DIR"
  fi
}

start_agent() {
  require_binary "$XRCE_AGENT_BIN"
  if [[ -n "$XRCE_AGENT_LD_LIBRARY_PATH" ]]; then
    setsid bash -lc "cd \"$ROOT_DIR\" && export LD_LIBRARY_PATH=\"$XRCE_AGENT_LD_LIBRARY_PATH\${LD_LIBRARY_PATH:+:\$LD_LIBRARY_PATH}\" && exec \"$XRCE_AGENT_BIN\" $XRCE_AGENT_ARGS" >"$XRCE_LOG_FILE" 2>&1 &
  else
    setsid bash -lc "cd \"$ROOT_DIR\" && exec \"$XRCE_AGENT_BIN\" $XRCE_AGENT_ARGS" >"$XRCE_LOG_FILE" 2>&1 &
  fi
  echo $! >"$XRCE_PID_FILE"
}

start_px4() {
  require_cmd make
  require_cmd gz
  require_cmd python3
  setsid bash -lc "cd \"$PX4_DIR\" && exec env GZ_DISTRO=\"$GZ_DISTRO\" GZ_PARTITION=\"$GZ_PARTITION\" HEADLESS=1 make $PX4_SITL_MAKE_ARGS px4_sitl gz_x500" >"$PX4_LOG_FILE" 2>&1 &
  echo $! >"$PX4_PID_FILE"
}

main() {
  cd "$ROOT_DIR"
  check_git_state

  if [[ "${1:-}" == "--check" ]]; then
    print_plan
    echo "Check mode only; no processes were started."
    exit 0
  fi

  require_cmd git
  require_cmd make
  require_cmd python3
  require_cmd setsid
  require_cmd kill
  require_cmd sleep
  require_cmd awk
  require_cmd sed
  require_cmd grep
  check_runtime_clean
  print_plan

  start_agent
  sleep 1
  ensure_alive "$XRCE_PID_FILE" "Micro XRCE-DDS Agent"

  start_px4
  sleep 3
  ensure_alive "$PX4_PID_FILE" "PX4 SITL + Gazebo Harmonic"

  cat <<EOF
Phase 1 stack started.
PX4 PID file: $PX4_PID_FILE
XRCE PID file: $XRCE_PID_FILE
Logs: $LOG_DIR
EOF
}

main "$@"
