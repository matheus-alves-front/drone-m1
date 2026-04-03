#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
WORKSPACE_DIR="$ROOT_DIR/robotics/ros2_ws"

bash "$WORKSPACE_DIR/scripts/validate-workspace.sh"

python3 -m py_compile \
  "$WORKSPACE_DIR/src/drone_perception/drone_perception/image_ops.py" \
  "$WORKSPACE_DIR/src/drone_perception/drone_perception/detection.py" \
  "$WORKSPACE_DIR/src/drone_perception/drone_perception/tracking.py" \
  "$WORKSPACE_DIR/src/drone_perception/drone_perception/camera_input_node.py" \
  "$WORKSPACE_DIR/src/drone_perception/drone_perception/object_detector_node.py" \
  "$WORKSPACE_DIR/src/drone_perception/drone_perception/tracker_node.py" \
  "$WORKSPACE_DIR/src/drone_perception/test/test_image_ops.py" \
  "$WORKSPACE_DIR/src/drone_perception/test/test_detection.py" \
  "$WORKSPACE_DIR/src/drone_perception/test/test_detector.py" \
  "$WORKSPACE_DIR/src/drone_perception/test/test_frame_generator.py" \
  "$WORKSPACE_DIR/src/drone_perception/test/test_tracker.py" \
  "$WORKSPACE_DIR/src/drone_perception/test/test_tracking.py" \
  "$WORKSPACE_DIR/scripts/publish_sim_camera_stream.py" \
  "$WORKSPACE_DIR/scripts/wait_for_perception_heartbeat.py" \
  "$WORKSPACE_DIR/scripts/wait_for_vision_detection.py" \
  "$WORKSPACE_DIR/scripts/wait_for_tracked_object.py" \
  "$WORKSPACE_DIR/scripts/wait_for_perception_event.py"

rg -n "camera|detector|tracker|opencv|event|heartbeat|perception" \
  "$WORKSPACE_DIR/src/drone_perception" \
  "$WORKSPACE_DIR/src/drone_bringup" \
  "$WORKSPACE_DIR/src/drone_msgs" >/dev/null

test -f "$ROOT_DIR/simulation/scenarios/perception_target_tracking.json"
test -f "$ROOT_DIR/simulation/scenarios/perception_target_tracking.md"

echo "phase-6 local validation passed"
