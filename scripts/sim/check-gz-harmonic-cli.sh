#!/usr/bin/env bash

set -euo pipefail

die() {
  printf 'gazebo harmonic preflight failed: %s\n' "$1" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

dump_context() {
  echo '--- gz package context ---'
  dpkg -l | grep -E '^ii  (gz-|libgz-)' || true
  echo '--- gz binaries ---'
  ls /usr/bin | grep -E '^gz' | sort || true
}

check_baseline() {
  if command -v dpkg-query >/dev/null 2>&1; then
    if dpkg-query -W -f='${Status}\n' gz-garden 2>/dev/null | grep -Fxq 'install ok installed'; then
      die "validation environment still contains gz-garden; use the clean Jammy + Harmonic image instead"
    fi

    if ! dpkg-query -W -f='${Status}\n' gz-harmonic 2>/dev/null | grep -Fxq 'install ok installed'; then
      die "gz-harmonic is not installed in the current validation environment"
    fi
  fi
}

main() {
  require_cmd gz
  require_cmd timeout
  check_baseline

  export GZ_PARTITION="${GZ_PARTITION:-drone-sim-preflight}"

  local version_log
  local sim_log
  local service_log
  version_log="$(mktemp)"
  sim_log="$(mktemp)"
  service_log="$(mktemp)"

  if ! gz sim --versions >"$version_log" 2>&1; then
    cat "$version_log" >&2 || true
    dump_context >&2
    die "gz sim --versions did not execute successfully in this environment"
  fi

  if ! timeout 20 bash -lc '
    set -euo pipefail
    gz sim -r -s /usr/share/gz/gz-sim8/worlds/default.sdf >"'"$sim_log"'" 2>&1 &
    pid=$!
    trap "kill $pid >/dev/null 2>&1 || true; wait $pid >/dev/null 2>&1 || true" EXIT
    sleep 3
    gz service -i --service /world/default/scene/info >"'"$service_log"'" 2>&1
  '; then
    echo '--- gz sim --versions ---' >&2
    cat "$version_log" >&2 || true
    echo '--- gz service ---' >&2
    cat "$service_log" >&2 || true
    echo '--- gz sim ---' >&2
    cat "$sim_log" >&2 || true
    dump_context >&2
    die "Gazebo Harmonic CLI runtime is not healthy enough for PX4 SITL validation"
  fi
}

main "$@"
