#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$ROOT_DIR/../.." && pwd)"
TEST_PYTHON_BIN="${TEST_PYTHON_BIN:-python3}"

ensure_pytest() {
  local venv_dir="$REPO_ROOT/.cache/pytest-venv"
  if [[ ! -x "$venv_dir/bin/python" ]]; then
    python3 -m venv "$venv_dir"
  fi
  if ! "$venv_dir/bin/python" -m pip --version >/dev/null 2>&1; then
    "$venv_dir/bin/python" -m ensurepip --upgrade >/dev/null 2>&1
  fi
  if ! "$venv_dir/bin/python" -m pytest --version >/dev/null 2>&1; then
    "$venv_dir/bin/python" -m pip install --quiet -r "$REPO_ROOT/packages/shared-py/requirements-test.txt"
  fi
  if ! "$venv_dir/bin/python" -c 'import cv2, numpy' >/dev/null 2>&1; then
    "$venv_dir/bin/python" -m pip install --quiet -r "$REPO_ROOT/packages/shared-py/requirements-phase6.txt"
  fi
  TEST_PYTHON_BIN="$venv_dir/bin/python"
}

ensure_pytest

required_paths=(
  "$ROOT_DIR/README.md"
  "$ROOT_DIR/src/drone_bringup/package.xml"
  "$ROOT_DIR/src/drone_bringup/setup.py"
  "$ROOT_DIR/src/drone_bringup/setup.cfg"
  "$ROOT_DIR/src/drone_bringup/config/drone_px4.yaml"
  "$ROOT_DIR/src/drone_bringup/config/drone_mission.yaml"
  "$ROOT_DIR/src/drone_bringup/config/drone_perception.yaml"
  "$ROOT_DIR/src/drone_bringup/config/drone_safety.yaml"
  "$ROOT_DIR/src/drone_bringup/drone_bringup/__init__.py"
  "$ROOT_DIR/src/drone_bringup/drone_bringup/launch/bringup.launch.py"
  "$ROOT_DIR/src/drone_bringup/test/test_package.py"
  "$ROOT_DIR/src/drone_msgs/package.xml"
  "$ROOT_DIR/src/drone_msgs/CMakeLists.txt"
  "$ROOT_DIR/src/drone_msgs/msg/MissionCommand.msg"
  "$ROOT_DIR/src/drone_msgs/msg/MissionStatus.msg"
  "$ROOT_DIR/src/drone_msgs/msg/PerceptionHeartbeat.msg"
  "$ROOT_DIR/src/drone_msgs/msg/SafetyFault.msg"
  "$ROOT_DIR/src/drone_msgs/msg/SafetyStatus.msg"
  "$ROOT_DIR/src/drone_msgs/msg/VehicleCommand.msg"
  "$ROOT_DIR/src/drone_msgs/msg/VehicleCommandStatus.msg"
  "$ROOT_DIR/src/drone_msgs/msg/VehicleState.msg"
  "$ROOT_DIR/src/drone_msgs/msg/README.md"
  "$ROOT_DIR/src/drone_mission/package.xml"
  "$ROOT_DIR/src/drone_mission/setup.py"
  "$ROOT_DIR/src/drone_mission/setup.cfg"
  "$ROOT_DIR/src/drone_mission/resource/drone_mission"
  "$ROOT_DIR/src/drone_mission/drone_mission/__init__.py"
  "$ROOT_DIR/src/drone_mission/drone_mission/contracts.py"
  "$ROOT_DIR/src/drone_mission/drone_mission/errors.py"
  "$ROOT_DIR/src/drone_mission/drone_mission/fake_gateway.py"
  "$ROOT_DIR/src/drone_mission/drone_mission/gateway.py"
  "$ROOT_DIR/src/drone_mission/drone_mission/geodesy.py"
  "$ROOT_DIR/src/drone_mission/drone_mission/loader.py"
  "$ROOT_DIR/src/drone_mission/drone_mission/mission_executor.py"
  "$ROOT_DIR/src/drone_mission/drone_mission/mission_manager_node.py"
  "$ROOT_DIR/src/drone_mission/drone_mission/mission_state_machine.py"
  "$ROOT_DIR/src/drone_mission/test/test_loader.py"
  "$ROOT_DIR/src/drone_mission/test/test_mission_executor.py"
  "$ROOT_DIR/src/drone_mission/test/test_mission_state_machine.py"
  "$ROOT_DIR/src/drone_mission/test/test_ros2_gateway.py"
  "$ROOT_DIR/src/drone_px4/package.xml"
  "$ROOT_DIR/src/drone_px4/setup.py"
  "$ROOT_DIR/src/drone_px4/setup.cfg"
  "$ROOT_DIR/src/drone_px4/resource/drone_px4"
  "$ROOT_DIR/src/drone_px4/drone_px4/__init__.py"
  "$ROOT_DIR/src/drone_px4/drone_px4/state_model.py"
  "$ROOT_DIR/src/drone_px4/drone_px4/px4_bridge_node.py"
  "$ROOT_DIR/src/drone_px4/test/test_state_model.py"
  "$ROOT_DIR/src/drone_safety/package.xml"
  "$ROOT_DIR/src/drone_safety/setup.py"
  "$ROOT_DIR/src/drone_safety/setup.cfg"
  "$ROOT_DIR/src/drone_safety/resource/drone_safety"
  "$ROOT_DIR/src/drone_safety/drone_safety/__init__.py"
  "$ROOT_DIR/src/drone_safety/drone_safety/contracts.py"
  "$ROOT_DIR/src/drone_safety/drone_safety/rules.py"
  "$ROOT_DIR/src/drone_safety/drone_safety/safety_manager_node.py"
  "$ROOT_DIR/src/drone_safety/test/test_rules.py"
  "$ROOT_DIR/src/drone_perception/package.xml"
  "$ROOT_DIR/src/drone_perception/setup.py"
  "$ROOT_DIR/src/drone_perception/setup.cfg"
  "$ROOT_DIR/src/drone_perception/resource/drone_perception"
  "$ROOT_DIR/src/drone_perception/drone_perception/__init__.py"
  "$ROOT_DIR/src/drone_perception/drone_perception/image_ops.py"
  "$ROOT_DIR/src/drone_perception/drone_perception/detection.py"
  "$ROOT_DIR/src/drone_perception/drone_perception/tracking.py"
  "$ROOT_DIR/src/drone_perception/drone_perception/camera_input_node.py"
  "$ROOT_DIR/src/drone_perception/drone_perception/object_detector_node.py"
  "$ROOT_DIR/src/drone_perception/drone_perception/tracker_node.py"
  "$ROOT_DIR/src/drone_perception/drone_perception/frame_generator.py"
  "$ROOT_DIR/src/drone_perception/README.md"
  "$ROOT_DIR/src/drone_perception/test/test_detector.py"
  "$ROOT_DIR/src/drone_perception/test/test_frame_generator.py"
  "$ROOT_DIR/src/drone_perception/test/test_image_ops.py"
  "$ROOT_DIR/src/drone_perception/test/test_tracker.py"
  "$ROOT_DIR/src/drone_telemetry/package.xml"
  "$ROOT_DIR/src/drone_telemetry/setup.py"
  "$ROOT_DIR/src/drone_telemetry/setup.cfg"
  "$ROOT_DIR/src/drone_telemetry/resource/drone_telemetry"
  "$ROOT_DIR/src/drone_telemetry/drone_telemetry/__init__.py"
  "$ROOT_DIR/src/drone_telemetry/drone_telemetry/contracts.py"
  "$ROOT_DIR/src/drone_telemetry/drone_telemetry/serializers.py"
  "$ROOT_DIR/src/drone_telemetry/drone_telemetry/transport.py"
  "$ROOT_DIR/src/drone_telemetry/drone_telemetry/telemetry_bridge_node.py"
  "$ROOT_DIR/src/drone_telemetry/test/test_serializers.py"
  "$ROOT_DIR/src/drone_telemetry/test/test_transport.py"
  "$ROOT_DIR/scripts/build-phase-3-container-image.sh"
  "$ROOT_DIR/scripts/validate-phase-3-container.sh"
  "$ROOT_DIR/scripts/validate-phase-4.sh"
  "$ROOT_DIR/scripts/validate-phase-4-container.sh"
  "$ROOT_DIR/scripts/validate-phase-5.sh"
  "$ROOT_DIR/scripts/validate-phase-5-container.sh"
  "$ROOT_DIR/scripts/validate-phase-6.sh"
  "$ROOT_DIR/scripts/validate-phase-6-container.sh"
  "$ROOT_DIR/scripts/validate-phase-7.sh"
  "$ROOT_DIR/scripts/publish_sim_camera_stream.py"
  "$ROOT_DIR/scripts/wait_for_perception_heartbeat.py"
  "$ROOT_DIR/scripts/wait_for_vision_detection.py"
  "$ROOT_DIR/scripts/wait_for_tracked_object.py"
  "$ROOT_DIR/scripts/wait_for_perception_event.py"
  "$REPO_ROOT/scripts/sim/configure_px4_sim_params.py"
  "$ROOT_DIR/scripts/wait_for_mission_status.py"
  "$ROOT_DIR/scripts/wait_for_command_status.py"
  "$ROOT_DIR/scripts/wait_for_safety_status.py"
  "$ROOT_DIR/scripts/wait_for_vehicle_state.py"
  "$ROOT_DIR/src/px4_msgs/README.md"
  "$ROOT_DIR/src/px4_msgs/PINNING.md"
  "$ROOT_DIR/src/px4_msgs/package.xml"
  "$ROOT_DIR/src/px4_msgs/CMakeLists.txt"
  "$ROOT_DIR/src/px4_msgs/msg/VehicleStatus.msg"
  "$ROOT_DIR/src/px4_msgs/msg/VehicleLocalPosition.msg"
  "$ROOT_DIR/src/px4_msgs/msg/VehicleGlobalPosition.msg"
  "$ROOT_DIR/src/px4_msgs/msg/VehicleLandDetected.msg"
  "$ROOT_DIR/src/px4_msgs/msg/GotoSetpoint.msg"
  "$ROOT_DIR/src/px4_msgs/msg/VehicleCommand.msg"
  "$ROOT_DIR/src/px4_msgs/msg/VehicleCommandAck.msg"
  "$ROOT_DIR/src/px4_msgs/srv/VehicleCommand.srv"
)

