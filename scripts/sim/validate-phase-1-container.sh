#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IMAGE="${PHASE1_CONTAINER_IMAGE:-drone-sim-phase1-harmonic:latest}"
CONTAINER_WORKDIR="/workspace"
HOST_UID="$(id -u)"
HOST_GID="$(id -g)"
HOST_CACHE_DIR="$ROOT_DIR/.cache/phase-1/micro-xrce-agent"
HOST_AGENT_INSTALL_DIR="$HOST_CACHE_DIR/install"
HOST_RUNTIME_DIR="$ROOT_DIR/.sim-runtime/phase-1-container"
HOST_LOG_DIR="$ROOT_DIR/.sim-logs/phase-1-container"
CONTAINER_AGENT_SRC_DIR="$CONTAINER_WORKDIR/.cache/phase-1/micro-xrce-agent/src"
CONTAINER_AGENT_BUILD_DIR="$CONTAINER_WORKDIR/.cache/phase-1/micro-xrce-agent/build"
CONTAINER_AGENT_INSTALL_DIR="$CONTAINER_WORKDIR/.cache/phase-1/micro-xrce-agent/install"
CONTAINER_RUNTIME_DIR="$CONTAINER_WORKDIR/.sim-runtime/phase-1-container"
CONTAINER_LOG_DIR="$CONTAINER_WORKDIR/.sim-logs/phase-1-container"
AGENT_TAG="${MICRO_XRCE_AGENT_TAG:-v2.4.3}"
AGENT_BUILD_JOBS="${MICRO_XRCE_AGENT_BUILD_JOBS:-2}"
AGENT_CMAKE_FLAGS="${MICRO_XRCE_AGENT_CMAKE_FLAGS:--DUAGENT_CED_PROFILE=OFF -DUAGENT_DISCOVERY_PROFILE=OFF -DUAGENT_P2P_PROFILE=OFF -DUAGENT_SOCKETCAN_PROFILE=OFF}"
PX4_BUILD_JOBS="${PHASE1_PX4_BUILD_JOBS:-2}"
AUTO_BUILD_IMAGE="${PHASE1_CONTAINER_AUTO_BUILD:-1}"

die() {
  printf 'phase-1 container validation failed: %s\n' "$1" >&2
  exit 1
}

require_cmd() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || die "missing required command: $cmd"
}

