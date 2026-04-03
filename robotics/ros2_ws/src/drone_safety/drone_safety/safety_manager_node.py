from __future__ import annotations

import time
from dataclasses import dataclass

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy

from drone_msgs.msg import (
    MissionCommand,
    MissionStatus,
    PerceptionHeartbeat,
    SafetyFault,
    SafetyStatus,
    VehicleCommand,
    VehicleState,
)

from drone_safety.contracts import SafetyConfig, SafetySignals
from drone_safety.rules import evaluate_safety, horizontal_distance_m


@dataclass
class FaultState:
    active: bool
    value: float
    detail: str
    updated_monotonic_s: float


class SafetyManagerNode(Node):
    def __init__(self) -> None:
        super().__init__("safety_manager")

        self.declare_parameter("state_topic", "/drone/vehicle_state")
        self.declare_parameter("mission_status_topic", "/drone/mission_status")
        self.declare_parameter("mission_command_topic", "/drone/mission_command")
        self.declare_parameter("vehicle_command_topic", "/drone/vehicle_command")
        self.declare_parameter("safety_fault_topic", "/drone/safety_fault")
        self.declare_parameter("safety_status_topic", "/drone/safety_status")
        self.declare_parameter("perception_heartbeat_topic", "/drone/perception_heartbeat")
        self.declare_parameter("publish_rate_hz", 5.0)
        self.declare_parameter("geofence_enabled", True)
        self.declare_parameter("geofence_max_distance_m", 12.0)
        self.declare_parameter("geofence_max_altitude_m", 8.0)
        self.declare_parameter("gps_loss_timeout_s", 1.5)
        self.declare_parameter("require_perception_heartbeat", False)
        self.declare_parameter("perception_timeout_s", 2.0)
        self.declare_parameter("perception_max_latency_s", 0.5)
        self.declare_parameter("geofence_action", "return_to_home")
        self.declare_parameter("gps_loss_action", "land")
        self.declare_parameter("rc_loss_action", "return_to_home")
        self.declare_parameter("data_link_loss_action", "return_to_home")
        self.declare_parameter("perception_timeout_action", "land")
        self.declare_parameter("perception_latency_action", "land")

        self._config = SafetyConfig(
            geofence_enabled=bool(self.get_parameter("geofence_enabled").value),
            geofence_max_distance_m=float(self.get_parameter("geofence_max_distance_m").value),
            geofence_max_altitude_m=float(self.get_parameter("geofence_max_altitude_m").value),
            gps_loss_timeout_s=float(self.get_parameter("gps_loss_timeout_s").value),
            require_perception_heartbeat=bool(self.get_parameter("require_perception_heartbeat").value),
            perception_timeout_s=float(self.get_parameter("perception_timeout_s").value),
            perception_max_latency_s=float(self.get_parameter("perception_max_latency_s").value),
            geofence_action=str(self.get_parameter("geofence_action").value),
            gps_loss_action=str(self.get_parameter("gps_loss_action").value),
            rc_loss_action=str(self.get_parameter("rc_loss_action").value),
            data_link_loss_action=str(self.get_parameter("data_link_loss_action").value),
            perception_timeout_action=str(self.get_parameter("perception_timeout_action").value),
            perception_latency_action=str(self.get_parameter("perception_latency_action").value),
        )

        self._latest_vehicle_state: VehicleState | None = None
        self._latest_mission_status: MissionStatus | None = None
        self._faults: dict[str, FaultState] = {}
        self._last_perception_heartbeat_monotonic_s: float | None = None
        self._last_perception_latency_s: float = 0.0
        self._last_perception_healthy = True
        self._position_invalid_since_monotonic_s: float | None = None
        self._home_latitude_deg: float | None = None
        self._home_longitude_deg: float | None = None
        self._last_active_signature: tuple[str, str, str] | None = None
        self._trigger_count = 0

        status_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        domain_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )

        self._status_publisher = self.create_publisher(
            SafetyStatus,
            str(self.get_parameter("safety_status_topic").value),
            status_qos,
        )
        self._mission_command_publisher = self.create_publisher(
            MissionCommand,
            str(self.get_parameter("mission_command_topic").value),
            domain_qos,
        )
        self._vehicle_command_publisher = self.create_publisher(
            VehicleCommand,
            str(self.get_parameter("vehicle_command_topic").value),
            domain_qos,
        )

        self.create_subscription(
            VehicleState,
            str(self.get_parameter("state_topic").value),
            self._handle_vehicle_state,
            domain_qos,
        )
        self.create_subscription(
            MissionStatus,
            str(self.get_parameter("mission_status_topic").value),
            self._handle_mission_status,
            status_qos,
        )
        self.create_subscription(
            SafetyFault,
            str(self.get_parameter("safety_fault_topic").value),
            self._handle_safety_fault,
            domain_qos,
        )
        self.create_subscription(
            PerceptionHeartbeat,
            str(self.get_parameter("perception_heartbeat_topic").value),
            self._handle_perception_heartbeat,
            domain_qos,
        )

        publish_rate_hz = max(float(self.get_parameter("publish_rate_hz").value), 1.0)
        self.create_timer(1.0 / publish_rate_hz, self._evaluate_safety)

        self.get_logger().info(
            "safety_manager initialized "
            f"(geofence_enabled={self._config.geofence_enabled}, "
            f"geofence_max_distance_m={self._config.geofence_max_distance_m}, "
            f"gps_loss_timeout_s={self._config.gps_loss_timeout_s})",
        )

    def _handle_vehicle_state(self, msg: VehicleState) -> None:
        self._latest_vehicle_state = msg
        now = time.monotonic()

        if bool(msg.connected) and bool(msg.position_valid):
            self._position_invalid_since_monotonic_s = None
            if self._home_latitude_deg is None or (not bool(msg.armed) and bool(msg.landed)):
                self._home_latitude_deg = float(msg.latitude_deg)
                self._home_longitude_deg = float(msg.longitude_deg)
        elif bool(msg.connected) and self._position_invalid_since_monotonic_s is None:
            self._position_invalid_since_monotonic_s = now

        if not bool(msg.connected):
            self._home_latitude_deg = None
            self._home_longitude_deg = None
            self._position_invalid_since_monotonic_s = None

    def _handle_mission_status(self, msg: MissionStatus) -> None:
        self._latest_mission_status = msg

    def _handle_safety_fault(self, msg: SafetyFault) -> None:
        fault_type = msg.fault_type.strip().lower()
        if not fault_type:
            return

        if bool(msg.active):
            self._faults[fault_type] = FaultState(
                active=True,
                value=float(msg.value),
                detail=msg.detail,
                updated_monotonic_s=time.monotonic(),
            )
            self.get_logger().warning(f"safety fault activated (fault_type={fault_type}, detail={msg.detail!r})")
            return

        if fault_type in self._faults:
            self._faults.pop(fault_type, None)
            self.get_logger().info(f"safety fault cleared (fault_type={fault_type})")

    def _handle_perception_heartbeat(self, msg: PerceptionHeartbeat) -> None:
        self._last_perception_heartbeat_monotonic_s = time.monotonic()
        self._last_perception_latency_s = float(msg.pipeline_latency_s)
        self._last_perception_healthy = bool(msg.healthy)

    def _evaluate_safety(self) -> None:
        vehicle_state = self._latest_vehicle_state
        if vehicle_state is None:
            self._publish_inactive_status()
            return

        now = time.monotonic()
        mission_active = bool(
            self._latest_mission_status
            and self._latest_mission_status.active
            and not self._latest_mission_status.terminal
        )
        monitoring_window = mission_active or bool(vehicle_state.armed)

        position_valid = bool(vehicle_state.position_valid)
        home_position_valid = (
            self._home_latitude_deg is not None
            and self._home_longitude_deg is not None
            and position_valid
        )
        distance_from_home_m = 0.0
        if home_position_valid:
            distance_from_home_m = horizontal_distance_m(
                float(vehicle_state.latitude_deg),
                float(vehicle_state.longitude_deg),
                float(self._home_latitude_deg),
                float(self._home_longitude_deg),
            )

        injected_gps_loss = "gps_loss" in self._faults
        gps_lost = injected_gps_loss or (
            monitoring_window
            and bool(vehicle_state.connected)
            and not position_valid
            and self._position_invalid_since_monotonic_s is not None
            and (now - self._position_invalid_since_monotonic_s) >= self._config.gps_loss_timeout_s
        )
        perception_timeout = "perception_timeout" in self._faults
        perception_latency_exceeded = "perception_latency" in self._faults
        if self._config.require_perception_heartbeat and monitoring_window:
            if self._last_perception_heartbeat_monotonic_s is None:
                perception_timeout = True
            elif (now - self._last_perception_heartbeat_monotonic_s) > self._config.perception_timeout_s:
                perception_timeout = True
            if (
                self._last_perception_heartbeat_monotonic_s is not None
                and (
                    not self._last_perception_healthy
                    or self._last_perception_latency_s > self._config.perception_max_latency_s
                )
            ):
                perception_latency_exceeded = True

        signals = SafetySignals(
            mission_active=mission_active,
            vehicle_connected=bool(vehicle_state.connected),
            vehicle_armed=bool(vehicle_state.armed),
            vehicle_landed=bool(vehicle_state.landed),
            vehicle_failsafe=bool(vehicle_state.failsafe),
            position_valid=position_valid,
            home_position_valid=bool(home_position_valid),
            distance_from_home_m=distance_from_home_m,
            relative_altitude_m=float(vehicle_state.relative_altitude_m),
            gps_lost=gps_lost,
            rc_lost="rc_loss" in self._faults,
            data_link_lost="data_link_loss" in self._faults,
            perception_timeout=perception_timeout,
            perception_latency_exceeded=perception_latency_exceeded,
        )
        decision = evaluate_safety(self._config, signals)

        if decision is None:
            self._publish_inactive_status()
            return

        signature = (decision.rule, decision.action, decision.source)
        mission_abort_requested = False
        vehicle_command_sent = False
        if signature != self._last_active_signature:
            self._last_active_signature = signature
            self._trigger_count += 1
            if mission_active:
                self._publish_mission_command("abort")
                mission_abort_requested = True
            if bool(vehicle_state.connected) and bool(vehicle_state.armed) and decision.action in {
                "land",
                "return_to_home",
            }:
                self._publish_vehicle_command(decision.action)
                vehicle_command_sent = True
            self.get_logger().warning(
                f"safety rule triggered (rule={decision.rule}, action={decision.action}, source={decision.source})"
            )

        self._publish_safety_status(
            active=True,
            mission_abort_requested=mission_abort_requested,
            vehicle_command_sent=vehicle_command_sent,
            rule=decision.rule,
            action=decision.action,
            source=decision.source,
            detail=decision.detail,
        )

    def _publish_inactive_status(self) -> None:
        if self._last_active_signature is None:
            return
        self._last_active_signature = None
        self._publish_safety_status(
            active=False,
            mission_abort_requested=False,
            vehicle_command_sent=False,
            rule="",
            action="",
            source="",
            detail="safety state clear",
        )

    def _publish_safety_status(
        self,
        *,
        active: bool,
        mission_abort_requested: bool,
        vehicle_command_sent: bool,
        rule: str,
        action: str,
        source: str,
        detail: str,
    ) -> None:
        msg = SafetyStatus()
        msg.stamp = self.get_clock().now().to_msg()
        msg.active = active
        msg.mission_abort_requested = mission_abort_requested
        msg.vehicle_command_sent = vehicle_command_sent
        msg.rule = rule
        msg.action = action
        msg.source = source
        msg.detail = detail
        msg.trigger_count = self._trigger_count
        self._status_publisher.publish(msg)

    def _publish_mission_command(self, command: str) -> None:
        msg = MissionCommand()
        msg.stamp = self.get_clock().now().to_msg()
        msg.command = command
        self._mission_command_publisher.publish(msg)

    def _publish_vehicle_command(self, command: str) -> None:
        msg = VehicleCommand()
        msg.stamp = self.get_clock().now().to_msg()
        msg.command = command
        self._vehicle_command_publisher.publish(msg)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = SafetyManagerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
