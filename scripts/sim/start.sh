#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PX4_DIR="$ROOT_DIR/third_party/PX4-Autopilot"
PX4_BUILD_DIR="$PX4_DIR/build/px4_sitl_default"
PX4_BIN_DIR="$PX4_BUILD_DIR/bin"
PX4_BIN="$PX4_BIN_DIR/px4"
RUNTIME_DIR="${PHASE1_RUNTIME_DIR:-$ROOT_DIR/.sim-runtime/phase-1}"
LOG_DIR="${PHASE1_LOG_DIR:-$ROOT_DIR/.sim-logs/phase-1}"
GZ_DISTRO="${PHASE1_GZ_DISTRO:-harmonic}"
GZ_PARTITION="${PHASE1_GZ_PARTITION:-drone-sim-phase1}"
HEADLESS_MODE="${PHASE1_HEADLESS:-1}"
PYTHON_BIN="${PHASE1_PYTHON_BIN:-python3}"
XRCE_AGENT_BIN="${MICRO_XRCE_AGENT_BIN:-MicroXRCEAgent}"
XRCE_AGENT_ARGS="${MICRO_XRCE_AGENT_ARGS:-udp4 -p 8888}"
XRCE_AGENT_LD_LIBRARY_PATH="${MICRO_XRCE_AGENT_LD_LIBRARY_PATH:-}"
PX4_SITL_MAKE_ARGS="${PX4_SITL_MAKE_ARGS:-}"
PX4_PID_FILE="$RUNTIME_DIR/px4_sitl.pid"
XRCE_PID_FILE="$RUNTIME_DIR/microxrce_agent.pid"
PX4_LOG_FILE="$LOG_DIR/px4_sitl.log"
XRCE_LOG_FILE="$LOG_DIR/microxrce_agent.log"
GZ_GSTREAMER_PLUGIN="$PX4_BUILD_DIR/src/modules/simulation/gz_plugins/libGstCameraSystem.so"

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

require_python_module() {
  local module="$1"
  "$PYTHON_BIN" - <<PY >/dev/null 2>&1 || die "missing required Python module: $module (create .venv and install with: $PYTHON_BIN -m pip install $module)"
import importlib
importlib.import_module("$module")
PY
}

require_python_snippet() {
  local description="$1"
  local snippet="$2"
  "$PYTHON_BIN" - <<PY >/dev/null 2>&1 || die "$description (sync with: $PYTHON_BIN -m pip install -r $PX4_DIR/Tools/setup/requirements.txt)"
$snippet
PY
}

require_opencv_dev() {
  require_cmd pkg-config
  pkg-config --exists opencv4 || die "missing required OpenCV development package: install libopencv-dev"
}

resolve_python_defaults() {
  local local_venv_python="$ROOT_DIR/.venv/bin/python"

  if [[ -n "${PHASE1_PYTHON_BIN:-}" ]]; then
    return 0
  fi

  if [[ -x "$local_venv_python" ]]; then
    PYTHON_BIN="$local_venv_python"
  fi
}