main() {
  require_cmd docker
  require_cmd id

  if [[ "${1:-}" == "--check" ]]; then
    echo "Container validation plan:"
    echo "1. Build or reuse clean validation image $IMAGE"
    echo "2. Start $IMAGE as the host user against $ROOT_DIR"
    echo "3. Build and cache Micro XRCE-DDS Agent $AGENT_TAG in $HOST_CACHE_DIR"
    echo "4. Build with $AGENT_BUILD_JOBS job(s) and flags: $AGENT_CMAKE_FLAGS"
    echo "5. Run a Gazebo Harmonic CLI preflight inside the validation container"
    echo "6. Run scripts/sim/start.sh with PX4 build parallelism limited to $PX4_BUILD_JOBS job(s)"
    echo "7. Wait for PX4 runtime log markers and stop the stack"
    exit 0
  fi

  mkdir -p "$HOST_CACHE_DIR"

  if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
    bash "$ROOT_DIR/scripts/sim/build-phase-1-container-image.sh"
  elif [[ "$AUTO_BUILD_IMAGE" == "1" ]]; then
    bash "$ROOT_DIR/scripts/sim/build-phase-1-container-image.sh"
  fi

  docker run --rm \
    --user "$HOST_UID:$HOST_GID" \
    -e "HOME=/tmp/codex-home-user" \
    -v "$ROOT_DIR:$CONTAINER_WORKDIR" \
    -w "$CONTAINER_WORKDIR" \
    "$IMAGE" \
    bash -lc "
      set -euo pipefail
      rm -rf \"$CONTAINER_RUNTIME_DIR\" \"$CONTAINER_LOG_DIR\"
      mkdir -p \"$CONTAINER_RUNTIME_DIR\" \"$CONTAINER_LOG_DIR\" /tmp/codex-home-user
      export HOST_UID=$HOST_UID
      export HOST_GID=$HOST_GID
      export CONTAINER_WORKDIR=\"$CONTAINER_WORKDIR\"
      export CONTAINER_AGENT_SRC_DIR=\"$CONTAINER_AGENT_SRC_DIR\"
      export CONTAINER_AGENT_BUILD_DIR=\"$CONTAINER_AGENT_BUILD_DIR\"
      export CONTAINER_AGENT_INSTALL_DIR=\"$CONTAINER_AGENT_INSTALL_DIR\"
      export CONTAINER_RUNTIME_DIR=\"$CONTAINER_RUNTIME_DIR\"
      export CONTAINER_LOG_DIR=\"$CONTAINER_LOG_DIR\"
      export AGENT_TAG=\"$AGENT_TAG\"
      export AGENT_BUILD_JOBS=\"$AGENT_BUILD_JOBS\"
      export AGENT_CMAKE_FLAGS=\"$AGENT_CMAKE_FLAGS\"
      export PX4_BUILD_JOBS=\"$PX4_BUILD_JOBS\"
      export GZ_PARTITION=phase1-container-preflight
      export PHASE1_GZ_PARTITION=phase1-container-runtime
      bash <<'EOS'
set -euo pipefail

dump_logs() {
  if [[ -f \"$CONTAINER_LOG_DIR/microxrce_agent.log\" ]]; then
    echo '--- microxrce_agent.log ---'
    cat \"$CONTAINER_LOG_DIR/microxrce_agent.log\"
  fi
  if [[ -f \"$CONTAINER_LOG_DIR/px4_sitl.log\" ]]; then
    echo '--- px4_sitl.log ---'
    cat \"$CONTAINER_LOG_DIR/px4_sitl.log\"
  fi
}

cleanup() {
  PHASE1_RUNTIME_DIR=$CONTAINER_RUNTIME_DIR PHASE1_LOG_DIR=$CONTAINER_LOG_DIR bash scripts/sim/stop.sh >/dev/null 2>&1 || true
}

trap cleanup EXIT
cd \"$CONTAINER_WORKDIR\"

if ! find \"$CONTAINER_AGENT_BUILD_DIR\" -type f -name MicroXRCEAgent | grep -q .; then
  echo '[phase1-container] building Micro XRCE-DDS Agent cache'
  rm -rf \"$CONTAINER_AGENT_SRC_DIR\" \"$CONTAINER_AGENT_BUILD_DIR\"
  git clone --branch \"$AGENT_TAG\" --depth 1 https://github.com/eProsima/Micro-XRCE-DDS-Agent.git \"$CONTAINER_AGENT_SRC_DIR\"
  cmake -S \"$CONTAINER_AGENT_SRC_DIR\" -B \"$CONTAINER_AGENT_BUILD_DIR\" -DCMAKE_BUILD_TYPE=Release $AGENT_CMAKE_FLAGS
  cmake --build \"$CONTAINER_AGENT_BUILD_DIR\" --target uagent -j\"$AGENT_BUILD_JOBS\"
fi

echo '[phase1-container] resolving cached agent artifacts'
if [[ ! -x \"$CONTAINER_AGENT_INSTALL_DIR/bin/MicroXRCEAgent\" ]]; then
  echo '[phase1-container] installing cached agent artifacts'
  rm -rf \"$CONTAINER_AGENT_INSTALL_DIR\"
  cmake --install \"$CONTAINER_AGENT_BUILD_DIR\" --prefix \"$CONTAINER_AGENT_INSTALL_DIR\"
fi

if [[ -x \"$CONTAINER_AGENT_INSTALL_DIR/bin/MicroXRCEAgent\" ]]; then
  AGENT_BIN=\"$CONTAINER_AGENT_INSTALL_DIR/bin/MicroXRCEAgent\"
  AGENT_LD_LIBRARY_PATH=\"$CONTAINER_AGENT_INSTALL_DIR/lib\"
else
  AGENT_BIN=\$(find \"$CONTAINER_AGENT_BUILD_DIR\" -type f -name MicroXRCEAgent | head -n 1)
  test -n \"\$AGENT_BIN\"
  test -x \"\$AGENT_BIN\"
  AGENT_LD_LIBRARY_PATH=\$(find \"$CONTAINER_AGENT_BUILD_DIR\" -type f \\( -name 'libmicroxrcedds_agent.so*' -o -name 'libfastrtps.so*' -o -name 'libfastcdr.so*' -o -name 'libmicrocdr.so*' -o -name 'libfoonathan_memory*.so*' \\) -printf '%h\n' | awk '!seen[\$0]++' | paste -sd:)
  test -n \"\$AGENT_LD_LIBRARY_PATH\"
fi

echo '[phase1-container] validating Gazebo Harmonic CLI runtime'
bash scripts/sim/check-gz-harmonic-cli.sh

echo '[phase1-container] resetting PX4 SITL build directory'
rm -rf third_party/PX4-Autopilot/build/px4_sitl_default

echo '[phase1-container] starting Phase 1 stack'
if ! MICRO_XRCE_AGENT_BIN=\"\$AGENT_BIN\" MICRO_XRCE_AGENT_LD_LIBRARY_PATH=\"\$AGENT_LD_LIBRARY_PATH\" PX4_SITL_MAKE_ARGS=\"-j\$PX4_BUILD_JOBS\" PHASE1_GZ_DISTRO=harmonic PHASE1_GZ_PARTITION=\"\$PHASE1_GZ_PARTITION\" PHASE1_RUNTIME_DIR=$CONTAINER_RUNTIME_DIR PHASE1_LOG_DIR=$CONTAINER_LOG_DIR bash scripts/sim/start.sh; then
  dump_logs
  exit 1
fi

echo '[phase1-container] waiting for PX4 runtime readiness marker'
deadline=$((SECONDS + 1200))
while true; do
  if [[ -f \"$CONTAINER_LOG_DIR/px4_sitl.log\" ]] && grep -Fq 'INFO  [px4] Startup script returned successfully' \"$CONTAINER_LOG_DIR/px4_sitl.log\"; then
    break
  fi
  if (( SECONDS >= deadline )); then
    dump_logs
    exit 1
  fi
  sleep 2
done

test -s \"$CONTAINER_LOG_DIR/microxrce_agent.log\"
echo phase-1 container validation passed
EOS
    "
}

main "$@"
