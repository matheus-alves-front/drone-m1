#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
IMAGE="${PHASE3_CONTAINER_IMAGE:-drone-sim-phase3-humble-harmonic:latest}"
CONTAINER_WORKDIR="/workspace"
HOST_UID="$(id -u)"
HOST_GID="$(id -g)"
HOST_CACHE_DIR="$ROOT_DIR/.cache/phase-3"
CONTAINER_SITE_PACKAGES_DIR="$CONTAINER_WORKDIR/.cache/phase-3/site-packages"
CONTAINER_AGENT_SRC_DIR="$CONTAINER_WORKDIR/.cache/phase-1/micro-xrce-agent/src"
CONTAINER_AGENT_BUILD_DIR="$CONTAINER_WORKDIR/.cache/phase-1/micro-xrce-agent/build"
CONTAINER_AGENT_INSTALL_DIR="$CONTAINER_WORKDIR/.cache/phase-1/micro-xrce-agent/install"
CONTAINER_RUNTIME_DIR="$CONTAINER_WORKDIR/.sim-runtime/phase-3-container"
CONTAINER_LOG_DIR="$CONTAINER_WORKDIR/.sim-logs/phase-3-container"
CONTAINER_ROS_WS_DIR="/tmp/phase3-ros2-ws"
AGENT_TAG="${MICRO_XRCE_AGENT_TAG:-v2.4.3}"
AGENT_BUILD_JOBS="${MICRO_XRCE_AGENT_BUILD_JOBS:-2}"
AGENT_CMAKE_FLAGS="${MICRO_XRCE_AGENT_CMAKE_FLAGS:--DUAGENT_CED_PROFILE=OFF -DUAGENT_DISCOVERY_PROFILE=OFF -DUAGENT_P2P_PROFILE=OFF -DUAGENT_SOCKETCAN_PROFILE=OFF}"
PX4_BUILD_JOBS="${PHASE3_PX4_BUILD_JOBS:-1}"
SCENARIO_TIMEOUT_S="${PHASE3_SCENARIO_TIMEOUT_S:-180}"
AUTO_BUILD_IMAGE="${PHASE3_CONTAINER_AUTO_BUILD:-1}"