for path in "${required_paths[@]}"; do
  if [[ ! -e "$path" ]]; then
    echo "missing required workspace artifact: $path" >&2
    exit 1
  fi
done

find "$ROOT_DIR/src" -type d -name "__pycache__" -prune -exec rm -rf {} +

python3 -m py_compile \
  "$ROOT_DIR/src/drone_bringup/drone_bringup/launch/bringup.launch.py" \
  "$ROOT_DIR/src/drone_bringup/test/test_package.py" \
  "$ROOT_DIR/src/drone_mission/drone_mission/contracts.py" \
  "$ROOT_DIR/src/drone_mission/drone_mission/errors.py" \
  "$ROOT_DIR/src/drone_mission/drone_mission/fake_gateway.py" \
  "$ROOT_DIR/src/drone_mission/drone_mission/gateway.py" \
  "$ROOT_DIR/src/drone_px4/drone_px4/state_model.py" \
  "$ROOT_DIR/src/drone_px4/drone_px4/px4_bridge_node.py" \
  "$ROOT_DIR/src/drone_px4/test/test_state_model.py" \
  "$ROOT_DIR/src/drone_safety/drone_safety/contracts.py" \
  "$ROOT_DIR/src/drone_safety/drone_safety/rules.py" \
  "$ROOT_DIR/src/drone_safety/drone_safety/safety_manager_node.py" \
  "$ROOT_DIR/src/drone_safety/test/test_rules.py" \
  "$ROOT_DIR/src/drone_perception/drone_perception/image_ops.py" \
  "$ROOT_DIR/src/drone_perception/drone_perception/detection.py" \
  "$ROOT_DIR/src/drone_perception/drone_perception/tracking.py" \
  "$ROOT_DIR/src/drone_perception/drone_perception/camera_input_node.py" \
  "$ROOT_DIR/src/drone_perception/drone_perception/object_detector_node.py" \
  "$ROOT_DIR/src/drone_perception/drone_perception/tracker_node.py" \
  "$ROOT_DIR/src/drone_perception/drone_perception/frame_generator.py" \
  "$ROOT_DIR/src/drone_perception/test/test_detector.py" \
  "$ROOT_DIR/src/drone_perception/test/test_frame_generator.py" \
  "$ROOT_DIR/src/drone_perception/test/test_image_ops.py" \
  "$ROOT_DIR/src/drone_perception/test/test_tracker.py" \
  "$ROOT_DIR/src/drone_telemetry/drone_telemetry/contracts.py" \
  "$ROOT_DIR/src/drone_telemetry/drone_telemetry/serializers.py" \
  "$ROOT_DIR/src/drone_telemetry/drone_telemetry/transport.py" \
  "$ROOT_DIR/src/drone_telemetry/drone_telemetry/telemetry_bridge_node.py" \
  "$ROOT_DIR/src/drone_telemetry/test/test_serializers.py" \
  "$ROOT_DIR/src/drone_telemetry/test/test_transport.py" \
  "$ROOT_DIR/src/drone_mission/drone_mission/geodesy.py" \
  "$ROOT_DIR/src/drone_mission/drone_mission/loader.py" \
  "$ROOT_DIR/src/drone_mission/drone_mission/mission_executor.py" \
  "$ROOT_DIR/src/drone_mission/drone_mission/mission_manager_node.py" \
  "$ROOT_DIR/src/drone_mission/drone_mission/mission_state_machine.py" \
  "$ROOT_DIR/src/drone_mission/test/test_loader.py" \
  "$ROOT_DIR/src/drone_mission/test/test_mission_executor.py" \
  "$ROOT_DIR/src/drone_mission/test/test_mission_state_machine.py" \
  "$ROOT_DIR/src/drone_mission/test/test_ros2_gateway.py" \
  "$REPO_ROOT/scripts/sim/configure_px4_sim_params.py" \
  "$ROOT_DIR/scripts/publish_sim_camera_stream.py" \
  "$ROOT_DIR/scripts/wait_for_mission_status.py" \
  "$ROOT_DIR/scripts/wait_for_command_status.py" \
  "$ROOT_DIR/scripts/wait_for_perception_heartbeat.py" \
  "$ROOT_DIR/scripts/wait_for_vision_detection.py" \
  "$ROOT_DIR/scripts/wait_for_tracked_object.py" \
  "$ROOT_DIR/scripts/wait_for_perception_event.py" \
  "$ROOT_DIR/scripts/wait_for_safety_status.py" \
  "$ROOT_DIR/scripts/wait_for_vehicle_state.py"

