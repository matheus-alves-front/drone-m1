#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$ROOT_DIR/../.." && pwd)"
TEST_PYTHON_BIN="${TEST_PYTHON_BIN:-python3}"

ensure_test_python() {
  local venv_dir="$REPO_ROOT/.cache/phase7-venv"
  if [[ ! -x "$venv_dir/bin/python" ]]; then
    python3 -m venv "$venv_dir"
  fi
  if ! "$venv_dir/bin/python" -m pip --version >/dev/null 2>&1; then
    "$venv_dir/bin/python" -m ensurepip --upgrade >/dev/null 2>&1
  fi
  "$venv_dir/bin/python" -m pip install --quiet -r "$REPO_ROOT/packages/shared-py/requirements-test.txt" >/dev/null
  "$venv_dir/bin/python" -m pip install --quiet -r "$REPO_ROOT/services/telemetry-api/requirements.txt" >/dev/null
  TEST_PYTHON_BIN="$venv_dir/bin/python"
}

ensure_dashboard_deps() {
  if [[ ! -d "$REPO_ROOT/apps/dashboard/node_modules" ]]; then
    npm install --prefix "$REPO_ROOT/apps/dashboard" --no-fund --no-audit >/dev/null
  fi
}

ensure_test_python
ensure_dashboard_deps

python3 -m py_compile \
  "$ROOT_DIR/src/drone_telemetry/drone_telemetry/contracts.py" \
  "$ROOT_DIR/src/drone_telemetry/drone_telemetry/serializers.py" \
  "$ROOT_DIR/src/drone_telemetry/drone_telemetry/transport.py" \
  "$ROOT_DIR/src/drone_telemetry/drone_telemetry/telemetry_bridge_node.py"

PYTHONPATH="$ROOT_DIR/src/drone_telemetry" python3 -m unittest discover \
  -s "$ROOT_DIR/src/drone_telemetry/test" \
  -p "test_*.py"

PYTHONPATH="$REPO_ROOT/services/telemetry-api" "$TEST_PYTHON_BIN" -m pytest \
  "$REPO_ROOT/services/telemetry-api/tests" -q

npm test --prefix "$REPO_ROOT/apps/dashboard"
npm run --prefix "$REPO_ROOT/apps/dashboard" build

rg -n "telemetry|metrics|replay|dashboard|log" "$ROOT_DIR" "$REPO_ROOT/services" "$REPO_ROOT/apps" >/dev/null

echo "phase-7 validation passed"
