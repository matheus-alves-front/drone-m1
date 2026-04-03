#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
IMAGE="${PHASE5_CONTAINER_IMAGE:-drone-sim-phase3-humble-harmonic:latest}"
CONTAINER_WORKDIR="/workspace"
HOST_UID="$(id -u)"
HOST_GID="$(id -g)"
CONTAINER_SITE_PACKAGES_DIR="$CONTAINER_WORKDIR/.cache/phase-5/site-packages"
CONTAINER_AGENT_SRC_DIR="$CONTAINER_WORKDIR/.cache/phase-1/micro-xrce-agent/src"
CONTAINER_AGENT_BUILD_DIR="$CONTAINER_WORKDIR/.cache/phase-1/micro-xrce-agent/build"
CONTAINER_AGENT_INSTALL_DIR="$CONTAINER_WORKDIR/.cache/phase-1/micro-xrce-agent/install"
CONTAINER_RUNTIME_DIR="$CONTAINER_WORKDIR/.sim-runtime/phase-5-container"
CONTAINER_LOG_DIR="$CONTAINER_WORKDIR/.sim-logs/phase-5-container"
CONTAINER_ROS_WS_DIR="/tmp/phase5-ros2-ws"
AGENT_TAG="${MICRO_XRCE_AGENT_TAG:-v2.4.3}"
AGENT_BUILD_JOBS="${MICRO_XRCE_AGENT_BUILD_JOBS:-2}"
AGENT_CMAKE_FLAGS="${MICRO_XRCE_AGENT_CMAKE_FLAGS:--DUAGENT_CED_PROFILE=OFF -DUAGENT_DISCOVERY_PROFILE=OFF -DUAGENT_P2P_PROFILE=OFF -DUAGENT_SOCKETCAN_PROFILE=OFF}"
PX4_BUILD_JOBS="${PHASE5_PX4_BUILD_JOBS:-1}"
FORCE_CLEAN_PX4_BUILD="${PHASE5_FORCE_CLEAN_PX4_BUILD:-0}"
AUTO_BUILD_IMAGE="${PHASE5_CONTAINER_AUTO_BUILD:-1}"
SCENARIO_TIMEOUT_S="${PHASE5_SCENARIO_TIMEOUT_S:-180}"

