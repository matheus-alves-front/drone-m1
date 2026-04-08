#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ROS_DISTRO="${MARK1_ROS_DISTRO:-humble}"
PYTHON_VERSION="${MARK1_PYTHON_VERSION:-3.11}"
NODE_MAJOR="${MARK1_NODE_MAJOR:-20}"
AGENT_TAG="${MARK1_MICRO_XRCE_AGENT_TAG:-v2.4.3}"
VENV_DIR="${MARK1_VENV_DIR:-$ROOT_DIR/.venv-r3}"
MIN_FREE_GB="${MARK1_MIN_FREE_GB:-35}"
RECOMMENDED_DISK_GB="${MARK1_RECOMMENDED_DISK_GB:-80}"
AGENT_SRC_DIR="$ROOT_DIR/.cache/phase-1/micro-xrce-agent/src"
AGENT_BUILD_DIR="$ROOT_DIR/.cache/phase-1/micro-xrce-agent/build"
AGENT_INSTALL_DIR="$ROOT_DIR/.cache/phase-1/micro-xrce-agent/install"

die() {
  printf 'mark1 bootstrap failed: %s\n' "$1" >&2
  exit 1
}

log() {
  printf '[mark1-bootstrap] %s\n' "$1"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

resolve_system_python_bin() {
  local python_bin="/usr/bin/python${PYTHON_VERSION}"

  if [[ -x "$python_bin" ]]; then
    printf '%s\n' "$python_bin"
    return
  fi

  python_bin="$(PATH=/usr/sbin:/usr/bin:/sbin:/bin command -v "python${PYTHON_VERSION}" || true)"
  [[ -n "$python_bin" ]] || die "missing python${PYTHON_VERSION}; rerun the bootstrap after apt dependencies are installed"
  printf '%s\n' "$python_bin"
}

find_system_python_bin() {
  local python_bin="/usr/bin/python${PYTHON_VERSION}"

  if [[ -x "$python_bin" ]]; then
    printf '%s\n' "$python_bin"
    return
  fi

  PATH=/usr/sbin:/usr/bin:/sbin:/bin command -v "python${PYTHON_VERSION}" 2>/dev/null || true
}

assert_ubuntu_jammy() {
  if [[ "${MARK1_SKIP_OS_CHECK:-0}" == "1" ]]; then
    log "skipping Ubuntu baseline check because MARK1_SKIP_OS_CHECK=1"
    return
  fi

  [[ -f /etc/os-release ]] || die "missing /etc/os-release"
  # shellcheck disable=SC1091
  source /etc/os-release
  [[ "${ID:-}" == "ubuntu" ]] || die "baseline expects Ubuntu 22.04"
  [[ "${VERSION_ID:-}" == "22.04" ]] || die "baseline expects Ubuntu 22.04"
  [[ "${VERSION_CODENAME:-}" == "jammy" ]] || die "baseline expects Ubuntu 22.04 jammy"
}

assert_disk_budget() {
  if [[ "${MARK1_SKIP_DISK_CHECK:-0}" == "1" ]]; then
    log "skipping disk budget check because MARK1_SKIP_DISK_CHECK=1"
    return
  fi

  local free_gb
  free_gb="$(df --output=avail -BG "$ROOT_DIR" | tail -n 1 | tr -dc '0-9')"
  [[ -n "$free_gb" ]] || die "unable to determine free disk space"

  if (( free_gb < MIN_FREE_GB )); then
    die "need at least ${MIN_FREE_GB}G free to bootstrap Mark 1 safely; current free space is ${free_gb}G. Recommended VM disk size is ${RECOMMENDED_DISK_GB}G."
  fi
}

install_base_apt_packages() {
  log "installing base Ubuntu packages"
  sudo apt-get update -y
  sudo apt-get install -y --no-install-recommends \
    apt-transport-https \
    bc \
    build-essential \
    ca-certificates \
    cmake \
    curl \
    dmidecode \
    git \
    gnupg \
    gnupg2 \
    gstreamer1.0-libav \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-ugly \
    libeigen3-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libimage-exiftool-perl \
    libopencv-dev \
    libunwind-dev \
    libxml2-utils \
    lsb-release \
    ninja-build \
    pkg-config \
    protobuf-compiler \
    rsync \
    software-properties-common \
    wget
}

ensure_deadsnakes_python() {
  local python_bin
  local needs_python_support=0

  python_bin="$(find_system_python_bin)"

  if [[ -z "$python_bin" ]]; then
    needs_python_support=1
  fi

  if ! dpkg-query -W -f='${Status}' "${python_bin}-venv" 2>/dev/null | grep -q "install ok installed"; then
    needs_python_support=1
  fi

  if ! dpkg-query -W -f='${Status}' "${python_bin}-dev" 2>/dev/null | grep -q "install ok installed"; then
    needs_python_support=1
  fi

  if (( ! needs_python_support )) && "$python_bin" -m ensurepip --version >/dev/null 2>&1; then
    return
  fi

  log "ensuring Python ${PYTHON_VERSION} runtime, headers, and venv support from deadsnakes"
  sudo add-apt-repository -y ppa:deadsnakes/ppa
  sudo apt-get update -y
  sudo apt-get install -y --no-install-recommends \
    "python${PYTHON_VERSION}" \
    "python${PYTHON_VERSION}-dev" \
    "python${PYTHON_VERSION}-venv"

  python_bin="$(resolve_system_python_bin)"
  "$python_bin" -m ensurepip --version >/dev/null 2>&1 \
    || die "python${PYTHON_VERSION} is installed but ensurepip is still unavailable; verify python${PYTHON_VERSION}-venv on the VM"
}

ensure_gazebo_repo() {
  if [[ ! -f /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg ]]; then
    log "registering Gazebo Harmonic apt repository"
    sudo wget https://packages.osrfoundation.org/gazebo.gpg -O /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
  fi

  if [[ ! -f /etc/apt/sources.list.d/gazebo-stable.list ]]; then
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable jammy main" \
      | sudo tee /etc/apt/sources.list.d/gazebo-stable.list >/dev/null
  fi

  sudo apt-get update -y
  sudo apt-get install -y --no-install-recommends \
    gz-harmonic \
    gz-sim8-cli \
    gz-tools2 \
    gz-transport13-cli
}

ensure_ros_repo() {
  if [[ ! -f /usr/share/keyrings/ros-archive-keyring.gpg ]]; then
    log "registering ROS 2 apt repository"
    curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
      | sudo gpg --dearmor -o /usr/share/keyrings/ros-archive-keyring.gpg
  fi

  if [[ ! -f /etc/apt/sources.list.d/ros2.list ]]; then
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu jammy main" \
      | sudo tee /etc/apt/sources.list.d/ros2.list >/dev/null
  fi

  sudo apt-get update -y
  sudo apt-get install -y --no-install-recommends \
    python3-colcon-common-extensions \
    python3-pip \
    python3-pytest \
    python3-rosdep \
    python3-vcstool \
    "ros-${ROS_DISTRO}-ament-lint-common" \
    "ros-${ROS_DISTRO}-ros-base"
}

ensure_nodesource_node() {
  local current_major
  current_major="$(node -v 2>/dev/null | sed -E 's/^v([0-9]+).*/\1/' || true)"
  if [[ -n "$current_major" ]] && (( current_major >= NODE_MAJOR )); then
    return
  fi

  log "installing Node.js ${NODE_MAJOR}.x"
  curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | sudo -E bash -
  sudo apt-get install -y --no-install-recommends nodejs
}

ensure_rosdep_ready() {
  if ! command -v rosdep >/dev/null 2>&1; then
    return
  fi
  sudo rosdep init >/dev/null 2>&1 || true
  rosdep update
}

source_ros_setup() {
  local ros_setup="/opt/ros/${ROS_DISTRO}/setup.bash"
  local had_nounset=0

  [[ -f "$ros_setup" ]] || die "missing ROS setup script: $ros_setup"

  if [[ $- == *u* ]]; then
    had_nounset=1
    set +u
  fi

  export AMENT_TRACE_SETUP_FILES="${AMENT_TRACE_SETUP_FILES:-}"
  # shellcheck disable=SC1090
  source "$ros_setup"

  if (( had_nounset )); then
    set -u
  fi
}

prepare_submodules() {
  log "syncing git submodules"
  git -C "$ROOT_DIR" submodule update --init --recursive
}

create_python_venv() {
  local python_bin

  log "creating Python virtualenv at $VENV_DIR"
  python_bin="$(resolve_system_python_bin)"

  if [[ -n "${VIRTUAL_ENV:-}" ]]; then
    log "active virtualenv detected at $VIRTUAL_ENV; forcing system Python via $python_bin"
  fi

  if [[ -d "$VENV_DIR" ]]; then
    log "resetting existing Python virtualenv at $VENV_DIR"
    rm -rf "$VENV_DIR"
  fi
  "$python_bin" -m venv "$VENV_DIR"
  if ! "$VENV_DIR/bin/python" -m pip --version >/dev/null 2>&1; then
    log "virtualenv created without pip; bootstrapping pip with ensurepip"
    "$VENV_DIR/bin/python" -m ensurepip --upgrade \
      || die "virtualenv bootstrap could not enable pip; confirm python${PYTHON_VERSION}-venv is installed and rerun the bootstrap"
  fi
  "$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel
}

install_python_dependencies() {
  log "installing Python dependencies into $VENV_DIR"
  "$VENV_DIR/bin/python" -m pip install -r "$ROOT_DIR/third_party/PX4-Autopilot/Tools/setup/requirements.txt"
  "$VENV_DIR/bin/python" -m pip install -r "$ROOT_DIR/packages/shared-py/requirements-test.txt"
  "$VENV_DIR/bin/python" -m pip install -r "$ROOT_DIR/packages/shared-py/requirements-phase2.txt"
  "$VENV_DIR/bin/python" -m pip install -r "$ROOT_DIR/packages/shared-py/requirements-phase6.txt"
  "$VENV_DIR/bin/python" -m pip install \
    -e "$ROOT_DIR/packages/shared-py[test]" \
    -e "$ROOT_DIR/services/control-api[test]" \
    -e "$ROOT_DIR/services/telemetry-api[test]"
}

install_dashboard_dependencies() {
  log "installing dashboard npm dependencies"
  npm install --prefix "$ROOT_DIR/apps/dashboard" --no-fund --no-audit
}

xrce_agent_cache_is_complete() {
  [[ -x "$AGENT_INSTALL_DIR/bin/MicroXRCEAgent" ]] || return 1
  [[ -f "$AGENT_INSTALL_DIR/lib/libfastrtps.so.2.14.6" ]] || return 1
  [[ -f "$AGENT_INSTALL_DIR/lib/libfastcdr.so.2.2.7" ]] || return 1
  [[ -f "$AGENT_INSTALL_DIR/lib/libmicroxrcedds_agent.so.2.4.3" ]] || return 1
}

build_micro_xrce_agent_cache() {
  if xrce_agent_cache_is_complete; then
    log "Micro XRCE-DDS Agent cache already present"
    return
  fi

  log "building Micro XRCE-DDS Agent cache ($AGENT_TAG)"
  rm -rf "$AGENT_SRC_DIR" "$AGENT_BUILD_DIR" "$AGENT_INSTALL_DIR"
  mkdir -p "$(dirname "$AGENT_SRC_DIR")"
  git clone --branch "$AGENT_TAG" --depth 1 https://github.com/eProsima/Micro-XRCE-DDS-Agent.git "$AGENT_SRC_DIR"
  cmake \
    -S "$AGENT_SRC_DIR" \
    -B "$AGENT_BUILD_DIR" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$AGENT_INSTALL_DIR"
  cmake --build "$AGENT_BUILD_DIR" --target uagent -j"$(nproc)"
  cmake --install "$AGENT_BUILD_DIR"
}

install_ros_workspace_dependencies() {
  if ! command -v rosdep >/dev/null 2>&1; then
    return
  fi
  log "installing ROS workspace dependencies via rosdep"
  rosdep install \
    --from-paths "$ROOT_DIR/robotics/ros2_ws/src" \
    --ignore-src \
    -r \
    -y \
    --rosdistro "$ROS_DISTRO" \
    --skip-keys "ament_python"
}

build_ros_workspace() {
  log "building ROS 2 workspace"
  source_ros_setup
  cd "$ROOT_DIR/robotics/ros2_ws"
  colcon build --symlink-install --packages-up-to drone_bringup
}

run_smoke_checks() {
  log "running bootstrap smoke checks"
  bash "$ROOT_DIR/scripts/bootstrap/validate-phase-0.sh"
  bash "$ROOT_DIR/robotics/ros2_ws/scripts/validate-workspace.sh"
  PHASE1_PYTHON_BIN="$VENV_DIR/bin/python" bash "$ROOT_DIR/scripts/sim/start.sh" --check >/dev/null
  bash "$ROOT_DIR/scripts/sim/stop.sh" --check >/dev/null
}

print_next_steps() {
  cat <<EOF

Mark 1 bootstrap completed.

Recommended next steps:

1. Terminal 1
   cd "$ROOT_DIR"
   ulimit -n 8192
   source "$VENV_DIR/bin/activate"
   export TELEMETRY_API_DATA_ROOT=/tmp/mark1-telemetry
   telemetry-api

2. Terminal 2
   cd "$ROOT_DIR"
   ulimit -n 8192
   source "$VENV_DIR/bin/activate"
   export TELEMETRY_API_BASE_URL=http://127.0.0.1:8080
   export CONTROL_API_STATE_DIR=/tmp/mark1-control-state
   control-api

3. Terminal 3
   cd "$ROOT_DIR"
   npm --prefix apps/dashboard run dev

4. Terminal 4
   cd "$ROOT_DIR"
   source /opt/ros/${ROS_DISTRO}/setup.bash
   source robotics/ros2_ws/install/setup.bash
   ros2 launch drone_bringup bringup.launch.py enable_mission:=true enable_safety:=true enable_telemetry:=true mission_auto_start:=false

5. Start simulation
   curl -X POST http://127.0.0.1:8090/api/v1/control/simulation/start \\
     -H 'content-type: application/json' \\
     -d '{"input":{"mode":"visual"},"requested_by":{"type":"manual_validation","id":"terminal"}}'

EOF
}

main() {
  require_cmd git
  require_cmd curl
  require_cmd sudo
  assert_ubuntu_jammy
  assert_disk_budget
  install_base_apt_packages
  ensure_deadsnakes_python
  ensure_gazebo_repo
  ensure_ros_repo
  ensure_nodesource_node
  ensure_rosdep_ready
  prepare_submodules
  create_python_venv
  install_python_dependencies
  install_dashboard_dependencies
  build_micro_xrce_agent_cache
  install_ros_workspace_dependencies
  build_ros_workspace
  run_smoke_checks
  print_next_steps
}

main "$@"
