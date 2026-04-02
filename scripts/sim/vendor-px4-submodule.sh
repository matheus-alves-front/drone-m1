#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PX4_PATH="$ROOT_DIR/third_party/PX4-Autopilot"
PX4_REMOTE_URL="${PX4_REMOTE_URL:-https://github.com/PX4/PX4-Autopilot.git}"
PX4_TAG="${PX4_TAG:-v1.16.1}"

cd "$ROOT_DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "This directory is not a valid Git worktree. PX4 must be vendorized as a git submodule." >&2
  exit 1
fi

if [[ -e "$PX4_PATH" ]] && ! git submodule status -- "$PX4_PATH" >/dev/null 2>&1; then
  echo "Path $PX4_PATH already exists but is not registered as a git submodule." >&2
  echo "Remove the conflicting path before adding the PX4 submodule." >&2
  exit 1
fi

if git submodule status -- "$PX4_PATH" >/dev/null 2>&1; then
  git submodule update --init --recursive "$PX4_PATH"
else
  git submodule add "$PX4_REMOTE_URL" "$PX4_PATH"
fi

git -C "$PX4_PATH" fetch --tags --force
git -C "$PX4_PATH" checkout "$PX4_TAG"
git -C "$PX4_PATH" submodule update --init --recursive

cat <<EOF
PX4 submodule prepared at $PX4_PATH
Pinned tag: $PX4_TAG
Next step: align px4_msgs with release/1.16 in the ROS 2 workspace.
EOF
