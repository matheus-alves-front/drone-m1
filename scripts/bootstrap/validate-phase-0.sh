#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

required_files=(
  "README.md"
  "docs/PROJECT-SCOPE.md"
  "docs/SIMULATION-ARCHITECTURE.md"
  "docs/PROJECT-ARCHITECTURE.md"
  "docs/MONOREPO-STRUCTURE.md"
  "docs/AGENTS-AND-SKILLS.md"
  "docs/DEVELOPMENT-STANDARDS.md"
  "docs/TESTING-AND-FAILURE-MODEL.md"
  "docs/CHECKLIST-FRAMEWORK.md"
  "docs/PROJECT-EXECUTION-CHECKLIST.md"
  "docs/PHASE-0-OPEN-DECISIONS.md"
  ".github/workflows/bootstrap-check.yml"
  ".devcontainer/devcontainer.json"
  "robotics/ros2_ws/README.md"
  "robotics/ros2_ws/scripts/validate-workspace.sh"
  "simulation/README.md"
  "simulation/gazebo/README.md"
  "simulation/gazebo/worlds/README.md"
  "simulation/gazebo/models/README.md"
  "simulation/gazebo/resources/README.md"
  "simulation/scenarios/README.md"
  "scripts/sim/README.md"
  "scripts/scenarios/README.md"
  "scripts/tooling/tests/test_phase0_structure.py"
  "services/telemetry-api/README.md"
  "apps/dashboard/README.md"
  "packages/shared-py/README.md"
  "packages/shared-ts/README.md"
  "third_party/README.md"
)

required_dirs=(
  ".agents"
  ".codex"
  "docs"
  "robotics"
  "robotics/ros2_ws"
  "robotics/ros2_ws/src"
  "simulation"
  "simulation/gazebo"
  "simulation/gazebo/worlds"
  "simulation/gazebo/models"
  "simulation/gazebo/resources"
  "simulation/scenarios"
  "scripts"
  "scripts/bootstrap"
  "scripts/sim"
  "scripts/scenarios"
  "scripts/tooling"
  ".github"
  ".github/workflows"
  ".devcontainer"
  "services"
  "services/telemetry-api"
  "apps"
  "apps/dashboard"
  "packages"
  "packages/shared-py"
  "packages/shared-ts"
  "third_party"
)

for dir in "${required_dirs[@]}"; do
  if [[ ! -d "$dir" ]]; then
    printf 'Missing required directory: %s\n' "$dir" >&2
    exit 1
  fi
done

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    printf 'Missing required file: %s\n' "$file" >&2
    exit 1
  fi
done

if ! grep -q 'docs/PROJECT-EXECUTION-CHECKLIST.md' README.md; then
  echo 'README.md does not reference docs/PROJECT-EXECUTION-CHECKLIST.md' >&2
  exit 1
fi

if ! grep -q '^## Fase 0 - Bootstrap$' docs/PROJECT-EXECUTION-CHECKLIST.md; then
  echo 'Checklist does not define the Fase 0 - Bootstrap section' >&2
  exit 1
fi

for phase in 1 2 3 4 5 6 7 8; do
  if ! grep -q "^## Fase ${phase} -" docs/PROJECT-EXECUTION-CHECKLIST.md; then
    printf 'Checklist does not define phase %s\n' "$phase" >&2
    exit 1
  fi
done

if ! grep -q 'scripts/bootstrap/validate-phase-0.sh' .github/workflows/bootstrap-check.yml; then
  echo 'CI workflow does not call scripts/bootstrap/validate-phase-0.sh' >&2
  exit 1
fi

if ! grep -q 'docs/PHASE-0-OPEN-DECISIONS.md' docs/PROJECT-EXECUTION-CHECKLIST.md; then
  echo 'Checklist does not reference docs/PHASE-0-OPEN-DECISIONS.md' >&2
  exit 1
fi

bash robotics/ros2_ws/scripts/validate-workspace.sh >/dev/null

echo 'Phase 0 bootstrap validation passed.'
