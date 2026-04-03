#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
IMAGE="${PHASE6_CONTAINER_IMAGE:-drone-sim-phase3-humble-harmonic:latest}"
CONTAINER_WORKDIR="/workspace"
HOST_UID="$(id -u)"
HOST_GID="$(id -g)"
CONTAINER_SITE_PACKAGES_DIR="$CONTAINER_WORKDIR/.cache/phase-6/site-packages"
CONTAINER_AGENT_SRC_DIR="$CONTAINER_WORKDIR/.cache/phase-1/micro-xrce-agent/src"
CONTAINER_AGENT_BUILD_DIR="$CONTAINER_WORKDIR/.cache/phase-1/micro-xrce-agent/build"
CONTAINER_AGENT_INSTALL_DIR="$CONTAINER_WORKDIR/.cache/phase-1/micro-xrce-agent/install"
CONTAINER_RUNTIME_DIR="$CONTAINER_WORKDIR/.sim-runtime/phase-6-container"
CONTAINER_LOG_DIR="$CONTAINER_WORKDIR/.sim-logs/phase-6-container"
CONTAINER_ROS_WS_DIR="/tmp/phase6-ros2-ws"
AGENT_TAG="${MICRO_XRCE_AGENT_TAG:-v2.4.3}"
AGENT_BUILD_JOBS="${MICRO_XRCE_AGENT_BUILD_JOBS:-2}"
AGENT_CMAKE_FLAGS="${MICRO_XRCE_AGENT_CMAKE_FLAGS:--DUAGENT_CED_PROFILE=OFF -DUAGENT_DISCOVERY_PROFILE=OFF -DUAGENT_P2P_PROFILE=OFF -DUAGENT_SOCKETCAN_PROFILE=OFF}"
PX4_BUILD_JOBS="${PHASE6_PX4_BUILD_JOBS:-1}"
FORCE_CLEAN_PX4_BUILD="${PHASE6_FORCE_CLEAN_PX4_BUILD:-0}"
AUTO_BUILD_IMAGE="${PHASE6_CONTAINER_AUTO_BUILD:-1}"
MISSION_TIMEOUT_S="${PHASE6_MISSION_TIMEOUT_S:-240}"

