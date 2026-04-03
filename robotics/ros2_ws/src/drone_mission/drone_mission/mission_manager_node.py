from __future__ import annotations

import asyncio
import os
import threading
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy

from drone_msgs.msg import (
    MissionCommand,
    MissionStatus,
    PerceptionEvent,
    TrackedObject,
    VehicleCommand,
    VehicleCommandStatus,
    VehicleState,
)

from drone_mission.gateway import create_gateway
from drone_mission.errors import MissionTimeout
from drone_mission.loader import MissionValidationError, load_mission_contract
from drone_mission.mission_executor import MissionExecutor
from drone_mission.mission_state_machine import MissionPhase, MissionStateMachine


class MissionManagerNode(Node):
    def __init__(self) -> None:
        super().__init__("mission_manager")

        self.declare_parameter("mission_command_topic", "/drone/mission_command")
        self.declare_parameter("mission_status_topic", "/drone/mission_status")
        self.declare_parameter("state_topic", "/drone/vehicle_state")
        self.declare_parameter("command_topic", "/drone/vehicle_command")
        self.declare_parameter("command_status_topic", "/drone/vehicle_command_status")
        self.declare_parameter("perception_event_topic", "/drone/perception/event")
        self.declare_parameter("tracked_object_topic", "/drone/perception/tracked_object")
        self.declare_parameter("scenario_file", "simulation/scenarios/patrol_basic.json")
        self.declare_parameter("backend", "ros2_domain")
        self.declare_parameter("auto_start", False)
        self.declare_parameter("require_track_lock_before_patrol", False)
        self.declare_parameter("track_lock_timeout_s", 20.0)
        self.declare_parameter("publish_rate_hz", 5.0)
        self.declare_parameter("command_retry_interval_s", 3.0)
        self.declare_parameter("max_command_retries", 5)
        self.declare_parameter("takeoff_altitude_tolerance_m", 0.4)

        scenario_file = str(self.get_parameter("scenario_file").value)
        if not os.path.isabs(scenario_file):
            scenario_file = os.path.join(os.getcwd(), scenario_file)

        self._contract = load_mission_contract(scenario_file)
        self._backend = str(self.get_parameter("backend").value)
        self._auto_start = bool(self.get_parameter("auto_start").value)
        self._state_lock = threading.Lock()
        self._latest_vehicle_state: VehicleState | None = None
        self._latest_command_status: VehicleCommandStatus | None = None
        self._latest_command_status_serial = 0
        self._latest_perception_event: PerceptionEvent | None = None
        self._latest_perception_event_serial = 0
        self._latest_tracked_object: TrackedObject | None = None
        self._last_forwarded_command = ""
        self._abort_requested = threading.Event()
        self._worker_thread: threading.Thread | None = None
        self._state_machine = MissionStateMachine(
            mission_id=self._contract.name,
            total_waypoints=len(self._contract.patrol.waypoint_offsets_north_m),
        )

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
            MissionStatus,
            str(self.get_parameter("mission_status_topic").value),
            status_qos,
        )
        self._vehicle_command_publisher = self.create_publisher(
            VehicleCommand,
            str(self.get_parameter("command_topic").value),
            domain_qos,
        )
        self.create_subscription(
            MissionCommand,
            str(self.get_parameter("mission_command_topic").value),
            self._handle_mission_command,
            domain_qos,
        )
        self.create_subscription(
            VehicleState,
            str(self.get_parameter("state_topic").value),
            self._handle_vehicle_state,
            domain_qos,
        )
        self.create_subscription(
            VehicleCommandStatus,
            str(self.get_parameter("command_status_topic").value),
            self._handle_vehicle_command_status,
            status_qos,
        )
        self.create_subscription(
            PerceptionEvent,
            str(self.get_parameter("perception_event_topic").value),
            self._handle_perception_event,
            domain_qos,
        )
        self.create_subscription(
            TrackedObject,
            str(self.get_parameter("tracked_object_topic").value),
            self._handle_tracked_object,
            domain_qos,
        )

        publish_rate_hz = float(self.get_parameter("publish_rate_hz").value)
        self.create_timer(1.0 / max(publish_rate_hz, 1.0), self._publish_status)
        self.create_timer(0.5, self._maybe_auto_start)

        self.get_logger().info(
            "mission_manager initialized "
            f"(scenario_file={scenario_file}, backend={self._backend}, auto_start={self._auto_start})",
        )

    def _handle_vehicle_state(self, msg: VehicleState) -> None:
        with self._state_lock:
            self._latest_vehicle_state = msg

    def _handle_vehicle_command_status(self, msg: VehicleCommandStatus) -> None:
        with self._state_lock:
            self._latest_command_status = msg
            self._latest_command_status_serial += 1

    def _handle_perception_event(self, msg: PerceptionEvent) -> None:
        with self._state_lock:
            self._latest_perception_event = msg
            self._latest_perception_event_serial += 1

    def _handle_tracked_object(self, msg: TrackedObject) -> None:
        with self._state_lock:
            self._latest_tracked_object = msg

    def _handle_mission_command(self, msg: MissionCommand) -> None:
        command = msg.command.strip().lower().replace("-", "_").replace(" ", "_")
        if command in {"start", "start_patrol"}:
            self._start_worker(reason="mission start requested from topic")
            return
        if command == "abort":
            self._abort_requested.set()
            self.get_logger().warning("mission abort requested from topic")
            return
        if command == "reset":
            if self._worker_thread and self._worker_thread.is_alive():
                self.get_logger().warning("cannot reset mission while worker is still active")
                return
            with self._state_lock:
                self._state_machine.reset()
                self._last_forwarded_command = ""
            self.get_logger().info("mission state machine reset")
            return
        self.get_logger().warning(f"unsupported mission command={msg.command!r}")

    def _maybe_auto_start(self) -> None:
        if not self._auto_start:
            return
        if self._worker_thread and self._worker_thread.is_alive():
            return
        with self._state_lock:
            latest_vehicle_state = self._latest_vehicle_state
        if latest_vehicle_state is None:
            return
        if (
            not latest_vehicle_state.connected
            or not latest_vehicle_state.position_valid
            or latest_vehicle_state.failsafe
        ):
            return
        self._auto_start = False
        self._start_worker(reason="mission auto-start after vehicle connection")

    def _start_worker(self, *, reason: str) -> None:
        if self._worker_thread and self._worker_thread.is_alive():
            self.get_logger().warning("mission worker already active")
            return

        self._abort_requested.clear()
        with self._state_lock:
            if self._state_machine.snapshot.phase != MissionPhase.IDLE:
                self._state_machine.reset(detail="mission restart requested")
        self._worker_thread = threading.Thread(
            target=self._run_worker,
            name="mission-manager-worker",
            daemon=True,
        )
        self._worker_thread.start()
        self.get_logger().info(reason)

    def _run_worker(self) -> None:
        try:
            gateway = create_gateway(
                self._backend,
                publish_command=self._publish_vehicle_command,
                get_vehicle_state=self._get_latest_vehicle_state,
                get_command_status=self._get_latest_command_status,
                command_retry_interval_s=float(self.get_parameter("command_retry_interval_s").value),
                max_command_retries=int(self.get_parameter("max_command_retries").value),
                takeoff_altitude_tolerance_m=float(self.get_parameter("takeoff_altitude_tolerance_m").value),
            )
            executor = MissionExecutor(
                gateway=gateway,
                state_machine=self._state_machine,
                wait_for_visual_lock=(
                    self._wait_for_visual_lock
                    if bool(self.get_parameter("require_track_lock_before_patrol").value)
                    else None
                ),
                visual_lock_timeout_s=float(self.get_parameter("track_lock_timeout_s").value),
            )
            asyncio.run(executor.run(self._contract, should_abort=self._abort_requested.is_set))
        except MissionValidationError as exc:
            with self._state_lock:
                self._state_machine.transition(MissionPhase.FAILED, detail=str(exc))
            self.get_logger().error(f"mission contract error: {exc}")
        except Exception as exc:  # pragma: no cover
            with self._state_lock:
                terminal_phases = {MissionPhase.ABORTED, MissionPhase.COMPLETED, MissionPhase.FAILED}
                if self._state_machine.snapshot.phase not in terminal_phases:
                    self._state_machine.transition(MissionPhase.FAILED, detail=str(exc))
            self.get_logger().error(f"mission worker failed: {exc}")

    def _publish_vehicle_command(self, command: str, **payload: float) -> None:
        msg = VehicleCommand()
        msg.stamp = self.get_clock().now().to_msg()
        msg.command = command
        msg.target_altitude_m = float(payload.get("target_altitude_m", 0.0))
        msg.target_absolute_altitude_m = float(payload.get("target_absolute_altitude_m", 0.0))
        msg.target_yaw_deg = float(payload.get("target_yaw_deg", 0.0))
        msg.target_latitude_deg = float(payload.get("target_latitude_deg", 0.0))
        msg.target_longitude_deg = float(payload.get("target_longitude_deg", 0.0))
        self._vehicle_command_publisher.publish(msg)
        with self._state_lock:
            self._last_forwarded_command = command
        self.get_logger().info(f"forwarded mission vehicle command={command}")

    def _get_latest_vehicle_state(self) -> VehicleState | None:
        with self._state_lock:
            return self._latest_vehicle_state

    def _get_latest_command_status(self) -> tuple[int, VehicleCommandStatus | None]:
        with self._state_lock:
            return self._latest_command_status_serial, self._latest_command_status

    async def _wait_for_visual_lock(self, timeout_s: float) -> None:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            with self._state_lock:
                latest_event = self._latest_perception_event
                latest_tracked_object = self._latest_tracked_object
            if latest_tracked_object is not None and bool(latest_tracked_object.tracked):
                return
            if latest_event is not None and latest_event.event_type == "track_locked":
                return
            await asyncio.sleep(0.1)
        raise MissionTimeout("timed out while waiting for perception visual lock")

    def _publish_status(self) -> None:
        with self._state_lock:
            snapshot = self._state_machine.snapshot
            last_forwarded_command = getattr(self, "_last_forwarded_command", "")

        msg = MissionStatus()
        msg.stamp = self.get_clock().now().to_msg()
        msg.mission_id = snapshot.mission_id
        msg.phase = snapshot.phase.value
        msg.active = snapshot.active
        msg.completed = snapshot.completed
        msg.aborted = snapshot.aborted
        msg.failed = snapshot.failed
        msg.terminal = snapshot.completed or snapshot.aborted or snapshot.failed
        msg.succeeded = snapshot.completed
        msg.detail = snapshot.detail
        msg.current_waypoint_index = snapshot.current_waypoint_index
        msg.total_waypoints = snapshot.total_waypoints
        msg.last_command = last_forwarded_command
        self._status_publisher.publish(msg)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = MissionManagerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
