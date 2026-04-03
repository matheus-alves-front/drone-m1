#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IMAGE="${PHASE2_CONTAINER_IMAGE:-${PHASE1_CONTAINER_IMAGE:-drone-sim-phase1-harmonic:latest}}"
CONTAINER_WORKDIR="/workspace"
HOST_UID="$(id -u)"
HOST_GID="$(id -g)"
HOST_CACHE_DIR="$ROOT_DIR/.cache/phase-2"
HOST_RUNTIME_DIR="$ROOT_DIR/.sim-runtime/phase-2-container"
HOST_LOG_DIR="$ROOT_DIR/.sim-logs/phase-2-container"
CONTAINER_SITE_PACKAGES_DIR="$CONTAINER_WORKDIR/.cache/phase-2/site-packages"
CONTAINER_RUNTIME_DIR="$CONTAINER_WORKDIR/.sim-runtime/phase-2-container"
CONTAINER_LOG_DIR="$CONTAINER_WORKDIR/.sim-logs/phase-2-container"
CONTAINER_AGENT_INSTALL_DIR="$CONTAINER_WORKDIR/.cache/phase-1/micro-xrce-agent/install"
PX4_BUILD_JOBS="${PHASE2_PX4_BUILD_JOBS:-1}"
SCENARIO_TIMEOUT_S="${PHASE2_SCENARIO_TIMEOUT_S:-180}"
AUTO_BUILD_IMAGE="${PHASE2_CONTAINER_AUTO_BUILD:-1}"

die() {
  printf 'phase-2 container validation failed: %s\n' "$1" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

main() {
  require_cmd docker

  if [[ "${1:-}" == "--check" ]]; then
    echo "Container validation plan:"
    echo "1. Build or reuse clean validation image $IMAGE"
    echo "2. Start $IMAGE and run the simulation flow as the host user"
    echo "3. Reuse the cached Micro XRCE-DDS Agent from Phase 1"
    echo "4. Run a Gazebo Harmonic CLI preflight inside the validation container"
    echo "5. Start the Phase 1 stack with PX4 build parallelism limited to $PX4_BUILD_JOBS job(s)"
    echo "6. Install pytest and mavsdk into a cache-local Python target directory"
    echo "7. Execute scripts/scenarios/run_takeoff_land.sh against PX4 SITL"
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
      rm -rf \"$CONTAINER_WORKDIR/third_party/PX4-Autopilot/build/px4_sitl_default\"
      rm -rf \"$CONTAINER_RUNTIME_DIR\" \"$CONTAINER_LOG_DIR\"
      mkdir -p \"$CONTAINER_RUNTIME_DIR\" \"$CONTAINER_LOG_DIR\" \"$CONTAINER_SITE_PACKAGES_DIR\" /tmp/codex-home-user
      export HOST_UID=$HOST_UID
      export HOST_GID=$HOST_GID
      export HOME=/tmp/codex-home-user
      export CONTAINER_WORKDIR=\"$CONTAINER_WORKDIR\"
      export CONTAINER_SITE_PACKAGES_DIR=\"$CONTAINER_SITE_PACKAGES_DIR\"
      export CONTAINER_RUNTIME_DIR=\"$CONTAINER_RUNTIME_DIR\"
      export CONTAINER_LOG_DIR=\"$CONTAINER_LOG_DIR\"
      export CONTAINER_AGENT_INSTALL_DIR=\"$CONTAINER_AGENT_INSTALL_DIR\"
      export PX4_BUILD_JOBS=\"$PX4_BUILD_JOBS\"
      export SCENARIO_TIMEOUT_S=\"$SCENARIO_TIMEOUT_S\"
      export GZ_PARTITION=phase2-container-preflight
      bash <<'EOS'
set -euo pipefail

dump_logs() {
  if [[ -f "$CONTAINER_LOG_DIR/microxrce_agent.log" ]]; then
    echo '--- microxrce_agent.log ---'
    cat "$CONTAINER_LOG_DIR/microxrce_agent.log"
  fi
  if [[ -f "$CONTAINER_LOG_DIR/px4_sitl.log" ]]; then
    echo '--- px4_sitl.log ---'
    cat "$CONTAINER_LOG_DIR/px4_sitl.log"
  fi
}

cleanup() {
  PHASE1_RUNTIME_DIR=$CONTAINER_RUNTIME_DIR PHASE1_LOG_DIR=$CONTAINER_LOG_DIR bash scripts/sim/stop.sh >/dev/null 2>&1 || true
}

trap cleanup EXIT
cd "$CONTAINER_WORKDIR"

if [[ ! -x "$CONTAINER_AGENT_INSTALL_DIR/bin/MicroXRCEAgent" ]]; then
  echo 'Phase 1 XRCE cache missing; run scripts/sim/validate-phase-1-container.sh first.' >&2
  exit 1
fi

mkdir -p "$CONTAINER_SITE_PACKAGES_DIR"
echo '[phase2-container] installing Python requirements for MAVSDK runner'
python3 -m pip install --quiet --upgrade --target "$CONTAINER_SITE_PACKAGES_DIR" -r packages/shared-py/requirements-phase2.txt -r packages/shared-py/requirements-test.txt

echo '[phase2-container] validating Gazebo Harmonic CLI runtime'
bash scripts/sim/check-gz-harmonic-cli.sh

echo '[phase2-container] resetting PX4 SITL build directory'
rm -rf third_party/PX4-Autopilot/build/px4_sitl_default

echo '[phase2-container] starting Phase 1 stack for MAVSDK scenario execution'
if ! MICRO_XRCE_AGENT_BIN="$CONTAINER_AGENT_INSTALL_DIR/bin/MicroXRCEAgent" MICRO_XRCE_AGENT_LD_LIBRARY_PATH="$CONTAINER_AGENT_INSTALL_DIR/lib" PX4_SITL_MAKE_ARGS="-j$PX4_BUILD_JOBS" PHASE1_GZ_DISTRO=harmonic PHASE1_GZ_PARTITION="phase2-container-runtime" PHASE1_RUNTIME_DIR=$CONTAINER_RUNTIME_DIR PHASE1_LOG_DIR=$CONTAINER_LOG_DIR bash scripts/sim/start.sh; then
  dump_logs
  exit 1
fi

echo '[phase2-container] waiting for PX4 runtime readiness marker'
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

echo '[phase2-container] executing MAVSDK takeoff_land scenario'
export PYTHONPATH="$CONTAINER_WORKDIR/packages/shared-py/src:$CONTAINER_SITE_PACKAGES_DIR${PYTHONPATH:+:$PYTHONPATH}"
if ! timeout "$SCENARIO_TIMEOUT_S" bash scripts/scenarios/run_takeoff_land.sh --system-address udp://:14540 --output json; then
  dump_logs
  exit 1
fi

echo phase-2 container validation passed
EOS
    "
}

main "$@"
