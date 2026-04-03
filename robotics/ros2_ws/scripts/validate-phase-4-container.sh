#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
IMAGE="${PHASE4_CONTAINER_IMAGE:-drone-sim-phase3-humble-harmonic:latest}"
CONTAINER_WORKDIR="/workspace"
HOST_UID="$(id -u)"
HOST_GID="$(id -g)"
HOST_CACHE_DIR="$ROOT_DIR/.cache/phase-4"
CONTAINER_SITE_PACKAGES_DIR="$CONTAINER_WORKDIR/.cache/phase-4/site-packages"
CONTAINER_AGENT_SRC_DIR="$CONTAINER_WORKDIR/.cache/phase-1/micro-xrce-agent/src"
CONTAINER_AGENT_BUILD_DIR="$CONTAINER_WORKDIR/.cache/phase-1/micro-xrce-agent/build"
CONTAINER_AGENT_INSTALL_DIR="$CONTAINER_WORKDIR/.cache/phase-1/micro-xrce-agent/install"
CONTAINER_RUNTIME_DIR="$CONTAINER_WORKDIR/.sim-runtime/phase-4-container"
CONTAINER_LOG_DIR="$CONTAINER_WORKDIR/.sim-logs/phase-4-container"
CONTAINER_ROS_WS_DIR="/tmp/phase4-ros2-ws"
AGENT_TAG="${MICRO_XRCE_AGENT_TAG:-v2.4.3}"
AGENT_BUILD_JOBS="${MICRO_XRCE_AGENT_BUILD_JOBS:-2}"
AGENT_CMAKE_FLAGS="${MICRO_XRCE_AGENT_CMAKE_FLAGS:--DUAGENT_CED_PROFILE=OFF -DUAGENT_DISCOVERY_PROFILE=OFF -DUAGENT_P2P_PROFILE=OFF -DUAGENT_SOCKETCAN_PROFILE=OFF}"
PX4_BUILD_JOBS="${PHASE4_PX4_BUILD_JOBS:-1}"
FORCE_CLEAN_PX4_BUILD="${PHASE4_FORCE_CLEAN_PX4_BUILD:-0}"
SKIP_ROS_WS_BUILD="${PHASE4_SKIP_ROS_WS_BUILD:-0}"
MISSION_TIMEOUT_S="${PHASE4_MISSION_TIMEOUT_S:-240}"
AUTO_BUILD_IMAGE="${PHASE4_CONTAINER_AUTO_BUILD:-1}"

