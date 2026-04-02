#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

required_paths=(
  "$ROOT_DIR/README.md"
  "$ROOT_DIR/src/drone_bringup/package.xml"
  "$ROOT_DIR/src/drone_bringup/setup.py"
  "$ROOT_DIR/src/drone_bringup/setup.cfg"
  "$ROOT_DIR/src/drone_bringup/drone_bringup/__init__.py"
  "$ROOT_DIR/src/drone_bringup/drone_bringup/launch/bringup.launch.py"
  "$ROOT_DIR/src/drone_bringup/test/test_package.py"
  "$ROOT_DIR/src/drone_msgs/package.xml"
  "$ROOT_DIR/src/drone_msgs/CMakeLists.txt"
  "$ROOT_DIR/src/drone_msgs/msg/README.md"
)

for path in "${required_paths[@]}"; do
  if [[ ! -e "$path" ]]; then
    echo "missing required workspace artifact: $path" >&2
    exit 1
  fi
done

python3 -m py_compile \
  "$ROOT_DIR/src/drone_bringup/drone_bringup/launch/bringup.launch.py" \
  "$ROOT_DIR/src/drone_bringup/test/test_package.py"

echo "workspace bootstrap validation passed"
