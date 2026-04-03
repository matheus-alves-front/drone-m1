from __future__ import annotations

from drone_msgs.msg import PerceptionEvent, PerceptionHeartbeat, TrackedObject, VisionDetection
import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy

from drone_perception.detection import DetectionSample
from drone_perception.tracking import SingleObjectTracker


class TrackerNode(Node):
    def __init__(self) -> None:
        super().__init__("tracker")

        self.declare_parameter("detection_topic", "/drone/perception/detection")
        self.declare_parameter("tracked_topic", "/drone/perception/tracked_object")
        self.declare_parameter("event_topic", "/drone/perception/event")
        self.declare_parameter("heartbeat_topic", "/drone/perception_heartbeat")
        self.declare_parameter("reacquire_distance_px", 48.0)
        self.declare_parameter("healthy_latency_threshold_s", 0.25)

        detection_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        event_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self._tracker = SingleObjectTracker(
            reacquire_distance_px=float(self.get_parameter("reacquire_distance_px").value),
        )
        self._tracked_publisher = self.create_publisher(
            TrackedObject,
            str(self.get_parameter("tracked_topic").value),
            event_qos,
        )
        self._event_publisher = self.create_publisher(
            PerceptionEvent,
            str(self.get_parameter("event_topic").value),
            event_qos,
        )
        self._heartbeat_publisher = self.create_publisher(
            PerceptionHeartbeat,
            str(self.get_parameter("heartbeat_topic").value),
            event_qos,
        )
        self._last_tracked = False
        self.create_subscription(
            VisionDetection,
            str(self.get_parameter("detection_topic").value),
            self._handle_detection,
            detection_qos,
        )

        self.get_logger().info(
            "tracker initialized "
            f"(detection_topic={self.get_parameter('detection_topic').value}, "
            f"tracked_topic={self.get_parameter('tracked_topic').value})"
        )

    def _handle_detection(self, msg: VisionDetection) -> None:
        now_ns = self.get_clock().now().nanoseconds
        detection_stamp_ns = (int(msg.stamp.sec) * 1_000_000_000) + int(msg.stamp.nanosec)
        latency_s = max(0.0, (now_ns - detection_stamp_ns) / 1_000_000_000.0) if detection_stamp_ns else 0.0

        detection = DetectionSample(
            detected=bool(msg.detected),
            label=msg.label,
            confidence=float(msg.confidence),
            center_x=float(msg.center_x),
            center_y=float(msg.center_y),
            width=float(msg.width),
            height=float(msg.height),
            area_ratio=float(msg.area_ratio),
        )
        tracked_sample = self._tracker.update(detection)

        tracked = TrackedObject()
        tracked.stamp = self.get_clock().now().to_msg()
        tracked.tracked = bool(tracked_sample.tracked)
        tracked.track_id = int(tracked_sample.track_id)
        tracked.label = tracked_sample.label
        tracked.confidence = float(tracked_sample.confidence)
        tracked.center_x = float(tracked_sample.center_x)
        tracked.center_y = float(tracked_sample.center_y)
        tracked.width = float(tracked_sample.width)
        tracked.height = float(tracked_sample.height)
        tracked.age = int(tracked_sample.age)
        tracked.state = tracked_sample.state
        self._tracked_publisher.publish(tracked)

        if tracked_sample.tracked != self._last_tracked:
            event = PerceptionEvent()
            event.stamp = tracked.stamp
            event.event_type = "track_locked" if tracked_sample.tracked else "track_lost"
            event.track_id = int(tracked_sample.track_id)
            event.label = tracked_sample.label
            event.confidence = float(tracked_sample.confidence)
            event.detail = tracked_sample.state
            self._event_publisher.publish(event)
            self._last_tracked = tracked_sample.tracked

        heartbeat = PerceptionHeartbeat()
        heartbeat.stamp = self.get_clock().now().to_msg()
        heartbeat.healthy = latency_s <= float(self.get_parameter("healthy_latency_threshold_s").value)
        heartbeat.pipeline_latency_s = float(latency_s)
        self._heartbeat_publisher.publish(heartbeat)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = TrackerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
