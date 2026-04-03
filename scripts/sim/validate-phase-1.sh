#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

required_files=(
  "docs/decisions/PHASE-0-OPEN-DECISIONS.md"
  "docs/runbooks/PHASE-1-STARTUP-ORDER.md"
  "docs/runbooks/PHASE-1-BLOCKER-GAZEBO-HARMONIC-CONTAINER.md"
  "docs/runbooks/PX4-SITL-HEADLESS-RUNBOOK.md"
  "docs/decisions/SIMULATION-STACK-DECISIONS.md"
  "docs/PROJECT-EXECUTION-CHECKLIST.md"
  "docker/phase1-validation/Dockerfile"
  "scripts/sim/build-phase-1-container-image.sh"
  "scripts/sim/check-gz-harmonic-cli.sh"
  "scripts/sim/phase-1-manifest.md"
  "scripts/sim/start.sh"
  "scripts/sim/stop.sh"
  "scripts/sim/validate-phase-1-container.sh"
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

if ! grep -q 'v1.16.1' docs/decisions/PHASE-0-OPEN-DECISIONS.md; then
  echo 'Phase 0 decisions do not pin PX4 to v1.16.1.' >&2
  exit 1
fi

if ! grep -q 'release/1.16' docs/decisions/SIMULATION-STACK-DECISIONS.md; then
  echo 'Simulation stack decisions do not align px4_msgs with release/1.16.' >&2
  exit 1
fi

if ! grep -q 'Gazebo Harmonic' docs/decisions/SIMULATION-STACK-DECISIONS.md; then
  echo 'Simulation stack decisions do not declare Gazebo Harmonic.' >&2
  exit 1
fi

if ! grep -Eq 'Gazebo Classic.*nao' docs/decisions/SIMULATION-STACK-DECISIONS.md; then
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

if ! grep -q 'HEADLESS=1 make px4_sitl gz_x500' docs/runbooks/PX4-SITL-HEADLESS-RUNBOOK.md; then
  echo 'Headless PX4 runbook does not contain the official minimal command.' >&2
  exit 1
fi

if ! grep -q 'Ubuntu 22.04' docs/runbooks/PX4-SITL-HEADLESS-RUNBOOK.md; then
  echo 'Headless PX4 runbook does not list Ubuntu 22.04 as the reference environment.' >&2
  exit 1
fi

if ! grep -q 'Gazebo Harmonic' docs/runbooks/PX4-SITL-HEADLESS-RUNBOOK.md; then
  echo 'Headless PX4 runbook does not list Gazebo Harmonic as a prerequisite.' >&2
  exit 1
fi

if ! grep -q 'cmake' docs/runbooks/PX4-SITL-HEADLESS-RUNBOOK.md; then
  echo 'Headless PX4 runbook does not list cmake as a build prerequisite.' >&2
  exit 1
fi

if ! grep -q 'scripts/sim/start.sh' docs/runbooks/PHASE-1-STARTUP-ORDER.md; then
  echo 'Phase 1 startup order does not reference scripts/sim/start.sh.' >&2
  exit 1
fi

if ! grep -q 'scripts/sim/stop.sh' docs/runbooks/PHASE-1-STARTUP-ORDER.md; then
  echo 'Phase 1 startup order does not reference scripts/sim/stop.sh.' >&2
  exit 1
fi

if ! grep -q 'scripts/sim/start.sh' docs/runbooks/PX4-SITL-HEADLESS-RUNBOOK.md; then
  echo 'Headless PX4 runbook does not reference scripts/sim/start.sh.' >&2
  exit 1
fi

if ! grep -q 'scripts/sim/stop.sh' docs/runbooks/PX4-SITL-HEADLESS-RUNBOOK.md; then
  echo 'Headless PX4 runbook does not reference scripts/sim/stop.sh.' >&2
  exit 1
fi

if [[ ! -x scripts/sim/start.sh ]]; then
  echo 'scripts/sim/start.sh is not executable.' >&2
  exit 1
fi

if [[ ! -x scripts/sim/stop.sh ]]; then
  echo 'scripts/sim/stop.sh is not executable.' >&2
  exit 1
fi

if [[ ! -x scripts/sim/validate-phase-1-container.sh ]]; then
  echo 'scripts/sim/validate-phase-1-container.sh is not executable.' >&2
  exit 1
fi

if [[ ! -x scripts/sim/build-phase-1-container-image.sh ]]; then
  echo 'scripts/sim/build-phase-1-container-image.sh is not executable.' >&2
  exit 1
fi

if [[ ! -x scripts/sim/check-gz-harmonic-cli.sh ]]; then
  echo 'scripts/sim/check-gz-harmonic-cli.sh is not executable.' >&2
  exit 1
fi

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if ! git config -f .gitmodules --get submodule.third_party/PX4-Autopilot.path >/dev/null 2>&1; then
    echo 'Git worktree detected, but .gitmodules does not declare third_party/PX4-Autopilot correctly.' >&2
    exit 1
  fi

  if [[ -d third_party/PX4-Autopilot ]] && ! git submodule status -- third_party/PX4-Autopilot >/dev/null 2>&1; then
    echo 'Git worktree detected, but third_party/PX4-Autopilot is not mapped as a valid submodule.' >&2
    exit 1
  fi

  echo 'Phase 1 scaffold validation passed. Git worktree detected and PX4 submodule mapping is valid.'
else
  echo 'Phase 1 scaffold validation passed. PX4 submodule vendoring remains pending because this directory is not currently a Git worktree.'
fi
