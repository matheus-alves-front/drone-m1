from __future__ import annotations

from functools import partial

from drone_msgs.msg import (
    MissionStatus,
    PerceptionEvent,
    PerceptionHeartbeat,
    SafetyStatus,
    TrackedObject,
    VehicleCommandStatus,
    VehicleState,
)
import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy

from .serializers import (
    build_envelope,
    serialize_command_status,
    serialize_mission_status,
    serialize_perception_event,
    serialize_perception_heartbeat,
    serialize_safety_status,
    serialize_tracked_object,
    serialize_vehicle_state,
)
from .transport import AsyncTelemetryPublisher, TelemetryApiClient


class TelemetryBridgeNode(Node):
    def __init__(self) -> None:
        super().__init__("telemetry_bridge")

        self.declare_parameter("api_base_url", "http://127.0.0.1:8080")
        self.declare_parameter("api_timeout_s", 1.0)
        self.declare_parameter("run_id", "phase7-default")
        self.declare_parameter("session_id", "")
        self.declare_parameter("source", "telemetry_bridge_node")
        self.declare_parameter("vehicle_state_topic", "/drone/vehicle_state")
        self.declare_parameter("vehicle_command_status_topic", "/drone/vehicle_command_status")
        self.declare_parameter("mission_status_topic", "/drone/mission_status")
        self.declare_parameter("safety_status_topic", "/drone/safety_status")
        self.declare_parameter("tracked_object_topic", "/drone/perception/tracked_object")
        self.declare_parameter("perception_heartbeat_topic", "/drone/perception_heartbeat")
        self.declare_parameter("perception_event_topic", "/drone/perception/event")

        self._run_id = str(self.get_parameter("run_id").value)
        session_id = str(self.get_parameter("session_id").value).strip()
        self._session_id = session_id or None
        self._source = str(self.get_parameter("source").value)
        client = TelemetryApiClient(
            str(self.get_parameter("api_base_url").value),
            timeout_s=float(self.get_parameter("api_timeout_s").value),
        )
        self._publisher = AsyncTelemetryPublisher(client)

        state_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        stream_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=20,
        )

        subscriptions = [
            (VehicleState, str(self.get_parameter("vehicle_state_topic").value), "vehicle_state", serialize_vehicle_state, state_qos),
            (
                VehicleCommandStatus,
                str(self.get_parameter("vehicle_command_status_topic").value),
                "vehicle_command_status",
                serialize_command_status,
                state_qos,
            ),
            (MissionStatus, str(self.get_parameter("mission_status_topic").value), "mission_status", serialize_mission_status, state_qos),
            (SafetyStatus, str(self.get_parameter("safety_status_topic").value), "safety_status", serialize_safety_status, state_qos),
            (
                TrackedObject,
                str(self.get_parameter("tracked_object_topic").value),
                "tracked_object",
                serialize_tracked_object,
                stream_qos,
            ),
            (
                PerceptionHeartbeat,
                str(self.get_parameter("perception_heartbeat_topic").value),
                "perception_heartbeat",
                serialize_perception_heartbeat,
                state_qos,
            ),
            (
                PerceptionEvent,
                str(self.get_parameter("perception_event_topic").value),
                "perception_event",
                serialize_perception_event,
                stream_qos,
            ),
        ]

        self._subscriptions = []
        for msg_type, topic, kind, serializer, qos in subscriptions:
            self._subscriptions.append(
                self.create_subscription(
                    msg_type,
                    topic,
                    partial(self._forward_message, kind=kind, topic=topic, serializer=serializer),
                    qos,
                )
            )

        self.create_timer(2.0, self._report_transport_health)
        self.get_logger().info(
            "telemetry_bridge initialized "
            f"(api_base_url={self.get_parameter('api_base_url').value}, run_id={self._run_id})"
        )

    def _forward_message(self, msg, *, kind: str, topic: str, serializer) -> None:
        envelope = build_envelope(
            run_id=self._run_id,
            session_id=self._session_id,
            source=self._source,
            kind=kind,
            topic=topic,
            stamp=msg.stamp,
            payload=serializer(msg),
        )
        self._publisher.submit(envelope)

    def _report_transport_health(self) -> None:
        if self._publisher.last_error:
            self.get_logger().warning(f"telemetry bridge transport warning: {self._publisher.last_error}")

    def destroy_node(self) -> bool:
        self._publisher.close()
        return super().destroy_node()


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = TelemetryBridgeNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
