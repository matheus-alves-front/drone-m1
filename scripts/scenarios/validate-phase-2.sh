#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

VENV_DIR="$ROOT_DIR/.cache/phase-2/venv"
PYTHON_BIN="$VENV_DIR/bin/python"
PYTEST_BIN="$VENV_DIR/bin/pytest"

required_files=(
  "docs/PROJECT-EXECUTION-CHECKLIST.md"
  "docs/contracts/MAVSDK-SCENARIO-RUNNER.md"
  "docs/runbooks/MAVSDK-SCENARIO-RUNNER-RUNBOOK.md"
  "docs/runbooks/PHASE-1-BLOCKER-GAZEBO-HARMONIC-CONTAINER.md"
  "docker/phase1-validation/Dockerfile"
  "packages/shared-py/pyproject.toml"
  "packages/shared-py/requirements-phase2.txt"
  "packages/shared-py/requirements-test.txt"
  "packages/shared-py/src/drone_scenarios/__init__.py"
  "packages/shared-py/src/drone_scenarios/__main__.py"
  "packages/shared-py/src/drone_scenarios/cli.py"
  "packages/shared-py/src/drone_scenarios/contracts.py"
  "packages/shared-py/src/drone_scenarios/errors.py"
  "packages/shared-py/src/drone_scenarios/geodesy.py"
  "packages/shared-py/src/drone_scenarios/loader.py"
  "packages/shared-py/src/drone_scenarios/runner.py"
  "packages/shared-py/src/drone_scenarios/gateways/__init__.py"
  "packages/shared-py/src/drone_scenarios/gateways/base.py"
  "packages/shared-py/src/drone_scenarios/gateways/factory.py"
  "packages/shared-py/src/drone_scenarios/gateways/fake.py"
  "packages/shared-py/src/drone_scenarios/gateways/mavsdk_backend.py"
  "packages/shared-py/tests/conftest.py"
  "packages/shared-py/tests/test_cli.py"
  "packages/shared-py/tests/test_loader.py"
  "packages/shared-py/tests/test_runner.py"
  "scripts/scenarios/run_scenario.sh"
  "scripts/scenarios/run_takeoff_land.sh"
  "scripts/sim/build-phase-1-container-image.sh"
  "scripts/sim/check-gz-harmonic-cli.sh"
  "scripts/scenarios/validate-phase-2-container.sh"
  "simulation/scenarios/takeoff_land.json"
  "simulation/scenarios/takeoff_land.md"
)

for file in "${required_files[@]}"; do
  [[ -f "$file" ]] || { printf 'Missing required phase 2 artifact: %s\n' "$file" >&2; exit 1; }
done

[[ -x scripts/scenarios/run_scenario.sh ]] || { echo 'scripts/scenarios/run_scenario.sh is not executable.' >&2; exit 1; }
[[ -x scripts/scenarios/run_takeoff_land.sh ]] || { echo 'scripts/scenarios/run_takeoff_land.sh is not executable.' >&2; exit 1; }
[[ -x scripts/scenarios/validate-phase-2-container.sh ]] || { echo 'scripts/scenarios/validate-phase-2-container.sh is not executable.' >&2; exit 1; }

grep -q 'Python CLI' docs/decisions/PHASE-0-OPEN-DECISIONS.md || {
  echo 'Phase 0 decisions do not preserve the preferred Python CLI direction for MAVSDK.' >&2
  exit 1
}

grep -q 'MAVSDK' docs/PROJECT-EXECUTION-CHECKLIST.md || {
  echo 'Execution checklist does not mention MAVSDK in Phase 2.' >&2
  exit 1
}

grep -q 'takeoff_land.json' simulation/scenarios/README.md || {
  echo 'Scenarios README does not document the executable contract for Phase 2.' >&2
  exit 1
}

grep -q 'drone_scenarios' docs/contracts/MAVSDK-SCENARIO-RUNNER.md || {
  echo 'Phase 2 contract doc does not reference the official Python runner package.' >&2
  exit 1
}

grep -q '"name": "takeoff_land"' simulation/scenarios/takeoff_land.json || {
  echo 'takeoff_land.json does not declare the expected scenario name.' >&2
  exit 1
}

mkdir -p "$ROOT_DIR/.cache/phase-2"
if [[ ! -x "$PYTHON_BIN" ]]; then
  python3 -m venv "$VENV_DIR"
fi
"$PYTHON_BIN" -m pip install --quiet --upgrade pip
"$PYTHON_BIN" -m pip install --quiet pytest

PYTHONPATH="$ROOT_DIR/packages/shared-py/src${PYTHONPATH:+:$PYTHONPATH}" "$PYTEST_BIN" packages/shared-py/tests >/dev/null

"$ROOT_DIR/scripts/scenarios/run_scenario.sh" \
  "$ROOT_DIR/simulation/scenarios/takeoff_land.json" \
  --backend fake-success \
  --output json >/dev/null

"$ROOT_DIR/scripts/scenarios/run_takeoff_land.sh" \
  --backend fake-success \
  --output json >/dev/null

echo 'Phase 2 structural validation passed.'
