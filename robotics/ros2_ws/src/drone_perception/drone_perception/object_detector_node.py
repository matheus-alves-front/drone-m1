from __future__ import annotations

import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image

from drone_msgs.msg import PerceptionEvent, VisionDetection
from drone_perception.detection import detect_primary_target
from drone_perception.image_ops import ros_image_to_bgr


class ObjectDetectorNode(Node):
    def __init__(self) -> None:
        super().__init__("object_detector")

        self.declare_parameter("input_topic", "/drone/perception/preprocessed_image")
        self.declare_parameter("detection_topic", "/drone/perception/detection")
        self.declare_parameter("event_topic", "/drone/perception/event")
        self.declare_parameter("detection_label", "sim_target")
        self.declare_parameter("min_area_ratio", 0.002)

        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self._detection_publisher = self.create_publisher(
            VisionDetection,
            str(self.get_parameter("detection_topic").value),
            qos,
        )
        self._event_publisher = self.create_publisher(
            PerceptionEvent,
            str(self.get_parameter("event_topic").value),
            qos,
        )
        self._last_detected = False
        self.create_subscription(
            Image,
            str(self.get_parameter("input_topic").value),
            self._handle_image,
            qos,
        )

        self.get_logger().info(
            "object_detector initialized "
            f"(input_topic={self.get_parameter('input_topic').value}, "
            f"detection_topic={self.get_parameter('detection_topic').value})"
        )

    def _handle_image(self, msg: Image) -> None:
        sample = detect_primary_target(
            ros_image_to_bgr(msg),
            label=str(self.get_parameter("detection_label").value),
            min_area_ratio=float(self.get_parameter("min_area_ratio").value),
        )

        detection = VisionDetection()
        detection.stamp = msg.header.stamp
        detection.detected = bool(sample.detected)
        detection.label = sample.label
        detection.confidence = float(sample.confidence)
        detection.center_x = float(sample.center_x)
        detection.center_y = float(sample.center_y)
        detection.width = float(sample.width)
        detection.height = float(sample.height)
        detection.area_ratio = float(sample.area_ratio)
        self._detection_publisher.publish(detection)

        if sample.detected != self._last_detected:
            event = PerceptionEvent()
            event.stamp = self.get_clock().now().to_msg()
            event.event_type = "target_detected" if sample.detected else "target_missing"
            event.track_id = 0
            event.label = sample.label
            event.confidence = float(sample.confidence)
            event.detail = (
                f"area_ratio={sample.area_ratio:.4f}"
                if sample.detected
                else "detector lost target"
            )
            self._event_publisher.publish(event)
            self._last_detected = sample.detected


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = ObjectDetectorNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