bash -n "$ROOT_DIR/scripts/build-phase-3-container-image.sh"
bash -n "$ROOT_DIR/scripts/validate-phase-3-container.sh"
bash -n "$ROOT_DIR/scripts/validate-phase-4.sh"
bash -n "$ROOT_DIR/scripts/validate-phase-4-container.sh"
bash -n "$ROOT_DIR/scripts/validate-phase-5.sh"
bash -n "$ROOT_DIR/scripts/validate-phase-5-container.sh"
bash -n "$ROOT_DIR/scripts/validate-phase-6.sh"
bash -n "$ROOT_DIR/scripts/validate-phase-6-container.sh"
bash -n "$ROOT_DIR/scripts/validate-phase-7.sh"

PYTHONPATH="$ROOT_DIR/src/drone_bringup:$ROOT_DIR/src/drone_px4" \
  python3 -m unittest \
    "$ROOT_DIR/src/drone_bringup/test/test_package.py"

PYTHONPATH="$ROOT_DIR/src/drone_px4" python3 -m unittest discover \
  -s "$ROOT_DIR/src/drone_px4/test" \
  -p "test_*.py"

PYTHONPATH="$ROOT_DIR/src/drone_safety" python3 -m unittest discover \
  -s "$ROOT_DIR/src/drone_safety/test" \
  -p "test_*.py"