normalize_python_bin() {
  if [[ "$PYTHON_BIN" == */* ]]; then
    return 0
  fi

  local resolved
  resolved="$(command -v "$PYTHON_BIN" 2>/dev/null || true)"
  [[ -n "$resolved" ]] || die "missing required command: $PYTHON_BIN"
  PYTHON_BIN="$resolved"
}

resolve_xrce_agent_defaults() {
  local cached_install_bin="$ROOT_DIR/.cache/phase-1/micro-xrce-agent/install/bin/MicroXRCEAgent"
  local cached_install_lib="$ROOT_DIR/.cache/phase-1/micro-xrce-agent/install/lib"
  local cached_build_bin="$ROOT_DIR/.cache/phase-1/micro-xrce-agent/build/MicroXRCEAgent"

  if [[ -n "${MICRO_XRCE_AGENT_BIN:-}" ]]; then
    return 0
  fi

  if command -v "$XRCE_AGENT_BIN" >/dev/null 2>&1; then
    return 0
  fi

  if [[ -x "$cached_install_bin" ]]; then
    XRCE_AGENT_BIN="$cached_install_bin"
    if [[ -z "$XRCE_AGENT_LD_LIBRARY_PATH" && -d "$cached_install_lib" ]]; then
      XRCE_AGENT_LD_LIBRARY_PATH="$cached_install_lib"
    fi
    return 0
  fi

  if [[ -x "$cached_build_bin" ]]; then
    XRCE_AGENT_BIN="$cached_build_bin"
    return 0
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

clean_stale_pid_file() {
  local pid_file="$1"
  local label="$2"
  local pid

  [[ -e "$pid_file" ]] || return 0
  pid="$(cat "$pid_file" 2>/dev/null || true)"

  if [[ -n "$pid" ]] && kill -0 "$pid" >/dev/null 2>&1; then
    die "$label already active; stop it first with scripts/sim/stop.sh"
  fi

  rm -f "$pid_file"
}

check_runtime_clean() {
  clean_stale_pid_file "$PX4_PID_FILE" "PX4 SITL + Gazebo Harmonic"
  clean_stale_pid_file "$XRCE_PID_FILE" "Micro XRCE-DDS Agent"
}

print_plan() {
 cat <<EOF
Phase 1 startup plan:
1. Start Micro XRCE-DDS Agent on udp4 port 8888
2. Build PX4 SITL artifacts deterministically with px4_sitl_default
3. Start PX4 SITL + Gazebo Harmonic with GZ_DISTRO=$GZ_DISTRO GZ_PARTITION=$GZ_PARTITION HEADLESS=$HEADLESS_MODE
4. Track PIDs in $RUNTIME_DIR
5. Capture logs in $LOG_DIR
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

build_px4() {
  local -a env_args
  local python_dir
  env_args=(
    "GZ_DISTRO=$GZ_DISTRO"
    "GZ_PARTITION=$GZ_PARTITION"
    "PX4_SIM_MODEL=gz_x500"
    "GZ_IP=127.0.0.1"
    "DONT_RUN=1"
    "PYTHON_EXECUTABLE=$PYTHON_BIN"
  )
  python_dir="$(dirname "$PYTHON_BIN")"

  if [[ "$HEADLESS_MODE" == "1" ]]; then
    env_args+=("HEADLESS=1")
  fi

  printf '[phase1] building PX4 SITL artifacts with px4_sitl_default\n' >>"$PX4_LOG_FILE"
  # Gazebo GZ targets do not honor DONT_RUN=1 like gazebo-classic does, so the
  # build phase must avoid `make px4_sitl gz_x500` or the control-plane start
  # request hangs waiting on a simulator it later starts explicitly.
  if ! bash -lc "cd \"$PX4_DIR\" && export PATH=\"$python_dir:\$PATH\" && exec env ${env_args[*]} make $PX4_SITL_MAKE_ARGS px4_sitl_default" >>"$PX4_LOG_FILE" 2>&1; then
    die "PX4 SITL build failed; inspect logs in $LOG_DIR"
  fi

  [[ -x "$PX4_BIN" ]] || die "missing PX4 SITL binary after build: $PX4_BIN"

  if [[ "$HEADLESS_MODE" == "0" && ! -f "$GZ_GSTREAMER_PLUGIN" ]]; then
    cat >&2 <<EOF
phase-1 start warning: Gazebo camera plugin was not built.
Install GStreamer development packages and rebuild:
  sudo apt-get install -y libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev
This does not block the base simulator from running, but camera-backed features may fail.
EOF
  fi
}

start_px4() {
  require_cmd gz
  require_cmd python3
  if [[ "$HEADLESS_MODE" == "1" ]]; then
    setsid bash -lc "cd \"$PX4_BIN_DIR\" && exec env GZ_DISTRO=\"$GZ_DISTRO\" GZ_PARTITION=\"$GZ_PARTITION\" GZ_IP=127.0.0.1 PX4_SIM_MODEL=gz_x500 HEADLESS=1 \"$PX4_BIN\"" >>"$PX4_LOG_FILE" 2>&1 &
  else
    setsid bash -lc "cd \"$PX4_BIN_DIR\" && exec env GZ_DISTRO=\"$GZ_DISTRO\" GZ_PARTITION=\"$GZ_PARTITION\" GZ_IP=127.0.0.1 PX4_SIM_MODEL=gz_x500 \"$PX4_BIN\"" >>"$PX4_LOG_FILE" 2>&1 &
  fi
  echo $! >"$PX4_PID_FILE"
}

main() {
  cd "$ROOT_DIR"
  check_git_state
  resolve_python_defaults
  normalize_python_bin
  resolve_xrce_agent_defaults

  if [[ "${1:-}" == "--check" ]]; then
    print_plan
    echo "Check mode only; no processes were started."
    exit 0
  fi

  require_cmd git
  require_cmd make
  require_cmd cmake
  require_cmd ninja
  require_cmd pkg-config
  require_cmd gz
  require_binary "$PYTHON_BIN"
  require_python_module kconfiglib
  require_python_module yaml
  require_python_module jinja2
  require_python_module jsonschema
  require_python_snippet "incompatible empy/em module for PX4; expected empy<4 with em.RAW_OPT available" $'import em\nassert hasattr(em, "RAW_OPT")'
  require_opencv_dev
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

  build_px4
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
