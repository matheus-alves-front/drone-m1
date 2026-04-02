#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

required_files=(
  "docs/PHASE-0-OPEN-DECISIONS.md"
  "docs/SIMULATION-STACK-DECISIONS.md"
  "docs/PROJECT-EXECUTION-CHECKLIST.md"
  "scripts/sim/phase-1-manifest.md"
  "scripts/sim/vendor-px4-submodule.sh"
  "third_party/PX4-Autopilot.SUBMODULE.md"
  "simulation/README.md"
  "simulation/gazebo/README.md"
  "simulation/gazebo/worlds/README.md"
  "simulation/gazebo/worlds/harmonic_minimal.sdf"
  "simulation/gazebo/models/README.md"
  "simulation/gazebo/models/drone_base/README.md"
  "simulation/gazebo/resources/README.md"
  "simulation/scenarios/README.md"
  "simulation/scenarios/takeoff_land.md"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    printf 'Missing required phase 1 artifact: %s\n' "$file" >&2
    exit 1
  fi
done

if ! grep -q 'v1.16.1' docs/PHASE-0-OPEN-DECISIONS.md; then
  echo 'Phase 0 decisions do not pin PX4 to v1.16.1.' >&2
  exit 1
fi

if ! grep -q 'release/1.16' docs/SIMULATION-STACK-DECISIONS.md; then
  echo 'Simulation stack decisions do not align px4_msgs with release/1.16.' >&2
  exit 1
fi

if ! grep -q 'Gazebo Harmonic' docs/SIMULATION-STACK-DECISIONS.md; then
  echo 'Simulation stack decisions do not declare Gazebo Harmonic.' >&2
  exit 1
fi

if ! grep -Eq 'Gazebo Classic.*nao' docs/SIMULATION-STACK-DECISIONS.md; then
  echo 'Simulation stack decisions do not explicitly reject Gazebo Classic.' >&2
  exit 1
fi

if ! grep -q 'harmonic_minimal.sdf' simulation/gazebo/worlds/README.md; then
  echo 'Worlds README does not describe the initial Harmonic world.' >&2
  exit 1
fi

if ! grep -q 'takeoff_land.md' simulation/scenarios/README.md; then
  echo 'Scenarios README does not describe the initial takeoff/land scenario.' >&2
  exit 1
fi

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo 'Phase 1 scaffold validation passed. Git worktree detected; PX4 submodule can now be vendorized with scripts/sim/vendor-px4-submodule.sh.'
else
  echo 'Phase 1 scaffold validation passed. PX4 submodule vendoring remains pending because this directory is not currently a Git worktree.'
fi