PYTHONPATH="$ROOT_DIR/src/drone_perception" "$TEST_PYTHON_BIN" -m pytest \
  "$ROOT_DIR/src/drone_perception/test" -q

PYTHONPATH="$ROOT_DIR/src/drone_telemetry" python3 -m unittest discover \
  -s "$ROOT_DIR/src/drone_telemetry/test" \
  -p "test_*.py"

PYTHONPATH="$ROOT_DIR/src/drone_mission" "$TEST_PYTHON_BIN" -m pytest \
  "$ROOT_DIR/src/drone_mission/test" -q

if ! grep -q 'release/1.16' "$ROOT_DIR/src/px4_msgs/PINNING.md"; then
  echo "px4_msgs pinning manifesto does not reference release/1.16" >&2
  exit 1
fi

if ! grep -q 'v1.16.1' "$ROOT_DIR/src/px4_msgs/PINNING.md"; then
  echo "px4_msgs pinning manifesto does not reference PX4 v1.16.1" >&2
  exit 1
fi

if ! grep -q 'VehicleState.msg' "$ROOT_DIR/src/drone_msgs/CMakeLists.txt"; then
  echo "drone_msgs does not generate VehicleState.msg" >&2
  exit 1
fi

if ! grep -q 'MissionCommand.msg' "$ROOT_DIR/src/drone_msgs/CMakeLists.txt"; then
  echo "drone_msgs does not generate MissionCommand.msg" >&2
  exit 1