die() {
  printf 'phase-6 container validation failed: %s\n' "$1" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

main() {
  require_cmd docker

  if [[ "${1:-}" == "--check" ]]; then
    cat <<EOF
Container validation plan:
1. Reuse the Humble + Harmonic image from phase 3
2. Install phase 2 and phase 6 Python dependencies inside a cached site-packages directory
3. Build and test drone_perception with the ROS 2 workspace in container
4. Reuse the cached Micro XRCE-DDS Agent $AGENT_TAG
5. Run case 1 in an isolated runtime: prove the mission waits for visual lock before PATROL
6. Run case 2 in another isolated runtime: prove perception_timeout -> mission abort -> safe landing
EOF
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
    -e "MISSION_TIMEOUT_S=$MISSION_TIMEOUT_S" \
    -v "$ROOT_DIR:$CONTAINER_WORKDIR" \
    -w "$CONTAINER_WORKDIR" \
    "$IMAGE" \
    bash -s <<'EOS'
set -euo pipefail

mkdir -p "$CONTAINER_RUNTIME_DIR" "$CONTAINER_LOG_DIR" "$CONTAINER_SITE_PACKAGES_DIR" /tmp/codex-home-user
export HOME=/tmp/codex-home-user

ACTIVE_CASE=""
ACTIVE_LOG_DIR=""
ACTIVE_RUNTIME_DIR=""
camera_publisher_pid=""
bringup_pid=""
vehicle_observer_pid=""

cleanup_case() {
  if [[ -n "$camera_publisher_pid" ]]; then
    kill "$camera_publisher_pid" >/dev/null 2>&1 || true
    wait "$camera_publisher_pid" >/dev/null 2>&1 || true
    camera_publisher_pid=""
  fi
  if [[ -n "$vehicle_observer_pid" ]]; then
    kill "$vehicle_observer_pid" >/dev/null 2>&1 || true
    wait "$vehicle_observer_pid" >/dev/null 2>&1 || true
    vehicle_observer_pid=""
  fi
  if [[ -n "$bringup_pid" ]]; then
    kill "$bringup_pid" >/dev/null 2>&1 || true
    wait "$bringup_pid" >/dev/null 2>&1 || true
    bringup_pid=""
  fi
  pkill -f 'publish_sim_camera_stream.py' >/dev/null 2>&1 || true
  pkill -f 'ros2 launch drone_bringup bringup.launch.py' >/dev/null 2>&1 || true
  pkill -f '/px4_bridge_node' >/dev/null 2>&1 || true
  pkill -f '/mission_manager_node' >/dev/null 2>&1 || true
  pkill -f '/camera_input_node' >/dev/null 2>&1 || true
  pkill -f '/object_detector_node' >/dev/null 2>&1 || true
  pkill -f '/tracker_node' >/dev/null 2>&1 || true
  pkill -f '/safety_manager_node' >/dev/null 2>&1 || true
  if [[ -n "$ACTIVE_RUNTIME_DIR" && -n "$ACTIVE_LOG_DIR" ]]; then
    PHASE1_RUNTIME_DIR="$ACTIVE_RUNTIME_DIR" PHASE1_LOG_DIR="$ACTIVE_LOG_DIR" bash scripts/sim/stop.sh >/dev/null 2>&1 || true
  fi
}

cleanup_all() {
  cleanup_case
}

dump_case_logs() {
  if [[ -z "$ACTIVE_LOG_DIR" ]]; then
    return
  fi
  find "$ACTIVE_LOG_DIR" -type f | sort | while read -r file; do
    echo "--- ${ACTIVE_CASE}: $(basename "$file") ---"
    cat "$file"
  done
}

set_case_dirs() {
  ACTIVE_CASE="$1"
  ACTIVE_RUNTIME_DIR="$CONTAINER_RUNTIME_DIR/$ACTIVE_CASE"
  ACTIVE_LOG_DIR="$CONTAINER_LOG_DIR/$ACTIVE_CASE"
  rm -rf "$ACTIVE_RUNTIME_DIR" "$ACTIVE_LOG_DIR"
  mkdir -p "$ACTIVE_RUNTIME_DIR" "$ACTIVE_LOG_DIR"
}

prepare_mission_params() {
  local target_file="$1"
  local require_track_lock="$2"
  cat > "$target_file" <<PARAMS
/**:
  ros__parameters:
    backend: ros2_domain
    scenario_file: simulation/scenarios/patrol_basic.json
    state_topic: /drone/vehicle_state
    command_topic: /drone/vehicle_command
    command_status_topic: /drone/vehicle_command_status
    perception_event_topic: /drone/perception/event
    tracked_object_topic: /drone/perception/tracked_object
    mission_command_topic: /drone/mission_command
    mission_status_topic: /drone/mission_status
    publish_rate_hz: 5.0
    auto_start: false
    require_track_lock_before_patrol: $require_track_lock
    track_lock_timeout_s: 45.0
    takeoff_altitude_tolerance_m: 0.4
    command_retry_interval_s: 3.0
    max_command_retries: 5
PARAMS
}

prepare_safety_params() {
  local target_file="$1"
  local require_heartbeat="$2"
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
    geofence_max_distance_m: 50.0
    geofence_max_altitude_m: 8.0
    gps_loss_timeout_s: 1.5
    require_perception_heartbeat: $require_heartbeat
    perception_timeout_s: 1.5
    perception_max_latency_s: 0.5
    geofence_action: return_to_home
    gps_loss_action: land
    rc_loss_action: return_to_home
    data_link_loss_action: return_to_home
    perception_timeout_action: land
    perception_latency_action: land
PARAMS
}

start_stack() {
  if ! MICRO_XRCE_AGENT_BIN="$AGENT_BIN" MICRO_XRCE_AGENT_LD_LIBRARY_PATH="$AGENT_LD_LIBRARY_PATH" PX4_SITL_MAKE_ARGS="-j$PX4_BUILD_JOBS" PHASE1_GZ_DISTRO=harmonic PHASE1_GZ_PARTITION="phase6-${ACTIVE_CASE}" PHASE1_RUNTIME_DIR="$ACTIVE_RUNTIME_DIR" PHASE1_LOG_DIR="$ACTIVE_LOG_DIR" bash scripts/sim/start.sh; then
    dump_case_logs
    return 1
  fi

  local deadline=$((SECONDS + 1200))
  while true; do
    if [[ -f "$ACTIVE_LOG_DIR/px4_sitl.log" ]] && grep -Fq 'INFO  [px4] Startup script returned successfully' "$ACTIVE_LOG_DIR/px4_sitl.log"; then
      break
    fi
    if (( SECONDS >= deadline )); then
      dump_case_logs
      return 1
    fi
    sleep 2
  done

  python3 scripts/sim/configure_px4_sim_params.py --timeout-s 30 --set-int NAV_DLL_ACT=0 --set-float COM_DISARM_PRFLT=60 > "$ACTIVE_LOG_DIR/px4_sim_params.json"
}

start_bringup() {
  local mission_params_file="$1"
  local safety_params_file="$2"

  stdbuf -oL -eL ros2 launch drone_bringup bringup.launch.py \
    enable_mission:=true \
    mission_auto_start:=false \
    mission_params_file:="$mission_params_file" \
    enable_perception:=true \
    perception_params_file:="$CONTAINER_WORKDIR/robotics/ros2_ws/src/drone_bringup/config/drone_perception.yaml" \
    enable_safety:=true \
    safety_params_file:="$safety_params_file" \
    > "$ACTIVE_LOG_DIR/bringup.log" 2>&1 &
  bringup_pid="$!"
  sleep 8
}

start_camera_publisher() {
  stdbuf -oL -eL python3 robotics/ros2_ws/scripts/publish_sim_camera_stream.py \
    --topic /simulation/camera/image_raw \
    > "$ACTIVE_LOG_DIR/camera.log" 2>&1 &
  camera_publisher_pid="$!"
  sleep 3
}

stop_camera_publisher() {
  if [[ -n "$camera_publisher_pid" ]]; then
    kill "$camera_publisher_pid" >/dev/null 2>&1 || true
    wait "$camera_publisher_pid" >/dev/null 2>&1 || true
    camera_publisher_pid=""
  fi
}

wait_for_core_topics() {
  ros2 topic list > "$ACTIVE_LOG_DIR/topics_core.txt"
  for topic in \
    /drone/mission_command \
    /drone/mission_status \
    /drone/perception/event \
    /drone/perception_heartbeat \
    /drone/safety_status \
    /drone/vehicle_state; do
    grep -q "^${topic}$" "$ACTIVE_LOG_DIR/topics_core.txt" || { dump_case_logs; exit 1; }
  done
}

wait_for_perception_topics() {
  local deadline=$((SECONDS + 30))
  while true; do
    ros2 topic list > "$ACTIVE_LOG_DIR/topics_perception.txt"
    missing_topic=""
    for topic in \
      /drone/perception/preprocessed_image \
      /drone/perception/detection \
      /drone/perception/tracked_object; do
      if ! grep -q "^${topic}$" "$ACTIVE_LOG_DIR/topics_perception.txt"; then
        missing_topic="$topic"
        break
      fi
    done
    if [[ -z "$missing_topic" ]]; then
      return
    fi
    if (( SECONDS >= deadline )); then
      dump_case_logs
      exit 1
    fi
    sleep 1
  done
}

case_visual_lock_gate() {
  set_case_dirs "visual_lock_gate"
  start_stack || exit 1

  local mission_params="$ACTIVE_RUNTIME_DIR/mission.yaml"
  local safety_params="$ACTIVE_RUNTIME_DIR/safety.yaml"
  prepare_mission_params "$mission_params" "true"
  prepare_safety_params "$safety_params" "false"
  start_bringup "$mission_params" "$safety_params"
  wait_for_core_topics

  python3 robotics/ros2_ws/scripts/wait_for_vehicle_state.py \
    --timeout-s 90 \
    --connected true \
    --position-valid true \
    --failsafe false \
    > "$ACTIVE_LOG_DIR/vehicle_ready.json"

  local mission_barrier_ns
  mission_barrier_ns="$(python3 -c 'import time; print(time.time_ns())')"

  ros2 topic pub --once /drone/mission_command drone_msgs/msg/MissionCommand \
    "{stamp: {sec: 0, nanosec: 0}, command: start}" \
    > "$ACTIVE_LOG_DIR/mission_command.log"

  python3 robotics/ros2_ws/scripts/wait_for_command_status.py \
    --timeout-s 90 \
    --min-stamp-ns "$mission_barrier_ns" \
    --command arm \
    --accepted true \
    > "$ACTIVE_LOG_DIR/arm_ack.json"

  python3 robotics/ros2_ws/scripts/wait_for_vehicle_state.py \
    --timeout-s 90 \
    --min-stamp-ns "$mission_barrier_ns" \
    --connected true \
    --armed true \
    --failsafe false \
    > "$ACTIVE_LOG_DIR/armed_state.json"

  python3 robotics/ros2_ws/scripts/wait_for_mission_status.py \
    --timeout-s 120 \
    --min-stamp-ns "$mission_barrier_ns" \
    --phase hover \
    --active true \
    --detail-contains "waiting for visual lock before patrol" \
    > "$ACTIVE_LOG_DIR/waiting_visual_lock.json"

  local perception_barrier_ns
  perception_barrier_ns="$(python3 -c 'import time; print(time.time_ns())')"
  start_camera_publisher
  wait_for_perception_topics

  python3 robotics/ros2_ws/scripts/wait_for_perception_heartbeat.py \
    --timeout-s 60 \
    --min-stamp-ns "$perception_barrier_ns" \
    --healthy true \
    --max-pipeline-latency-s 0.5 \
    > "$ACTIVE_LOG_DIR/perception_heartbeat.json"

  python3 robotics/ros2_ws/scripts/wait_for_vision_detection.py \
    --timeout-s 60 \
    --min-stamp-ns "$perception_barrier_ns" \
    --detected true \
    --label sim_target \
    --min-confidence 0.5 \
    > "$ACTIVE_LOG_DIR/perception_detection.json"

  python3 robotics/ros2_ws/scripts/wait_for_tracked_object.py \
    --timeout-s 60 \
    --min-stamp-ns "$perception_barrier_ns" \
    --tracked true \
    --label sim_target \
    --min-age 1 \
    > "$ACTIVE_LOG_DIR/perception_tracked_object.json"

  python3 robotics/ros2_ws/scripts/wait_for_mission_status.py \
    --timeout-s 120 \
    --min-stamp-ns "$perception_barrier_ns" \
    --phase patrol \
    --active true \
    > "$ACTIVE_LOG_DIR/patrol_after_lock.json"

  cleanup_case
}

case_perception_timeout() {
  set_case_dirs "perception_timeout"
  start_stack || exit 1

  local mission_params="$ACTIVE_RUNTIME_DIR/mission.yaml"
  local safety_params="$ACTIVE_RUNTIME_DIR/safety.yaml"
  prepare_mission_params "$mission_params" "true"
  prepare_safety_params "$safety_params" "true"
  start_bringup "$mission_params" "$safety_params"
  wait_for_core_topics

  python3 robotics/ros2_ws/scripts/wait_for_vehicle_state.py \
    --timeout-s 90 \
    --connected true \
    --position-valid true \
    --failsafe false \
    > "$ACTIVE_LOG_DIR/vehicle_ready.json"

  local perception_barrier_ns
  perception_barrier_ns="$(python3 -c 'import time; print(time.time_ns())')"
  start_camera_publisher
  wait_for_perception_topics

  python3 robotics/ros2_ws/scripts/wait_for_perception_heartbeat.py \
    --timeout-s 60 \
    --min-stamp-ns "$perception_barrier_ns" \
    --healthy true \
    --max-pipeline-latency-s 0.5 \
    > "$ACTIVE_LOG_DIR/perception_heartbeat.json"

  python3 robotics/ros2_ws/scripts/wait_for_vision_detection.py \
    --timeout-s 60 \
    --min-stamp-ns "$perception_barrier_ns" \
    --detected true \
    --label sim_target \
    --min-confidence 0.5 \
    > "$ACTIVE_LOG_DIR/perception_detection.json"

  python3 robotics/ros2_ws/scripts/wait_for_tracked_object.py \
    --timeout-s 60 \
    --min-stamp-ns "$perception_barrier_ns" \
    --tracked true \
    --label sim_target \
    --min-age 1 \
    > "$ACTIVE_LOG_DIR/perception_tracked_object.json"

  local mission_barrier_ns
  mission_barrier_ns="$(python3 -c 'import time; print(time.time_ns())')"

  ros2 topic pub --once /drone/mission_command drone_msgs/msg/MissionCommand \
    "{stamp: {sec: 0, nanosec: 0}, command: start}" \
    > "$ACTIVE_LOG_DIR/mission_command.log"

  python3 robotics/ros2_ws/scripts/wait_for_command_status.py \
    --timeout-s 90 \
    --min-stamp-ns "$mission_barrier_ns" \
    --command arm \
    --accepted true \
    > "$ACTIVE_LOG_DIR/arm_ack.json"

  python3 robotics/ros2_ws/scripts/wait_for_vehicle_state.py \
    --timeout-s 90 \
    --min-stamp-ns "$mission_barrier_ns" \
    --connected true \
    --armed true \
    --failsafe false \
    > "$ACTIVE_LOG_DIR/armed_state.json"

  python3 robotics/ros2_ws/scripts/wait_for_vehicle_state.py \
    --timeout-s "$MISSION_TIMEOUT_S" \
    --min-stamp-ns "$mission_barrier_ns" \
    --min-altitude-m 2.0 \
    --require-airborne \
    --require-landed-after-airborne \
    > "$ACTIVE_LOG_DIR/vehicle_observation.json" &
  vehicle_observer_pid="$!"

  python3 robotics/ros2_ws/scripts/wait_for_mission_status.py \
    --timeout-s 120 \
    --min-stamp-ns "$mission_barrier_ns" \
    --phase patrol \
    --active true \
    > "$ACTIVE_LOG_DIR/patrol_before_failure.json"

  local failure_barrier_ns
  failure_barrier_ns="$(python3 -c 'import time; print(time.time_ns())')"
  stop_camera_publisher

  python3 robotics/ros2_ws/scripts/wait_for_safety_status.py \
    --timeout-s 120 \
    --min-stamp-ns "$failure_barrier_ns" \
    --active true \
    --rule perception_timeout \
    --action land \
    --source perception_watchdog \
    --mission-abort-requested true \
    --vehicle-command-sent true \
    --min-trigger-count 1 \
    > "$ACTIVE_LOG_DIR/safety_status.json"

  python3 robotics/ros2_ws/scripts/wait_for_mission_status.py \
    --timeout-s 120 \
    --min-stamp-ns "$failure_barrier_ns" \
    --aborted true \
    --terminal true \
    > "$ACTIVE_LOG_DIR/mission_aborted.json"

  wait "$vehicle_observer_pid"
  vehicle_observer_pid=""

  cleanup_case
}

trap cleanup_all EXIT
cd "$CONTAINER_WORKDIR"

python3 -m pip install --quiet --upgrade --target "$CONTAINER_SITE_PACKAGES_DIR" \
  -r packages/shared-py/requirements-phase2.txt \
  -r packages/shared-py/requirements-phase6.txt
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
colcon test --executor sequential --parallel-workers 1 --packages-select drone_msgs drone_px4 drone_mission drone_perception drone_safety drone_bringup
colcon test-result --verbose
set +u
source install/setup.bash
set -u
cd "$CONTAINER_WORKDIR"

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

case_visual_lock_gate
case_perception_timeout
EOS
}

main "$@"
