#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
DOCKERFILE_PATH="${PHASE3_CONTAINER_DOCKERFILE:-$REPO_ROOT/docker/phase3-validation/Dockerfile}"
BUILD_CONTEXT="${PHASE3_CONTAINER_BUILD_CONTEXT:-$REPO_ROOT/docker/phase3-validation}"
BASE_IMAGE="${PHASE3_CONTAINER_BASE_IMAGE:-${PHASE1_CONTAINER_IMAGE:-drone-sim-phase1-harmonic:latest}}"
IMAGE_TAG="${PHASE3_VALIDATION_IMAGE:-drone-sim-phase3-humble-harmonic:latest}"
AUTO_BUILD_PHASE1="${PHASE3_CONTAINER_AUTO_BUILD_PHASE1:-1}"

die() {
  printf 'phase-3 image build failed: %s\n' "$1" >&2
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
Phase 3 validation image build plan:
1. Ensure the Phase 1 base image exists: $BASE_IMAGE
2. Build Dockerfile: $DOCKERFILE_PATH
3. Build context: $BUILD_CONTEXT
4. Install ROS 2 Humble build/runtime packages on top of the Phase 1 image
5. Tag the resulting image as: $IMAGE_TAG
EOF
    exit 0
  fi

  if ! docker image inspect "$BASE_IMAGE" >/dev/null 2>&1; then
    bash "$REPO_ROOT/scripts/sim/build-phase-1-container-image.sh"
  elif [[ "$AUTO_BUILD_PHASE1" == "1" ]]; then
    bash "$REPO_ROOT/scripts/sim/build-phase-1-container-image.sh"
  fi

  docker build \
    --build-arg "PHASE3_CONTAINER_BASE_IMAGE=$BASE_IMAGE" \
    --tag "$IMAGE_TAG" \
    --file "$DOCKERFILE_PATH" \
    "$BUILD_CONTEXT"
}

main "$@"