fi

if ! grep -q 'MissionStatus.msg' "$ROOT_DIR/src/drone_msgs/CMakeLists.txt"; then
  echo "drone_msgs does not generate MissionStatus.msg" >&2
  exit 1
fi

for safety_msg in \
  'PerceptionHeartbeat.msg' \
  'PerceptionEvent.msg' \
  'SafetyFault.msg' \
  'SafetyStatus.msg' \
  'TrackedObject.msg' \
  'VisionDetection.msg'; do
  if ! grep -q "$safety_msg" "$ROOT_DIR/src/drone_msgs/CMakeLists.txt"; then
    echo "drone_msgs does not generate $safety_msg" >&2
    exit 1
  fi
done

for mission_status_field in \
  'bool terminal' \
  'bool succeeded' \
  'string last_command'; do
  if ! grep -q "$mission_status_field" "$ROOT_DIR/src/drone_msgs/msg/MissionStatus.msg"; then
    echo "MissionStatus.msg is missing required Phase 4 field: $mission_status_field" >&2
    exit 1
  fi
done

if ! grep -q 'VehicleCommand.msg' "$ROOT_DIR/src/drone_msgs/CMakeLists.txt"; then
  echo "drone_msgs does not generate VehicleCommand.msg" >&2
  exit 1
fi

if ! grep -q 'VehicleCommandStatus.msg' "$ROOT_DIR/src/drone_msgs/CMakeLists.txt"; then
  echo "drone_msgs does not generate VehicleCommandStatus.msg" >&2
  exit 1
fi

if ! grep -q 'px4_bridge_node' "$ROOT_DIR/src/drone_px4/setup.py"; then
  echo "drone_px4 does not expose px4_bridge_node entrypoint" >&2
  exit 1
fi

if ! grep -q 'mission_manager_node' "$ROOT_DIR/src/drone_mission/setup.py"; then
  echo "drone_mission does not expose mission_manager_node entrypoint" >&2
  exit 1
fi

if ! grep -q 'safety_manager_node' "$ROOT_DIR/src/drone_safety/setup.py"; then
  echo "drone_safety does not expose safety_manager_node entrypoint" >&2
  exit 1
fi

for perception_entrypoint in \
  'camera_input_node' \
  'object_detector_node' \
  'tracker_node'; do
  if ! grep -q "$perception_entrypoint" "$ROOT_DIR/src/drone_perception/setup.py"; then
    echo "drone_perception does not expose $perception_entrypoint entrypoint" >&2
    exit 1
  fi
done

if ! grep -q '/fmu/out/vehicle_status' "$ROOT_DIR/src/drone_bringup/config/drone_px4.yaml"; then
  echo "drone_bringup params do not reference the real PX4 vehicle status topic" >&2
  exit 1
fi

if ! grep -q '/fmu/in/vehicle_command' "$ROOT_DIR/src/drone_bringup/config/drone_px4.yaml"; then
  echo "drone_bringup params do not reference the real PX4 vehicle command topic" >&2
  exit 1
