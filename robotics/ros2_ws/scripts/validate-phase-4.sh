#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
WORKSPACE_DIR="$ROOT_DIR/robotics/ros2_ws"

bash "$WORKSPACE_DIR/scripts/validate-workspace.sh"

python3 -m py_compile \
  "$WORKSPACE_DIR/src/drone_mission/drone_mission/contracts.py" \
  "$WORKSPACE_DIR/src/drone_mission/drone_mission/geodesy.py" \
  "$WORKSPACE_DIR/src/drone_mission/drone_mission/gateway.py" \
  "$WORKSPACE_DIR/src/drone_mission/drone_mission/fake_gateway.py" \
  "$WORKSPACE_DIR/src/drone_mission/drone_mission/loader.py" \
  "$WORKSPACE_DIR/src/drone_mission/drone_mission/mission_executor.py" \
  "$WORKSPACE_DIR/src/drone_mission/drone_mission/mission_manager_node.py" \
  "$WORKSPACE_DIR/src/drone_mission/drone_mission/mission_state_machine.py" \
  "$WORKSPACE_DIR/scripts/wait_for_mission_status.py"

rg -n "mission_manager_node|MissionPhase|abort|return_to_home|patrol|ros2_domain|vehicle_command_status" "$WORKSPACE_DIR/src/drone_mission" >/dev/null
test -f "$ROOT_DIR/simulation/scenarios/patrol_basic.json"

echo "phase-4 local validation passed"