die() {
  printf 'phase-4 container validation failed: %s\n' "$1" >&2
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
    echo "2. Build and test drone_mission together with the existing ROS 2 workspace"
    echo "3. Reuse the cached Micro XRCE-DDS Agent $AGENT_TAG"
    echo "4. Install the phase-2 MAVSDK dependency set needed to configure PX4 simulation params"
    echo "5. Start the real Phase 1 stack with PX4 SITL + Gazebo Harmonic"
    echo "6. Configure PX4 runtime params required by the simulation-first patrol baseline"
    echo "7. Prove the pre-arm baseline (connected, landed and disarmed) before the mission start barrier"
    echo "8. Launch drone_bringup with mission enabled and start patrol_basic through /drone/mission_command"
    echo "9. Validate the real arm sequence: PX4 ACK accepted followed by VehicleState.armed=true after the same barrier"
    echo "10. Validate mission completion on /drone/mission_status and airborne/landed telemetry on /drone/vehicle_state"
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
    -e "FORCE_CLEAN_PX4_BUILD=$FORCE_CLEAN_PX4_BUILD" \
    -e "SKIP_ROS_WS_BUILD=$SKIP_ROS_WS_BUILD" \
    -e "MISSION_TIMEOUT_S=$MISSION_TIMEOUT_S" \
    -e "GZ_PARTITION=phase4-container-preflight" \
    -v "$ROOT_DIR:$CONTAINER_WORKDIR" \
    -w "$CONTAINER_WORKDIR" \
    "$IMAGE" \
    bash -s <<'EOS'
set -euo pipefail
python3 - "$SKIP_ROS_WS_BUILD" "$CONTAINER_RUNTIME_DIR" "$CONTAINER_LOG_DIR" "$CONTAINER_WORKDIR/robotics/ros2_ws/build" "$CONTAINER_WORKDIR/robotics/ros2_ws/install" "$CONTAINER_WORKDIR/robotics/ros2_ws/log" "$CONTAINER_ROS_WS_DIR" <<'PY'
import shutil
import sys
from pathlib import Path

skip_ros_ws_build = sys.argv[1] == "1"

paths = [Path(sys.argv[2]), Path(sys.argv[3])]
if not skip_ros_ws_build:
    paths.extend(Path(raw_path) for raw_path in sys.argv[4:])

for path in paths:
    if path.exists() or path.is_symlink():
        shutil.rmtree(path, ignore_errors=True)
PY
mkdir -p "$CONTAINER_RUNTIME_DIR" "$CONTAINER_LOG_DIR" "$CONTAINER_SITE_PACKAGES_DIR" /tmp/codex-home-user
export HOME=/tmp/codex-home-user

bash <<'INNER_EOS'
set -euo pipefail

dump_logs() {
  for file in \
    "$CONTAINER_LOG_DIR/px4_sim_params.json" \
    "$CONTAINER_LOG_DIR/pre_mission_vehicle_state.json" \
    "$CONTAINER_LOG_DIR/mission_command_pub.log" \
    "$CONTAINER_LOG_DIR/arm_ack.json" \
    "$CONTAINER_LOG_DIR/mission_patrol.json" \
    "$CONTAINER_LOG_DIR/goto_ack.json" \
    "$CONTAINER_LOG_DIR/mission_status.json" \
    "$CONTAINER_LOG_DIR/mission_observation.json" \
    "$CONTAINER_LOG_DIR/bringup.log" \
    "$CONTAINER_LOG_DIR/microxrce_agent.log" \
    "$CONTAINER_LOG_DIR/px4_sitl.log"; do
    if [[ -f "$file" ]]; then
      echo "--- $(basename "$file") ---"
      cat "$file"
    fi
  done
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
  echo '[phase4-container] building Micro XRCE-DDS Agent cache'
  rm -rf "$CONTAINER_AGENT_SRC_DIR" "$CONTAINER_AGENT_BUILD_DIR"
  git clone --branch "$AGENT_TAG" --depth 1 https://github.com/eProsima/Micro-XRCE-DDS-Agent.git "$CONTAINER_AGENT_SRC_DIR"
  cmake -S "$CONTAINER_AGENT_SRC_DIR" -B "$CONTAINER_AGENT_BUILD_DIR" -DCMAKE_BUILD_TYPE=Release $AGENT_CMAKE_FLAGS
  cmake --build "$CONTAINER_AGENT_BUILD_DIR" --target uagent -j"$AGENT_BUILD_JOBS"
fi

if [[ ! -x "$CONTAINER_AGENT_INSTALL_DIR/bin/MicroXRCEAgent" ]]; then
  echo '[phase4-container] installing cached agent artifacts'
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

echo '[phase4-container] preparing ROS 2 workspace'
echo '[phase4-container] installing Python requirements for PX4 runtime configuration'
python3 -m pip install --quiet --upgrade --target "$CONTAINER_SITE_PACKAGES_DIR" -r packages/shared-py/requirements-phase2.txt
export PYTHONPATH="$CONTAINER_WORKDIR/packages/shared-py/src:$CONTAINER_SITE_PACKAGES_DIR${PYTHONPATH:+:$PYTHONPATH}"

set +u
source /opt/ros/humble/setup.bash
set -u
if [[ "$SKIP_ROS_WS_BUILD" == "1" ]]; then
  cd "$CONTAINER_WORKDIR/robotics/ros2_ws"
  test -f install/setup.bash
else
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
  colcon build \
    --executor sequential \
    --parallel-workers 1 \
    --packages-up-to drone_bringup
  colcon test \
    --executor sequential \
    --parallel-workers 1 \
    --packages-select drone_msgs drone_px4 drone_mission drone_bringup
  colcon test-result --verbose
fi
set +u
source install/setup.bash
set -u
cd "$CONTAINER_WORKDIR"

echo '[phase4-container] validating Gazebo Harmonic CLI runtime'
bash scripts/sim/check-gz-harmonic-cli.sh

if [[ "$FORCE_CLEAN_PX4_BUILD" == "1" ]]; then
  echo '[phase4-container] resetting PX4 SITL build directory'
  rm -rf third_party/PX4-Autopilot/build/px4_sitl_default
fi

echo '[phase4-container] starting Phase 1 stack'
if ! MICRO_XRCE_AGENT_BIN="$AGENT_BIN" MICRO_XRCE_AGENT_LD_LIBRARY_PATH="$AGENT_LD_LIBRARY_PATH" PX4_SITL_MAKE_ARGS="-j$PX4_BUILD_JOBS" PHASE1_GZ_DISTRO=harmonic PHASE1_GZ_PARTITION="phase4-container-runtime" PHASE1_RUNTIME_DIR=$CONTAINER_RUNTIME_DIR PHASE1_LOG_DIR=$CONTAINER_LOG_DIR bash scripts/sim/start.sh; then
  dump_logs
  exit 1
fi

deadline=$((SECONDS + 1200))
while true; do
  if [[ -f "$CONTAINER_LOG_DIR/px4_sitl.log" ]] && grep -Fq 'INFO  [px4] Startup script returned successfully' "$CONTAINER_LOG_DIR/px4_sitl.log"; then
    break
  fi
  if pgrep -f '/workspace/third_party/PX4-Autopilot/build/px4_sitl_default/bin/px4' >/dev/null 2>&1 \
    && pgrep -f 'gz sim' >/dev/null 2>&1; then
    break
  fi
  if (( SECONDS >= deadline )); then
    dump_logs
    exit 1
  fi
  sleep 2
done

echo '[phase4-container] configuring PX4 simulation params'
if ! python3 scripts/sim/configure_px4_sim_params.py --timeout-s 30 --set-int NAV_DLL_ACT=0 --set-float COM_DISARM_PRFLT=60 > "$CONTAINER_LOG_DIR/px4_sim_params.json"; then
  dump_logs
  exit 1
fi

echo '[phase4-container] starting ROS 2 bringup with mission enabled'
stdbuf -oL -eL ros2 launch drone_bringup bringup.launch.py enable_mission:=true mission_auto_start:=false > "$CONTAINER_LOG_DIR/bringup.log" 2>&1 &
bringup_pid="$!"
sleep 5

ros2 topic list | tee "$CONTAINER_LOG_DIR/topic_list.txt"
for topic in /drone/vehicle_state /drone/mission_status /drone/vehicle_command_status; do
  if ! grep -q "^${topic}$" "$CONTAINER_LOG_DIR/topic_list.txt"; then
    dump_logs
    exit 1
  fi
done

if ! python3 robotics/ros2_ws/scripts/wait_for_vehicle_state.py --timeout-s 90 --connected true --armed false --landed true --position-valid true --failsafe false > "$CONTAINER_LOG_DIR/pre_mission_vehicle_state.json"; then
  dump_logs
  exit 1
fi

start_barrier_ns="$(python3 -c 'import time; print(time.time_ns())')"

echo '[phase4-container] starting mission through /drone/mission_command'
ros2 topic pub --once /drone/mission_command drone_msgs/msg/MissionCommand "{stamp: {sec: 0, nanosec: 0}, command: start}" > "$CONTAINER_LOG_DIR/mission_command_pub.log"

python3 robotics/ros2_ws/scripts/wait_for_vehicle_state.py --timeout-s "$MISSION_TIMEOUT_S" --min-stamp-ns "$start_barrier_ns" --min-altitude-m 2.0 --require-airborne --require-landed-after-airborne > "$CONTAINER_LOG_DIR/mission_observation.json" &
observer_pid="$!"

if ! python3 robotics/ros2_ws/scripts/wait_for_command_status.py --timeout-s 60 --min-stamp-ns "$start_barrier_ns" --command arm --accepted true > "$CONTAINER_LOG_DIR/arm_ack.json"; then
  dump_logs
  exit 1
fi

if ! python3 robotics/ros2_ws/scripts/wait_for_vehicle_state.py --timeout-s 60 --min-stamp-ns "$start_barrier_ns" --connected true --armed true --failsafe false > "$CONTAINER_LOG_DIR/armed_state.json"; then
  dump_logs
  exit 1
fi

if ! python3 robotics/ros2_ws/scripts/wait_for_mission_status.py --timeout-s "$MISSION_TIMEOUT_S" --phase patrol --active true --min-waypoint-index 1 > "$CONTAINER_LOG_DIR/mission_patrol.json"; then
  dump_logs
  exit 1
fi

if ! python3 robotics/ros2_ws/scripts/wait_for_mission_status.py --timeout-s "$MISSION_TIMEOUT_S" --phase completed --terminal true --succeeded true --completed true --last-command land --min-waypoint-index 3 > "$CONTAINER_LOG_DIR/mission_status.json"; then
  dump_logs
  exit 1
fi

wait "$observer_pid"
unset observer_pid

if ! grep -q '"saw_airborne": true' "$CONTAINER_LOG_DIR/mission_observation.json"; then
  dump_logs
  exit 1
fi

echo 'phase-4 container validation passed'
INNER_EOS
EOS
}

main "$@"
