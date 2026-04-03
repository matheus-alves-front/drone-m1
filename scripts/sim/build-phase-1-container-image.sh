#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DOCKERFILE_PATH="${PHASE1_CONTAINER_DOCKERFILE:-$ROOT_DIR/docker/phase1-validation/Dockerfile}"
BUILD_CONTEXT="${PHASE1_CONTAINER_BUILD_CONTEXT:-$ROOT_DIR/docker/phase1-validation}"
BASE_IMAGE="${PHASE1_CONTAINER_BASE_IMAGE:-px4io/px4-dev-base-jammy:latest}"
IMAGE_TAG="${PHASE1_CONTAINER_IMAGE:-drone-sim-phase1-harmonic:latest}"

die() {
  printf 'phase-1 image build failed: %s\n' "$1" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

main() {
  require_cmd docker

  [[ -f "$DOCKERFILE_PATH" ]] || die "missing Dockerfile: $DOCKERFILE_PATH"
  [[ -d "$BUILD_CONTEXT" ]] || die "missing build context directory: $BUILD_CONTEXT"

  if [[ "${1:-}" == "--check" ]]; then
    cat <<EOF
Phase 1 validation image build plan:
1. Use clean PX4 Jammy base image: $BASE_IMAGE
2. Build Dockerfile: $DOCKERFILE_PATH
3. Build context: $BUILD_CONTEXT
4. Install Gazebo Harmonic CLI/runtime packages in the image
5. Tag the resulting image as: $IMAGE_TAG
EOF
    exit 0
  fi

  docker build \
    --pull \
    --build-arg "PHASE1_CONTAINER_BASE_IMAGE=$BASE_IMAGE" \
    --tag "$IMAGE_TAG" \
    --file "$DOCKERFILE_PATH" \
    "$BUILD_CONTEXT"
}

main "$@"