die() {
  printf 'phase-3 container validation failed: %s\n' "$1" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

main() {
  require_cmd docker

  if [[ "${1:-}" == "--check" ]]; then
    echo "Container validation plan:"
    echo "1. Build or reuse image $IMAGE with Gazebo Harmonic + ROS 2 Humble"
    echo "2. Build the ROS 2 workspace with real px4_msgs in the container"
    echo "3. Build or reuse the cached Micro XRCE-DDS Agent $AGENT_TAG"
    echo "4. Start the real Phase 1 stack with PX4 SITL + Gazebo Harmonic"
    echo "5. Launch drone_bringup against live /fmu/out and /fmu/in PX4 topics"
    echo "6. Validate bridge connection, arm/disarm command forwarding and telemetry during MAVSDK takeoff_land"
    exit 0
  fi

  mkdir -p "$HOST_CACHE_DIR"

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
    -e "SCENARIO_TIMEOUT_S=$SCENARIO_TIMEOUT_S" \
    -e "GZ_PARTITION=phase3-container-preflight" \
    -v "$ROOT_DIR:$CONTAINER_WORKDIR" \
    -w "$CONTAINER_WORKDIR" \
    "$IMAGE" \
    bash -s <<'EOS'
set -euo pipefail
python3 - "$CONTAINER_RUNTIME_DIR" "$CONTAINER_LOG_DIR" "$CONTAINER_WORKDIR/robotics/ros2_ws/build" "$CONTAINER_WORKDIR/robotics/ros2_ws/install" "$CONTAINER_WORKDIR/robotics/ros2_ws/log" "$CONTAINER_ROS_WS_DIR" <<'PY'
import shutil
import sys
from pathlib import Path

for raw_path in sys.argv[1:]:
    path = Path(raw_path)
    if path.exists() or path.is_symlink():
        shutil.rmtree(path, ignore_errors=True)
PY
mkdir -p "$CONTAINER_RUNTIME_DIR" "$CONTAINER_LOG_DIR" "$CONTAINER_SITE_PACKAGES_DIR" /tmp/codex-home-user
export HOME=/tmp/codex-home-user

bash <<'INNER_EOS'
set -euo pipefail

dump_logs() {
  if [[ -f "$CONTAINER_LOG_DIR/connected.json" ]]; then
    echo '--- connected.json ---'
    cat "$CONTAINER_LOG_DIR/connected.json"
  fi
  if [[ -f "$CONTAINER_LOG_DIR/armed.json" ]]; then
    echo '--- armed.json ---'
    cat "$CONTAINER_LOG_DIR/armed.json"
  fi
  if [[ -f "$CONTAINER_LOG_DIR/disarmed.json" ]]; then
    echo '--- disarmed.json ---'
    cat "$CONTAINER_LOG_DIR/disarmed.json"
  fi
  if [[ -f "$CONTAINER_LOG_DIR/arm_command_status.json" ]]; then
    echo '--- arm_command_status.json ---'
    cat "$CONTAINER_LOG_DIR/arm_command_status.json"
  fi
  if [[ -f "$CONTAINER_LOG_DIR/disarm_command_status.json" ]]; then
    echo '--- disarm_command_status.json ---'
    cat "$CONTAINER_LOG_DIR/disarm_command_status.json"
  fi
  if [[ -f "$CONTAINER_LOG_DIR/takeoff_land_observation.json" ]]; then
    echo '--- takeoff_land_observation.json ---'
    cat "$CONTAINER_LOG_DIR/takeoff_land_observation.json"
  fi
  if [[ -f "$CONTAINER_LOG_DIR/takeoff_land_scenario.json" ]]; then
    echo '--- takeoff_land_scenario.json ---'
    cat "$CONTAINER_LOG_DIR/takeoff_land_scenario.json"
  fi
  if [[ -f "$CONTAINER_LOG_DIR/microxrce_agent.log" ]]; then
    echo '--- microxrce_agent.log ---'
    cat "$CONTAINER_LOG_DIR/microxrce_agent.log"
  fi
  if [[ -f "$CONTAINER_LOG_DIR/px4_sitl.log" ]]; then
    echo '--- px4_sitl.log ---'
    cat "$CONTAINER_LOG_DIR/px4_sitl.log"
  fi
  if [[ -f "$CONTAINER_LOG_DIR/bringup.log" ]]; then
    echo '--- bringup.log ---'
    cat "$CONTAINER_LOG_DIR/bringup.log"
  fi
}

cleanup() {
  if [[ -n "${bringup_pid:-}" ]]; then
    kill "$bringup_pid" >/dev/null 2>&1 || true
    wait "$bringup_pid" >/dev/null 2>&1 || true
  fi
  if [[ -n "${observer_pid:-}" ]]; then
    kill "$observer_pid" >/dev/null 2>&1 || true
    wait "$observer_pid" >/dev/null 2>&1 || true
  fi
  PHASE1_RUNTIME_DIR=$CONTAINER_RUNTIME_DIR PHASE1_LOG_DIR=$CONTAINER_LOG_DIR bash scripts/sim/stop.sh >/dev/null 2>&1 || true
}

trap cleanup EXIT
cd "$CONTAINER_WORKDIR"

if ! find "$CONTAINER_AGENT_BUILD_DIR" -type f -name MicroXRCEAgent | grep -q .; then
  echo '[phase3-container] building Micro XRCE-DDS Agent cache'
  rm -rf "$CONTAINER_AGENT_SRC_DIR" "$CONTAINER_AGENT_BUILD_DIR"
  git clone --branch "$AGENT_TAG" --depth 1 https://github.com/eProsima/Micro-XRCE-DDS-Agent.git "$CONTAINER_AGENT_SRC_DIR"
  cmake -S "$CONTAINER_AGENT_SRC_DIR" -B "$CONTAINER_AGENT_BUILD_DIR" -DCMAKE_BUILD_TYPE=Release $AGENT_CMAKE_FLAGS
  cmake --build "$CONTAINER_AGENT_BUILD_DIR" --target uagent -j"$AGENT_BUILD_JOBS"
fi

if [[ ! -x "$CONTAINER_AGENT_INSTALL_DIR/bin/MicroXRCEAgent" ]]; then
  echo '[phase3-container] installing cached agent artifacts'
  rm -rf "$CONTAINER_AGENT_INSTALL_DIR"
  cmake --install "$CONTAINER_AGENT_BUILD_DIR" --prefix "$CONTAINER_AGENT_INSTALL_DIR"
fi

if [[ -x "$CONTAINER_AGENT_INSTALL_DIR/bin/MicroXRCEAgent" ]]; then
  AGENT_BIN="$CONTAINER_AGENT_INSTALL_DIR/bin/MicroXRCEAgent"
  AGENT_LD_LIBRARY_PATH="$CONTAINER_AGENT_INSTALL_DIR/lib"
else
  AGENT_BIN=$(find "$CONTAINER_AGENT_BUILD_DIR" -type f -name MicroXRCEAgent | head -n 1)
  test -n "$AGENT_BIN"
  test -x "$AGENT_BIN"
  AGENT_LD_LIBRARY_PATH=$(find "$CONTAINER_AGENT_BUILD_DIR" -type f \( -name 'libmicroxrcedds_agent.so*' -o -name 'libfastrtps.so*' -o -name 'libfastcdr.so*' -o -name 'libmicrocdr.so*' -o -name 'libfoonathan_memory*.so*' \) -printf '%h\n' | awk '!seen[$0]++' | paste -sd:)
  test -n "$AGENT_LD_LIBRARY_PATH"
fi

echo '[phase3-container] installing Python requirements for MAVSDK scenario execution'
python3 -m pip install --quiet --upgrade --target "$CONTAINER_SITE_PACKAGES_DIR" -r packages/shared-py/requirements-phase2.txt
export PYTHONPATH="$CONTAINER_WORKDIR/packages/shared-py/src:$CONTAINER_SITE_PACKAGES_DIR${PYTHONPATH:+:$PYTHONPATH}"

echo '[phase3-container] preparing ROS 2 workspace'
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
export AMENT_TRACE_SETUP_FILES="${AMENT_TRACE_SETUP_FILES:-}"
export AMENT_PYTHON_EXECUTABLE="${AMENT_PYTHON_EXECUTABLE:-/usr/bin/python3}"
export CMAKE_BUILD_PARALLEL_LEVEL=1
export MAKEFLAGS=-j1
set +u
source /opt/ros/humble/setup.bash
set -u
cd "$CONTAINER_ROS_WS_DIR"
colcon build --executor sequential --parallel-workers 1 --symlink-install --packages-up-to drone_bringup
colcon test --executor sequential --parallel-workers 1 --packages-select drone_msgs drone_px4 drone_bringup
colcon test-result --verbose
set +u
source install/setup.bash
set -u
cd "$CONTAINER_WORKDIR"

echo '[phase3-container] validating Gazebo Harmonic CLI runtime'
bash scripts/sim/check-gz-harmonic-cli.sh

echo '[phase3-container] resetting PX4 SITL build directory'
rm -rf third_party/PX4-Autopilot/build/px4_sitl_default

echo '[phase3-container] starting Phase 1 stack for live ROS 2 bridge validation'
if ! MICRO_XRCE_AGENT_BIN="$AGENT_BIN" MICRO_XRCE_AGENT_LD_LIBRARY_PATH="$AGENT_LD_LIBRARY_PATH" PHASE1_PYTHON_BIN=python3 PX4_SITL_MAKE_ARGS="-j$PX4_BUILD_JOBS" PHASE1_GZ_DISTRO=harmonic PHASE1_GZ_PARTITION="phase3-container-runtime" PHASE1_RUNTIME_DIR=$CONTAINER_RUNTIME_DIR PHASE1_LOG_DIR=$CONTAINER_LOG_DIR bash scripts/sim/start.sh; then
  dump_logs
  exit 1
fi

echo '[phase3-container] waiting for PX4 runtime readiness marker'
deadline=$((SECONDS + 1200))
while true; do
  if [[ -f "$CONTAINER_LOG_DIR/px4_sitl.log" ]] && grep -Fq 'INFO  [px4] Startup script returned successfully' "$CONTAINER_LOG_DIR/px4_sitl.log"; then
    break
  fi
  if (( SECONDS >= deadline )); then
    dump_logs
    exit 1
  fi
  sleep 2
done

echo '[phase3-container] starting ROS 2 bringup against live PX4 topics'
ros2 launch drone_bringup bringup.launch.py > "$CONTAINER_LOG_DIR/bringup.log" 2>&1 &
bringup_pid="$!"
sleep 5

ros2 topic list | tee "$CONTAINER_LOG_DIR/topic_list.txt"
grep -q '/fmu/out/vehicle_status' "$CONTAINER_LOG_DIR/topic_list.txt"
grep -q '/drone/vehicle_state' "$CONTAINER_LOG_DIR/topic_list.txt"
grep -q '/drone/vehicle_command_status' "$CONTAINER_LOG_DIR/topic_list.txt"

if ! python3 robotics/ros2_ws/scripts/wait_for_vehicle_state.py --timeout-s 30 --connected true > "$CONTAINER_LOG_DIR/connected.json"; then
  dump_logs
  exit 1
fi

echo '[phase3-container] waiting for PX4 command handling to settle'
sleep 8

echo '[phase3-container] validating real arm command forwarding via command status'
ros2 topic pub --once /drone/vehicle_command drone_msgs/msg/VehicleCommand "{command: arm, target_altitude_m: 0.0}" >/dev/null
if ! python3 robotics/ros2_ws/scripts/wait_for_command_status.py --timeout-s 30 --command arm > "$CONTAINER_LOG_DIR/arm_command_status.json"; then
  dump_logs
  exit 1
fi

echo '[phase3-container] validating telemetry bridge during MAVSDK takeoff_land'
python3 robotics/ros2_ws/scripts/wait_for_vehicle_state.py --timeout-s "$SCENARIO_TIMEOUT_S" --min-altitude-m 2.0 --require-airborne --require-landed-after-airborne > "$CONTAINER_LOG_DIR/takeoff_land_observation.json" &
observer_pid="$!"

if ! timeout "$SCENARIO_TIMEOUT_S" bash scripts/scenarios/run_takeoff_land.sh --system-address udp://:14540 --output json > "$CONTAINER_LOG_DIR/takeoff_land_scenario.json"; then
  dump_logs
  exit 1
fi

wait "$observer_pid"
unset observer_pid

if ! grep -q '"saw_armed": true' "$CONTAINER_LOG_DIR/takeoff_land_observation.json"; then
  dump_logs
  exit 1
fi

echo '[phase3-container] validating real disarm command forwarding via command status'
ros2 topic pub --once /drone/vehicle_command drone_msgs/msg/VehicleCommand "{command: disarm, target_altitude_m: 0.0}" >/dev/null
if ! python3 robotics/ros2_ws/scripts/wait_for_command_status.py --timeout-s 30 --command disarm > "$CONTAINER_LOG_DIR/disarm_command_status.json"; then
  dump_logs
  exit 1
fi

echo 'phase-3 container validation passed'
INNER_EOS
EOS
}

main "$@"
