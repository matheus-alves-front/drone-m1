#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <simulation/scenarios/takeoff_land.json> [runner args...]" >&2
  exit 1
fi

SCENARIO_FILE="$1"
shift

case "$SCENARIO_FILE" in
  /*) ;;
  *) SCENARIO_FILE="$ROOT_DIR/$SCENARIO_FILE" ;;
esac

[[ -f "$SCENARIO_FILE" ]] || {
  echo "scenario file not found: $SCENARIO_FILE" >&2
  exit 1
}

scenario_name="$(basename "$SCENARIO_FILE" .json)"
if [[ "$scenario_name" != "takeoff_land" ]]; then
  cat <<EOF >&2
scenario '$scenario_name' is not executed by the MAVSDK CLI wrapper.
Use the phase-specific validators for ROS 2 domain scenarios:
  - patrol_basic -> bash robotics/ros2_ws/scripts/validate-phase-4-container.sh
  - geofence_breach / failsafe_gps_loss / failsafe_rc_loss -> bash robotics/ros2_ws/scripts/validate-phase-5-container.sh
  - perception_target_tracking / perception_timeout -> bash robotics/ros2_ws/scripts/validate-phase-6-container.sh
  - full maturity suite -> bash scripts/ci/validate-phase-8.sh
EOF
  exit 2
fi

export PYTHONPATH="$ROOT_DIR/packages/shared-py/src${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m drone_scenarios takeoff_land --scenario-file "$SCENARIO_FILE" "$@"