fi

if ! grep -q '/fmu/out/vehicle_control_mode' "$ROOT_DIR/src/drone_bringup/config/drone_px4.yaml"; then
  echo "drone_bringup params do not reference the real PX4 vehicle control mode topic" >&2
  exit 1
fi

if ! grep -q '/drone/mission_status' "$ROOT_DIR/src/drone_bringup/config/drone_mission.yaml"; then
  echo "drone_mission params do not reference the mission status topic" >&2
  exit 1
fi

if ! grep -q '/drone/safety_status' "$ROOT_DIR/src/drone_bringup/config/drone_safety.yaml"; then
  echo "drone_safety params do not reference the safety status topic" >&2
  exit 1
fi

if ! grep -q '/drone/safety_fault' "$ROOT_DIR/src/drone_bringup/config/drone_safety.yaml"; then
  echo "drone_safety params do not reference the safety fault topic" >&2
  exit 1
fi

for perception_topic in \
  '/simulation/camera/image_raw' \
  '/drone/perception/preprocessed_image' \
  '/drone/perception_heartbeat' \
  '/drone/perception/detection' \
  '/drone/perception/tracked_object' \
  '/drone/perception/event'; do
  if ! grep -q "$perception_topic" "$ROOT_DIR/src/drone_bringup/config/drone_perception.yaml"; then
    echo "drone_perception params do not reference $perception_topic" >&2
    exit 1
  fi
done

if ! grep -q 'backend: ros2_domain' "$ROOT_DIR/src/drone_bringup/config/drone_mission.yaml"; then
  echo "drone_mission params do not pin the ROS 2 domain mission backend" >&2
  exit 1
fi

if ! grep -q 'enable_mission' "$ROOT_DIR/src/drone_bringup/drone_bringup/launch/bringup.launch.py"; then
  echo "bringup launch does not expose optional mission node startup" >&2
  exit 1
fi

if ! grep -q 'mission_auto_start' "$ROOT_DIR/src/drone_bringup/drone_bringup/launch/bringup.launch.py"; then
  echo "bringup launch does not expose mission auto-start" >&2
  exit 1
fi

if ! grep -q 'enable_safety' "$ROOT_DIR/src/drone_bringup/drone_bringup/launch/bringup.launch.py"; then
  echo "bringup launch does not expose optional safety node startup" >&2
  exit 1
fi

if ! grep -q 'enable_perception' "$ROOT_DIR/src/drone_bringup/drone_bringup/launch/bringup.launch.py"; then
  echo "bringup launch does not expose optional perception node startup" >&2
  exit 1
fi

if ! grep -q 'enable_telemetry' "$ROOT_DIR/src/drone_bringup/drone_bringup/launch/bringup.launch.py"; then
  echo "bringup launch does not expose optional telemetry node startup" >&2
  exit 1
fi

if ! grep -q 'telemetry_bridge_node' "$ROOT_DIR/src/drone_telemetry/setup.py"; then
  echo "drone_telemetry does not expose telemetry_bridge_node entrypoint" >&2
  exit 1
fi

for telemetry_topic in \
  '/drone/vehicle_state' \
  '/drone/vehicle_command_status' \
  '/drone/mission_status' \
  '/drone/safety_status' \
  '/drone/perception/tracked_object' \
  '/drone/perception_heartbeat' \
  '/drone/perception/event'; do
  if ! grep -q "$telemetry_topic" "$ROOT_DIR/src/drone_bringup/config/drone_telemetry.yaml"; then
    echo "drone_telemetry params do not reference $telemetry_topic" >&2
    exit 1
  fi
done

if [[ ! -f "$ROOT_DIR/../../simulation/scenarios/patrol_basic.json" ]]; then
  echo "phase-4 mission contract patrol_basic.json is missing" >&2
  exit 1
fi

if [[ ! -f "$ROOT_DIR/../../simulation/scenarios/perception_target_tracking.json" ]]; then
  echo "phase-6 perception scenario perception_target_tracking.json is missing" >&2
  exit 1
fi

echo "workspace structural validation passed"