die() {
  printf 'phase-5 container validation failed: %s\n' "$1" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

main() {
  require_cmd docker

  if [[ "${1:-}" == "--check" ]]; then
    echo "Container validation plan:"
    echo "1. Reuse the Humble + Harmonic image from phase 3"
    echo "2. Build and test drone_safety together with the existing ROS 2 workspace"
    echo "3. Reuse the cached Micro XRCE-DDS Agent $AGENT_TAG"
    echo "4. Start the real Phase 1 stack with PX4 SITL + Gazebo Harmonic"
    echo "5. Launch bringup with mission and safety enabled"
    echo "6. Prove three safety failures in the official stack: geofence_breach, failsafe_gps_loss and failsafe_rc_loss"
    echo "7. Validate deterministic safety_status, mission abort and final landing for each case"
    exit 0
  fi

  if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
    bash "$ROOT_DIR/robotics/ros2_ws/scripts/build-phase-3-container-image.sh"
  elif [[ "$AUTO_BUILD_IMAGE" == "1" ]]; then
    bash "$ROOT_DIR/robotics/ros2_ws/scripts/build-phase-3-container-image.sh"
  fi

  docker run --rm \
    -i \
    --user "$HOST_UID:$HOST_GID" \
    -e "HOME=/tmp/codex-home-user" \
    -e "HOST_UID=$HOST_UID" \
    -e "HOST_GID=$HOST_GID" \
    -e "CONTAINER_WORKDIR=$CONTAINER_WORKDIR" \
    -e "CONTAINER_SITE_PACKAGES_DIR=$CONTAINER_SITE_PACKAGES_DIR" \
    -e "CONTAINER_AGENT_SRC_DIR=$CONTAINER_AGENT_SRC_DIR" \
    -e "CONTAINER_AGENT_BUILD_DIR=$CONTAINER_AGENT_BUILD_DIR" \
    -e "CONTAINER_AGENT_INSTALL_DIR=$CONTAINER_AGENT_INSTALL_DIR" \
    -e "CONTAINER_RUNTIME_DIR=$CONTAINER_RUNTIME_DIR" \
    -e "CONTAINER_LOG_DIR=$CONTAINER_LOG_DIR" \
    -e "CONTAINER_ROS_WS_DIR=$CONTAINER_ROS_WS_DIR" \
    -e "AGENT_TAG=$AGENT_TAG" \
    -e "AGENT_BUILD_JOBS=$AGENT_BUILD_JOBS" \
    -e "AGENT_CMAKE_FLAGS=$AGENT_CMAKE_FLAGS" \
    -e "PX4_BUILD_JOBS=$PX4_BUILD_JOBS" \
    -e "FORCE_CLEAN_PX4_BUILD=$FORCE_CLEAN_PX4_BUILD" \
    -e "SCENARIO_TIMEOUT_S=$SCENARIO_TIMEOUT_S" \
    -v "$ROOT_DIR:$CONTAINER_WORKDIR" \
    -w "$CONTAINER_WORKDIR" \
    "$IMAGE" \
    bash -s <<'EOS'
set -euo pipefail

mkdir -p "$CONTAINER_RUNTIME_DIR" "$CONTAINER_LOG_DIR" "$CONTAINER_SITE_PACKAGES_DIR" /tmp/codex-home-user
export HOME=/tmp/codex-home-user

cleanup() {
  if [[ -n "${bringup_pid:-}" ]]; then
    kill "$bringup_pid" >/dev/null 2>&1 || true
    wait "$bringup_pid" >/dev/null 2>&1 || true
  fi
  pkill -f 'ros2 launch drone_bringup bringup.launch.py' >/dev/null 2>&1 || true
  pkill -f '/px4_bridge_node' >/dev/null 2>&1 || true
  pkill -f '/mission_manager_node' >/dev/null 2>&1 || true
  pkill -f '/safety_manager_node' >/dev/null 2>&1 || true
  PHASE1_RUNTIME_DIR=$CONTAINER_RUNTIME_DIR PHASE1_LOG_DIR=$CONTAINER_LOG_DIR bash scripts/sim/stop.sh >/dev/null 2>&1 || true
}

dump_logs() {
  find "$CONTAINER_LOG_DIR" -type f | sort | while read -r file; do
    echo "--- $(basename "$file") ---"
    cat "$file"
  done
}

start_stack() {
  local case_log_dir="$1"

  if ! MICRO_XRCE_AGENT_BIN="$AGENT_BIN" MICRO_XRCE_AGENT_LD_LIBRARY_PATH="$AGENT_LD_LIBRARY_PATH" PX4_SITL_MAKE_ARGS="-j$PX4_BUILD_JOBS" PHASE1_GZ_DISTRO=harmonic PHASE1_GZ_PARTITION="phase5-container-runtime" PHASE1_RUNTIME_DIR=$CONTAINER_RUNTIME_DIR PHASE1_LOG_DIR=$case_log_dir bash scripts/sim/start.sh; then
    dump_logs
    return 1
  fi

  local deadline=$((SECONDS + 1200))
  while true; do
    if [[ -f "$case_log_dir/px4_sitl.log" ]] && grep -Fq 'INFO  [px4] Startup script returned successfully' "$case_log_dir/px4_sitl.log"; then
      break
    fi
    if (( SECONDS >= deadline )); then
      dump_logs
      return 1
    fi
    sleep 2
  done

  python3 scripts/sim/configure_px4_sim_params.py --timeout-s 30 --set-int NAV_DLL_ACT=0 --set-float COM_DISARM_PRFLT=60 > "$case_log_dir/px4_sim_params.json"
}

stop_stack() {
  PHASE1_RUNTIME_DIR=$CONTAINER_RUNTIME_DIR PHASE1_LOG_DIR=$CONTAINER_LOG_DIR bash scripts/sim/stop.sh >/dev/null 2>&1 || true
  sleep 2
}

start_bringup() {
  local case_name="$1"
  local safety_params_file="$2"
  local case_log_dir="$3"
  stdbuf -oL -eL ros2 launch drone_bringup bringup.launch.py \
    enable_mission:=true \
    mission_auto_start:=false \
    enable_safety:=true \
    safety_params_file:="$safety_params_file" \
    > "$case_log_dir/${case_name}_bringup.log" 2>&1 &
  bringup_pid="$!"
  sleep 5
}

stop_bringup() {
  if [[ -n "${bringup_pid:-}" ]]; then
    kill "$bringup_pid" >/dev/null 2>&1 || true
    wait "$bringup_pid" >/dev/null 2>&1 || true
    unset bringup_pid
  fi
  pkill -f 'ros2 launch drone_bringup bringup.launch.py' >/dev/null 2>&1 || true
  pkill -f '/px4_bridge_node' >/dev/null 2>&1 || true
  pkill -f '/mission_manager_node' >/dev/null 2>&1 || true
  pkill -f '/safety_manager_node' >/dev/null 2>&1 || true
  sleep 2
}

prepare_safety_params() {
  local target_file="$1"
  local geofence_distance="$2"
  cat > "$target_file" <<PARAMS
/**:
  ros__parameters:
    state_topic: /drone/vehicle_state
    mission_status_topic: /drone/mission_status
    mission_command_topic: /drone/mission_command
    vehicle_command_topic: /drone/vehicle_command
    safety_fault_topic: /drone/safety_fault
    safety_status_topic: /drone/safety_status
    perception_heartbeat_topic: /drone/perception_heartbeat
    publish_rate_hz: 5.0
    geofence_enabled: true
    geofence_max_distance_m: ${geofence_distance}
    geofence_max_altitude_m: 8.0
    gps_loss_timeout_s: 1.5
    require_perception_heartbeat: false
    perception_timeout_s: 2.0
    perception_max_latency_s: 0.5
    geofence_action: return_to_home
    gps_loss_action: land
    rc_loss_action: return_to_home
    data_link_loss_action: return_to_home
    perception_timeout_action: land
    perception_latency_action: land
PARAMS
}

run_case() (
  set -euo pipefail
  local case_name="$1"
  local fault_type="$2"
  local expected_action="$3"
  local geofence_distance="$4"
  local case_log_dir="$CONTAINER_LOG_DIR/$case_name"
  local expected_source="vehicle_state"

  rm -rf "$case_log_dir"
  mkdir -p "$case_log_dir"
  rm -f "$CONTAINER_RUNTIME_DIR/${case_name}"_*
  find "$CONTAINER_RUNTIME_DIR" -maxdepth 1 -type f -delete

  start_stack "$case_log_dir"

  local safety_params_file="$CONTAINER_RUNTIME_DIR/${case_name}_safety.yaml"
  prepare_safety_params "$safety_params_file" "$geofence_distance"
  start_bringup "$case_name" "$safety_params_file" "$case_log_dir"

  ros2 topic list > "$case_log_dir/${case_name}_topics.txt"
  for topic in /drone/vehicle_state /drone/mission_status /drone/safety_status /drone/safety_fault; do
    grep -q "^${topic}$" "$case_log_dir/${case_name}_topics.txt" || return 1
  done

  python3 robotics/ros2_ws/scripts/wait_for_vehicle_state.py \
    --timeout-s 90 \
    --connected true \
    --armed false \
    --landed true \
    --position-valid true \
    --failsafe false \
    > "$case_log_dir/${case_name}_preflight_vehicle_state.json"

  local start_barrier_ns
  start_barrier_ns="$(python3 -c 'import time; print(time.time_ns())')"

  ros2 topic pub --once /drone/mission_command drone_msgs/msg/MissionCommand \
    "{stamp: {sec: 0, nanosec: 0}, command: start}" \
    > "$case_log_dir/${case_name}_mission_command_pub.log"

  python3 robotics/ros2_ws/scripts/wait_for_vehicle_state.py \
    --timeout-s "$SCENARIO_TIMEOUT_S" \
    --min-stamp-ns "$start_barrier_ns" \
    --min-altitude-m 2.0 \
    --require-airborne \
    --require-landed-after-airborne \
    > "$case_log_dir/${case_name}_vehicle_observation.json" &
  observer_pid="$!"

  python3 robotics/ros2_ws/scripts/wait_for_command_status.py \
    --timeout-s 60 \
    --min-stamp-ns "$start_barrier_ns" \
    --command arm \
    --accepted true \
    > "$case_log_dir/${case_name}_arm_ack.json"

  python3 robotics/ros2_ws/scripts/wait_for_vehicle_state.py \
    --timeout-s 60 \
    --min-stamp-ns "$start_barrier_ns" \
    --connected true \
    --armed true \
    --failsafe false \
    > "$case_log_dir/${case_name}_armed_state.json"

  case "$fault_type" in
    rc_loss|data_link_loss)
      expected_source="fault_injection"
      ;;
    perception_timeout|perception_latency)
      expected_source="perception_watchdog"
      ;;
  esac

  python3 robotics/ros2_ws/scripts/wait_for_safety_status.py \
    --timeout-s "$SCENARIO_TIMEOUT_S" \
    --min-stamp-ns "$start_barrier_ns" \
    --active true \
    --mission-abort-requested true \
    --vehicle-command-sent true \
    --rule "$fault_type" \
    --action "$expected_action" \
    --source "$expected_source" \
    --min-trigger-count 1 \
    > "$case_log_dir/${case_name}_safety_status.json" &
  safety_waiter_pid="$!"

  if [[ "$fault_type" != "geofence_breach" ]]; then
    python3 robotics/ros2_ws/scripts/wait_for_mission_status.py \
      --timeout-s 90 \
      --min-stamp-ns "$start_barrier_ns" \
      --phase patrol \
      --active true \
      --min-waypoint-index 1 \
      > "$case_log_dir/${case_name}_mission_patrol.json"

    ros2 topic pub --once /drone/safety_fault drone_msgs/msg/SafetyFault \
      "{stamp: {sec: 0, nanosec: 0}, fault_type: ${fault_type}, active: true, value: 1.0, detail: '${case_name} injected'}" \
      > "$case_log_dir/${case_name}_fault_pub.log"
  fi

  wait "$safety_waiter_pid"

  python3 robotics/ros2_ws/scripts/wait_for_mission_status.py \
    --timeout-s "$SCENARIO_TIMEOUT_S" \
    --min-stamp-ns "$start_barrier_ns" \
    --aborted true \
    --terminal true \
    > "$case_log_dir/${case_name}_mission_aborted.json"

  wait "$observer_pid"
  unset observer_pid

  if [[ "$fault_type" != "geofence_breach" ]]; then
    ros2 topic pub --once /drone/safety_fault drone_msgs/msg/SafetyFault \
      "{stamp: {sec: 0, nanosec: 0}, fault_type: ${fault_type}, active: false, value: 0.0, detail: ''}" \
      > "$case_log_dir/${case_name}_fault_clear.log" || true
  fi

  stop_bringup
  stop_stack
)

trap cleanup EXIT
cd "$CONTAINER_WORKDIR"

python3 -m pip install --quiet --upgrade --target "$CONTAINER_SITE_PACKAGES_DIR" -r packages/shared-py/requirements-phase2.txt
export PYTHONPATH="$CONTAINER_WORKDIR/packages/shared-py/src:$CONTAINER_SITE_PACKAGES_DIR${PYTHONPATH:+:$PYTHONPATH}"

set +u
source /opt/ros/humble/setup.bash
set -u

python3 - "$CONTAINER_WORKDIR/robotics/ros2_ws" "$CONTAINER_ROS_WS_DIR" <<'PY'
import shutil
import sys
from pathlib import Path

source = Path(sys.argv[1])
target = Path(sys.argv[2])
shutil.rmtree(target, ignore_errors=True)
shutil.copytree(
    source,
    target,
    ignore=shutil.ignore_patterns("build", "install", "log", "__pycache__"),
)
PY

export CMAKE_BUILD_PARALLEL_LEVEL=1
export MAKEFLAGS=-j1
export CFLAGS="${CFLAGS:-} -O0"
export CXXFLAGS="${CXXFLAGS:-} -O0"
cd "$CONTAINER_ROS_WS_DIR"
colcon build --executor sequential --parallel-workers 1 --packages-up-to drone_bringup
colcon test --executor sequential --parallel-workers 1 --packages-select drone_msgs drone_px4 drone_mission drone_safety drone_bringup
colcon test-result --verbose
set +u
source install/setup.bash
set -u
cd "$CONTAINER_WORKDIR"

PHASE1_RUNTIME_DIR=$CONTAINER_RUNTIME_DIR PHASE1_LOG_DIR=$CONTAINER_LOG_DIR bash scripts/sim/stop.sh >/dev/null 2>&1 || true
pkill -f 'ros2 launch drone_bringup bringup.launch.py' >/dev/null 2>&1 || true
pkill -f '/px4_bridge_node' >/dev/null 2>&1 || true
pkill -f '/mission_manager_node' >/dev/null 2>&1 || true
pkill -f '/safety_manager_node' >/dev/null 2>&1 || true
rm -rf "$CONTAINER_LOG_DIR" "$CONTAINER_RUNTIME_DIR"
mkdir -p "$CONTAINER_LOG_DIR" "$CONTAINER_RUNTIME_DIR"

if ! find "$CONTAINER_AGENT_BUILD_DIR" -type f -name MicroXRCEAgent | grep -q .; then
  rm -rf "$CONTAINER_AGENT_SRC_DIR" "$CONTAINER_AGENT_BUILD_DIR"
  git clone --branch "$AGENT_TAG" --depth 1 https://github.com/eProsima/Micro-XRCE-DDS-Agent.git "$CONTAINER_AGENT_SRC_DIR"
  cmake -S "$CONTAINER_AGENT_SRC_DIR" -B "$CONTAINER_AGENT_BUILD_DIR" -DCMAKE_BUILD_TYPE=Release $AGENT_CMAKE_FLAGS
  cmake --build "$CONTAINER_AGENT_BUILD_DIR" --target uagent -j"$AGENT_BUILD_JOBS"
fi

if [[ ! -x "$CONTAINER_AGENT_INSTALL_DIR/bin/MicroXRCEAgent" ]]; then
  rm -rf "$CONTAINER_AGENT_INSTALL_DIR"
  cmake --install "$CONTAINER_AGENT_BUILD_DIR" --prefix "$CONTAINER_AGENT_INSTALL_DIR"
fi

AGENT_BIN="$CONTAINER_AGENT_INSTALL_DIR/bin/MicroXRCEAgent"
AGENT_LD_LIBRARY_PATH="$CONTAINER_AGENT_INSTALL_DIR/lib"

bash scripts/sim/check-gz-harmonic-cli.sh

if [[ "$FORCE_CLEAN_PX4_BUILD" == "1" ]]; then
  rm -rf third_party/PX4-Autopilot/build/px4_sitl_default
fi

run_case "geofence_breach" "geofence_breach" "return_to_home" "10.0" || { dump_logs; exit 1; }
run_case "failsafe_gps_loss" "gps_loss" "land" "50.0" || { dump_logs; exit 1; }
run_case "failsafe_rc_loss" "rc_loss" "return_to_home" "50.0" || { dump_logs; exit 1; }

echo 'phase-5 container validation passed'
EOS
}

main "$@"
