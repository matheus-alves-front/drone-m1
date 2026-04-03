#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
WORKSPACE_DIR="$ROOT_DIR/robotics/ros2_ws"

bash "$WORKSPACE_DIR/scripts/validate-workspace.sh"

python3 -m py_compile \
  "$WORKSPACE_DIR/src/drone_safety/drone_safety/contracts.py" \
  "$WORKSPACE_DIR/src/drone_safety/drone_safety/rules.py" \
  "$WORKSPACE_DIR/src/drone_safety/drone_safety/safety_manager_node.py" \
  "$WORKSPACE_DIR/src/drone_safety/test/test_rules.py" \
  "$WORKSPACE_DIR/scripts/wait_for_safety_status.py" \
  "$WORKSPACE_DIR/scripts/wait_for_mission_status.py"

PYTHONPATH="$WORKSPACE_DIR/src/drone_safety" python3 -m unittest discover \
  -s "$WORKSPACE_DIR/src/drone_safety/test" \
  -p "test_*.py"

rg -n "safety_manager_node|geofence|gps_loss|rc_loss|data_link_loss|perception_timeout|perception_latency" "$WORKSPACE_DIR/src/drone_safety" >/dev/null
test -f "$ROOT_DIR/simulation/scenarios/failsafe_gps_loss.json"
test -f "$ROOT_DIR/simulation/scenarios/failsafe_rc_loss.json"
test -f "$ROOT_DIR/simulation/scenarios/geofence_breach.json"

echo "phase-5 local validation passed"
