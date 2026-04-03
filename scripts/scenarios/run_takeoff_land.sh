#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

exec "$ROOT_DIR/scripts/scenarios/run_scenario.sh" \
  "$ROOT_DIR/simulation/scenarios/takeoff_land.json" \
  "$@"
