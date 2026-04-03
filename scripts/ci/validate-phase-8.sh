#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

run_local=1
run_runtime=1

print_plan() {
  cat <<'EOF'
Phase 8 validation plan:
1. Run bootstrap and structural validations for the monorepo.
2. Re-run the local validators that consolidate phases 1, 2, 4, 5, 6 and 7.
3. Assert that the mandatory scenario contracts exist in simulation/scenarios/.
4. Re-run the runtime validators that prove:
   - minimal stack startup
   - takeoff_land
   - patrol_basic
   - geofence_breach
   - failsafe_gps_loss
   - failsafe_rc_loss
   - perception_timeout
5. Exit successfully only when local quality gates and runtime smoke/failure scenarios pass.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check)
      print_plan
      exit 0
      ;;
    --local-only)
      run_runtime=0
      ;;
    --runtime-only)
      run_local=0
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 1
      ;;
  esac
  shift
done

run_local_suite() {
  bash "$ROOT_DIR/scripts/bootstrap/validate-phase-0.sh"
  python3 -m unittest "$ROOT_DIR/scripts/tooling/tests/test_phase0_structure.py"

  bash "$ROOT_DIR/robotics/ros2_ws/scripts/validate-workspace.sh"
  bash "$ROOT_DIR/scripts/sim/validate-phase-1.sh"
  bash "$ROOT_DIR/scripts/scenarios/validate-phase-2.sh"
  bash "$ROOT_DIR/robotics/ros2_ws/scripts/validate-phase-4.sh"
  bash "$ROOT_DIR/robotics/ros2_ws/scripts/validate-phase-5.sh"
  bash "$ROOT_DIR/robotics/ros2_ws/scripts/validate-phase-6.sh"
  bash "$ROOT_DIR/robotics/ros2_ws/scripts/validate-phase-7.sh"

  test -f "$ROOT_DIR/simulation/scenarios/takeoff_land.json"
  test -f "$ROOT_DIR/simulation/scenarios/patrol_basic.json"
  test -f "$ROOT_DIR/simulation/scenarios/failsafe_gps_loss.json"
  test -f "$ROOT_DIR/simulation/scenarios/failsafe_rc_loss.json"
  test -f "$ROOT_DIR/simulation/scenarios/geofence_breach.json"
  test -f "$ROOT_DIR/docs/runbooks/SIMULATION-OPERATIONS-TROUBLESHOOTING.md"
  test -f "$ROOT_DIR/docs/decisions/HARDWARE-MIGRATION-CRITERIA.md"
}

run_runtime_suite() {
  bash "$ROOT_DIR/scripts/sim/validate-phase-1-container.sh"
  bash "$ROOT_DIR/scripts/scenarios/validate-phase-2-container.sh"
  bash "$ROOT_DIR/robotics/ros2_ws/scripts/validate-phase-4-container.sh"
  bash "$ROOT_DIR/robotics/ros2_ws/scripts/validate-phase-5-container.sh"
  bash "$ROOT_DIR/robotics/ros2_ws/scripts/validate-phase-6-container.sh"
}

if [[ "$run_local" == "1" ]]; then
  run_local_suite
fi

if [[ "$run_runtime" == "1" ]]; then
  run_runtime_suite
fi

echo "phase-8 validation passed"
