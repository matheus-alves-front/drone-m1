"""ROS 2 bridge node that exposes a real PX4-backed domain boundary."""

from __future__ import annotations

import math
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy

from drone_msgs.msg import VehicleCommand as DomainVehicleCommand
from drone_msgs.msg import VehicleCommandStatus as DomainVehicleCommandStatus
from drone_msgs.msg import VehicleState as DomainVehicleState
from px4_msgs.msg import GotoSetpoint as Px4GotoSetpoint
from px4_msgs.msg import VehicleCommand as Px4VehicleCommand
from px4_msgs.msg import VehicleCommandAck
from px4_msgs.msg import FailsafeFlags
from px4_msgs.msg import VehicleGlobalPosition
from px4_msgs.msg import VehicleLandDetected
from px4_msgs.msg import VehicleControlMode
from px4_msgs.msg import VehicleLocalPosition
from px4_msgs.msg import VehicleStatus

from drone_px4.state_model import (
    geodetic_offset_m,
    local_position_from_reference,
    nav_state_name,
    normalize_command,
    resolve_takeoff_altitude,
)


class Px4BridgeNode(Node):
    """Bridge node that adapts real PX4 messages into domain-safe messages."""

    def __init__(self) -> None:
        super().__init__("px4_bridge")

        self.declare_parameter("state_topic", "/drone/vehicle_state")
        self.declare_parameter("command_topic", "/drone/vehicle_command")
        self.declare_parameter("command_status_topic", "/drone/vehicle_command_status")
        self.declare_parameter("publish_rate_hz", 5.0)
        self.declare_parameter("telemetry_timeout_s", 1.5)
        self.declare_parameter("default_takeoff_altitude_m", 3.0)
        self.declare_parameter("target_system", 1)
        self.declare_parameter("target_component", 1)
        self.declare_parameter("source_system", 1)
        self.declare_parameter("source_component", 1)
        self.declare_parameter("px4_vehicle_status_topic", "/fmu/out/vehicle_status")
        self.declare_parameter("px4_vehicle_local_position_topic", "/fmu/out/vehicle_local_position")
        self.declare_parameter("px4_vehicle_global_position_topic", "/fmu/out/vehicle_global_position")
        self.declare_parameter("px4_vehicle_land_detected_topic", "/fmu/out/vehicle_land_detected")
        self.declare_parameter("px4_vehicle_control_mode_topic", "/fmu/out/vehicle_control_mode")
        self.declare_parameter("px4_failsafe_flags_topic", "/fmu/out/failsafe_flags")
        self.declare_parameter("px4_vehicle_command_ack_topic", "/fmu/out/vehicle_command_ack")
        self.declare_parameter("px4_vehicle_command_input_topic", "/fmu/in/vehicle_command")
        self.declare_parameter("px4_goto_setpoint_input_topic", "/fmu/in/goto_setpoint")

        self._telemetry_timeout_s = float(self.get_parameter("telemetry_timeout_s").value)
        self._default_takeoff_altitude_m = float(self.get_parameter("default_takeoff_altitude_m").value)
        self._target_system = int(self.get_parameter("target_system").value)
        self._target_component = int(self.get_parameter("target_component").value)
        self._source_system = int(self.get_parameter("source_system").value)
        self._source_component = int(self.get_parameter("source_component").value)

        self._vehicle_status: VehicleStatus | None = None
        self._vehicle_local_position: VehicleLocalPosition | None = None
        self._vehicle_global_position: VehicleGlobalPosition | None = None
        self._vehicle_land_detected: VehicleLandDetected | None = None
        self._vehicle_control_mode: VehicleControlMode | None = None
        self._failsafe_flags: FailsafeFlags | None = None
        self._last_command_ack: VehicleCommandAck | None = None
        self._last_status_monotonic_s = 0.0
        self._last_position_monotonic_s = 0.0
        self._last_land_detected_monotonic_s = 0.0
        self._last_control_mode_monotonic_s = 0.0
        self._last_failsafe_flags_monotonic_s = 0.0
        self._saw_vehicle_status = False
        self._saw_vehicle_local_position = False
        self._saw_vehicle_global_position = False
        self._saw_vehicle_land_detected = False
        self._saw_vehicle_control_mode = False
        self._saw_failsafe_flags = False
        self._logged_first_state_publish = False
        self._last_connected_state: bool | None = None
        self._last_armed_source_warning: bool | None = None
        self._pending_command_names: dict[int, str] = {}
        self._active_goto_setpoint: Px4GotoSetpoint | None = None

        px4_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )
        domain_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        command_status_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )

        state_topic = str(self.get_parameter("state_topic").value)
        command_topic = str(self.get_parameter("command_topic").value)
        command_status_topic = str(self.get_parameter("command_status_topic").value)
        publish_rate_hz = float(self.get_parameter("publish_rate_hz").value)

        self._state_publisher = self.create_publisher(DomainVehicleState, state_topic, domain_qos)
        self._command_status_publisher = self.create_publisher(
            DomainVehicleCommandStatus,
            command_status_topic,
            command_status_qos,
        )
        self._vehicle_command_publisher = self.create_publisher(
            Px4VehicleCommand,
            str(self.get_parameter("px4_vehicle_command_input_topic").value),
            px4_qos,
        )
        self._goto_setpoint_publisher = self.create_publisher(
            Px4GotoSetpoint,
            str(self.get_parameter("px4_goto_setpoint_input_topic").value),
            px4_qos,
        )
        self._command_subscription = self.create_subscription(
            DomainVehicleCommand,
            command_topic,
            self._handle_command,
            domain_qos,
        )
        self._vehicle_status_subscription = self.create_subscription(
            VehicleStatus,
            str(self.get_parameter("px4_vehicle_status_topic").value),
            self._handle_vehicle_status,
            px4_qos,
        )
        self._vehicle_local_position_subscription = self.create_subscription(
            VehicleLocalPosition,
            str(self.get_parameter("px4_vehicle_local_position_topic").value),
            self._handle_vehicle_local_position,
            px4_qos,
        )
        self._vehicle_global_position_subscription = self.create_subscription(
            VehicleGlobalPosition,
            str(self.get_parameter("px4_vehicle_global_position_topic").value),
            self._handle_vehicle_global_position,
            px4_qos,
        )
        self._vehicle_land_detected_subscription = self.create_subscription(
            VehicleLandDetected,
            str(self.get_parameter("px4_vehicle_land_detected_topic").value),
            self._handle_vehicle_land_detected,
            px4_qos,
        )
        self._vehicle_control_mode_subscription = self.create_subscription(
            VehicleControlMode,
            str(self.get_parameter("px4_vehicle_control_mode_topic").value),
            self._handle_vehicle_control_mode,
            px4_qos,
        )
        self._failsafe_flags_subscription = self.create_subscription(
            FailsafeFlags,
            str(self.get_parameter("px4_failsafe_flags_topic").value),
            self._handle_failsafe_flags,
            px4_qos,
        )
        self._vehicle_command_ack_subscription = self.create_subscription(
            VehicleCommandAck,
            str(self.get_parameter("px4_vehicle_command_ack_topic").value),
            self._handle_vehicle_command_ack,
            px4_qos,
        )
        self._timer = self.create_timer(1.0 / max(publish_rate_hz, 1.0), self._publish_state)

        self.get_logger().info(
            "px4_bridge initialized "
            f"(state_topic={state_topic}, command_topic={command_topic}, command_status_topic={command_status_topic}, "
            f"telemetry_timeout_s={self._telemetry_timeout_s})",
        )

    def _handle_vehicle_status(self, msg: VehicleStatus) -> None:
        self._vehicle_status = msg
        self._last_status_monotonic_s = time.monotonic()
        if not self._saw_vehicle_status:
            self._saw_vehicle_status = True
            self.get_logger().info(
                "received first vehicle_status "
                f"(arming_state={msg.arming_state}, nav_state={msg.nav_state}, failsafe={msg.failsafe})",
            )

    def _handle_vehicle_local_position(self, msg: VehicleLocalPosition) -> None:
        self._vehicle_local_position = msg
        self._last_position_monotonic_s = time.monotonic()
        if not self._saw_vehicle_local_position:
            self._saw_vehicle_local_position = True
            self.get_logger().info(
                "received first vehicle_local_position "
                f"(z_valid={msg.z_valid}, z={msg.z:.3f})",
            )

    def _handle_vehicle_global_position(self, msg: VehicleGlobalPosition) -> None:
        self._vehicle_global_position = msg
        if not self._saw_vehicle_global_position:
            self._saw_vehicle_global_position = True
            self.get_logger().info(
                "received first vehicle_global_position "
                f"(lat_lon_valid={msg.lat_lon_valid}, alt_valid={msg.alt_valid}, alt={msg.alt:.3f})",
            )

    def _handle_vehicle_land_detected(self, msg: VehicleLandDetected) -> None:
        self._vehicle_land_detected = msg
        self._last_land_detected_monotonic_s = time.monotonic()
        if not self._saw_vehicle_land_detected:
            self._saw_vehicle_land_detected = True
            self.get_logger().info(
                "received first vehicle_land_detected "
                f"(landed={msg.landed}, maybe_landed={msg.maybe_landed}, ground_contact={msg.ground_contact})",
            )

    def _handle_vehicle_control_mode(self, msg: VehicleControlMode) -> None:
        self._vehicle_control_mode = msg
        self._last_control_mode_monotonic_s = time.monotonic()
        if not self._saw_vehicle_control_mode:
            self._saw_vehicle_control_mode = True
            self.get_logger().info(
                "received first vehicle_control_mode "
                f"(flag_armed={msg.flag_armed}, source_id={msg.source_id})",
            )

    def _handle_failsafe_flags(self, msg: FailsafeFlags) -> None:
        self._failsafe_flags = msg
        self._last_failsafe_flags_monotonic_s = time.monotonic()
        if not self._saw_failsafe_flags:
            self._saw_failsafe_flags = True
            self.get_logger().info(
                "received first failsafe_flags "
                f"(fd_critical_failure={msg.fd_critical_failure}, motor_failure={msg.fd_motor_failure}, "
                f"gcs_connection_lost={msg.gcs_connection_lost})",
            )

    def _handle_vehicle_command_ack(self, msg: VehicleCommandAck) -> None:
        self._last_command_ack = msg
        command_name = self._resolve_command_name_from_ack(msg)
        status_msg = DomainVehicleCommandStatus()
        status_msg.stamp = self.get_clock().now().to_msg()
        status_msg.command = command_name
        status_msg.px4_command = int(msg.command)
        status_msg.result = int(msg.result)
        status_msg.accepted = int(msg.result) == VehicleCommandAck.VEHICLE_CMD_RESULT_ACCEPTED
        status_msg.result_label = self._ack_result_label(int(msg.result))
        self._command_status_publisher.publish(status_msg)
        self.get_logger().info(
            f"vehicle command ack received (command={msg.command}, result={msg.result}, command_name={command_name})",
        )

    def _handle_command(self, msg: DomainVehicleCommand) -> None:
        normalized_command = normalize_command(msg.command)

        if normalized_command in {"goto", "go_to"}:
            goto_setpoint = self._build_goto_setpoint(
                target_latitude_deg=msg.target_latitude_deg,
                target_longitude_deg=msg.target_longitude_deg,
                target_absolute_altitude_m=msg.target_absolute_altitude_m,
                target_yaw_deg=msg.target_yaw_deg,
            )
            if goto_setpoint is None:
                self.get_logger().warning(
                    "unable to build goto_setpoint; waiting for valid local/global position reference before goto",
                )
                return

            self._active_goto_setpoint = goto_setpoint
            self._goto_setpoint_publisher.publish(goto_setpoint)
            self.get_logger().info(
                "forwarded domain command to PX4 goto_setpoint "
                f"(x={goto_setpoint.position[0]:.2f}, y={goto_setpoint.position[1]:.2f}, "
                f"z={goto_setpoint.position[2]:.2f})",
            )
            return

        vehicle_command = self._build_vehicle_command(
            normalized_command,
            target_altitude_m=msg.target_altitude_m,
            target_absolute_altitude_m=msg.target_absolute_altitude_m,
            target_yaw_deg=msg.target_yaw_deg,
            target_latitude_deg=msg.target_latitude_deg,
            target_longitude_deg=msg.target_longitude_deg,
        )

        if vehicle_command is None:
            self.get_logger().warning(
                "unsupported domain command="
                f"{normalized_command!r}; supported commands: arm, disarm, takeoff, land, goto, return_to_home",
            )
            return

        if normalized_command != "goto":
            self._active_goto_setpoint = None
        self._vehicle_command_publisher.publish(vehicle_command)
        self._pending_command_names[int(vehicle_command.command)] = normalized_command
        self.get_logger().info(
            f"forwarded domain command to PX4 (command={normalized_command}, px4_command={vehicle_command.command})",
        )

    def _build_vehicle_command(
        self,
        normalized_command: str,
        *,
        target_altitude_m: float,
        target_absolute_altitude_m: float,
        target_yaw_deg: float,
        target_latitude_deg: float,
        target_longitude_deg: float,
    ) -> Px4VehicleCommand | None:
        msg = Px4VehicleCommand()
        msg.timestamp = self._now_us()
        msg.target_system = self._target_system
        msg.target_component = self._target_component
        msg.source_system = self._source_system
        msg.source_component = self._source_component
        msg.confirmation = 0
        msg.from_external = True

        if normalized_command == "arm":
            msg.command = Px4VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM
            msg.param1 = float(Px4VehicleCommand.ARMING_ACTION_ARM)
            return msg

        if normalized_command == "disarm":
            msg.command = Px4VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM
            msg.param1 = float(Px4VehicleCommand.ARMING_ACTION_DISARM)
            return msg

        if normalized_command == "land":
            msg.command = Px4VehicleCommand.VEHICLE_CMD_NAV_LAND
            self._apply_current_global_position(msg)
            return msg

        if normalized_command == "takeoff":
            msg.command = Px4VehicleCommand.VEHICLE_CMD_NAV_TAKEOFF
            target_altitude = resolve_takeoff_altitude(
                target_altitude_m,
                self._default_takeoff_altitude_m,
            )
            self._apply_current_global_position(msg)
            if self._vehicle_global_position and self._vehicle_global_position.alt_valid:
                msg.param7 = float(self._vehicle_global_position.alt + target_altitude)
            else:
                msg.param7 = float(target_altitude)
            return msg

        if normalized_command in {"goto", "go_to"}:
            return None

        if normalized_command in {"return_to_home", "rtl"}:
            msg.command = Px4VehicleCommand.VEHICLE_CMD_NAV_RETURN_TO_LAUNCH
            return msg

        return None

    def _build_goto_setpoint(
        self,
        *,
        target_latitude_deg: float,
        target_longitude_deg: float,
        target_absolute_altitude_m: float,
        target_yaw_deg: float,
    ) -> Px4GotoSetpoint | None:
        if (
            self._vehicle_local_position is None
            or not self._vehicle_local_position.xy_valid
            or not self._vehicle_local_position.z_valid
            or not self._vehicle_global_position
            or not self._vehicle_global_position.lat_lon_valid
            or not self._vehicle_global_position.alt_valid
        ):
            return None

        if self._vehicle_local_position.xy_global and self._vehicle_local_position.z_global:
            target_x_m, target_y_m, target_z_m = local_position_from_reference(
                ref_lat_deg=float(self._vehicle_local_position.ref_lat),
                ref_lon_deg=float(self._vehicle_local_position.ref_lon),
                ref_alt_m=float(self._vehicle_local_position.ref_alt),
                target_lat_deg=float(target_latitude_deg),
                target_lon_deg=float(target_longitude_deg),
                target_alt_m=float(target_absolute_altitude_m),
            )
        else:
            delta_north_m, delta_east_m = geodetic_offset_m(
                float(self._vehicle_global_position.lat),
                float(self._vehicle_global_position.lon),
                float(target_latitude_deg),
                float(target_longitude_deg),
            )
            target_x_m = float(self._vehicle_local_position.x) + delta_north_m
            target_y_m = float(self._vehicle_local_position.y) + delta_east_m
            target_z_m = float(self._vehicle_local_position.z) - (
                float(target_absolute_altitude_m) - float(self._vehicle_global_position.alt)
            )

        goto_setpoint = Px4GotoSetpoint()
        goto_setpoint.timestamp = self._now_us()
        goto_setpoint.position = [float(target_x_m), float(target_y_m), float(target_z_m)]
        goto_setpoint.flag_control_heading = math.isfinite(target_yaw_deg)
        goto_setpoint.heading = float(math.radians(target_yaw_deg)) if math.isfinite(target_yaw_deg) else 0.0
        goto_setpoint.flag_set_max_horizontal_speed = False
        goto_setpoint.max_horizontal_speed = 0.0
        goto_setpoint.flag_set_max_vertical_speed = False
        goto_setpoint.max_vertical_speed = 0.0
        goto_setpoint.flag_set_max_heading_rate = False
        goto_setpoint.max_heading_rate = 0.0
        return goto_setpoint

    def _apply_current_global_position(self, msg: Px4VehicleCommand) -> None:
        if not self._vehicle_global_position:
            msg.param5 = math.nan
            msg.param6 = math.nan
            return

        if self._vehicle_global_position.lat_lon_valid:
            msg.param5 = float(self._vehicle_global_position.lat)
            msg.param6 = float(self._vehicle_global_position.lon)
        else:
            msg.param5 = math.nan
            msg.param6 = math.nan

        if self._vehicle_global_position.alt_valid:
            msg.param7 = float(self._vehicle_global_position.alt)

    @staticmethod
    def _ack_result_label(result: int) -> str:
        labels = {
            int(VehicleCommandAck.VEHICLE_CMD_RESULT_ACCEPTED): "ACCEPTED",
            int(VehicleCommandAck.VEHICLE_CMD_RESULT_TEMPORARILY_REJECTED): "TEMPORARILY_REJECTED",
            int(VehicleCommandAck.VEHICLE_CMD_RESULT_DENIED): "DENIED",
            int(VehicleCommandAck.VEHICLE_CMD_RESULT_UNSUPPORTED): "UNSUPPORTED",
            int(VehicleCommandAck.VEHICLE_CMD_RESULT_FAILED): "FAILED",
            int(VehicleCommandAck.VEHICLE_CMD_RESULT_IN_PROGRESS): "IN_PROGRESS",
            int(VehicleCommandAck.VEHICLE_CMD_RESULT_CANCELLED): "CANCELLED",
        }
        return labels.get(result, f"UNKNOWN_{result}")

    @staticmethod
    def _command_name_from_ack(msg: VehicleCommandAck) -> str:
        mapping = {
            int(Px4VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM): "arm_disarm",
            int(Px4VehicleCommand.VEHICLE_CMD_NAV_TAKEOFF): "takeoff",
            int(Px4VehicleCommand.VEHICLE_CMD_NAV_LAND): "land",
            int(Px4VehicleCommand.VEHICLE_CMD_DO_REPOSITION): "goto",
            int(Px4VehicleCommand.VEHICLE_CMD_NAV_RETURN_TO_LAUNCH): "return_to_home",
        }
        return mapping.get(int(msg.command), "unknown")

    def _resolve_command_name_from_ack(self, msg: VehicleCommandAck) -> str:
        recent_command_name = self._pending_command_names.get(int(msg.command))
        if recent_command_name:
            return recent_command_name
        return self._command_name_from_ack(msg)

    def _publish_state(self) -> None:
        state_msg = DomainVehicleState()
        state_msg.stamp = self.get_clock().now().to_msg()

        now = time.monotonic()
        connected = any(
            last_seen > 0.0 and (now - last_seen) <= self._telemetry_timeout_s
            for last_seen in (
                self._last_status_monotonic_s,
                self._last_position_monotonic_s,
                self._last_land_detected_monotonic_s,
                self._last_control_mode_monotonic_s,
                self._last_failsafe_flags_monotonic_s,
            )
        )
        state_msg.connected = connected
        if self._last_connected_state is None or connected != self._last_connected_state:
            self._last_connected_state = connected
            self.get_logger().info(
                f"vehicle_state connectivity transitioned (connected={connected})",
            )

        if not connected:
            self._active_goto_setpoint = None
            state_msg.armed = False
            state_msg.landed = False
            state_msg.failsafe = False
            state_msg.preflight_checks_pass = False
            state_msg.position_valid = False
            state_msg.nav_state = "DISCONNECTED"
            state_msg.altitude_m = 0.0
            state_msg.relative_altitude_m = 0.0
            state_msg.absolute_altitude_m = 0.0
            state_msg.latitude_deg = 0.0
            state_msg.longitude_deg = 0.0
            self._state_publisher.publish(state_msg)
            return

        vehicle_status_fresh = bool(
            self._vehicle_status and (now - self._last_status_monotonic_s) <= self._telemetry_timeout_s
        )
        vehicle_control_mode_fresh = bool(
            self._vehicle_control_mode and (now - self._last_control_mode_monotonic_s) <= self._telemetry_timeout_s
        )

        if vehicle_status_fresh:
            state_msg.armed = self._vehicle_status.arming_state == VehicleStatus.ARMING_STATE_ARMED
            state_msg.failsafe = bool(self._vehicle_status.failsafe)
            state_msg.preflight_checks_pass = bool(self._vehicle_status.pre_flight_checks_pass)
            state_msg.nav_state = nav_state_name(int(self._vehicle_status.nav_state))
        else:
            state_msg.armed = bool(
                vehicle_control_mode_fresh
                and self._vehicle_control_mode.flag_armed
            )
            state_msg.failsafe = bool(
                self._failsafe_flags
                and (now - self._last_failsafe_flags_monotonic_s) <= self._telemetry_timeout_s
                and (
                    self._failsafe_flags.fd_critical_failure
                    or self._failsafe_flags.fd_esc_arming_failure
                    or self._failsafe_flags.fd_motor_failure
                    or self._failsafe_flags.mission_failure
                    or self._failsafe_flags.navigator_failure
                    or self._failsafe_flags.vtol_fixed_wing_system_failure
                    or self._failsafe_flags.flight_time_limit_exceeded
                    or self._failsafe_flags.wind_limit_exceeded
                    or self._failsafe_flags.geofence_breached
                )
            )
            state_msg.preflight_checks_pass = bool(state_msg.armed)
            if self._vehicle_control_mode and (
                now - self._last_control_mode_monotonic_s
            ) <= self._telemetry_timeout_s:
                state_msg.nav_state = nav_state_name(int(self._vehicle_control_mode.source_id))
            else:
                state_msg.nav_state = "UNKNOWN"

        if vehicle_status_fresh and vehicle_control_mode_fresh:
            status_armed = self._vehicle_status.arming_state == VehicleStatus.ARMING_STATE_ARMED
            control_mode_armed = bool(self._vehicle_control_mode.flag_armed)
            armed_source_disagreement = status_armed != control_mode_armed
            if (
                self._last_armed_source_warning is None
                or armed_source_disagreement != self._last_armed_source_warning
            ):
                self._last_armed_source_warning = armed_source_disagreement
                if armed_source_disagreement:
                    self.get_logger().warning(
                        "armed-state source disagreement detected "
                        f"(vehicle_status={status_armed}, vehicle_control_mode={control_mode_armed})",
                    )
                else:
                    self.get_logger().info(
                        "armed-state source disagreement cleared "
                        f"(vehicle_status={status_armed}, vehicle_control_mode={control_mode_armed})",
                    )

        if self._vehicle_local_position and self._vehicle_local_position.z_valid:
            state_msg.altitude_m = float(-self._vehicle_local_position.z)
            state_msg.relative_altitude_m = float(-self._vehicle_local_position.z)
        else:
            state_msg.altitude_m = 0.0
            state_msg.relative_altitude_m = 0.0

        if self._vehicle_global_position and self._vehicle_global_position.alt_valid:
            state_msg.absolute_altitude_m = float(self._vehicle_global_position.alt)
        else:
            state_msg.absolute_altitude_m = 0.0

        if (
            self._vehicle_global_position
            and self._vehicle_global_position.lat_lon_valid
            and self._vehicle_global_position.alt_valid
        ):
            state_msg.position_valid = True
            state_msg.latitude_deg = float(self._vehicle_global_position.lat)
            state_msg.longitude_deg = float(self._vehicle_global_position.lon)
        else:
            state_msg.position_valid = False
            state_msg.latitude_deg = 0.0
            state_msg.longitude_deg = 0.0

        if self._vehicle_land_detected and (
            time.monotonic() - self._last_land_detected_monotonic_s
        ) <= self._telemetry_timeout_s:
            state_msg.landed = bool(self._vehicle_land_detected.landed)
        else:
            state_msg.landed = False

        self._state_publisher.publish(state_msg)
        if self._active_goto_setpoint is not None and not state_msg.failsafe:
            self._active_goto_setpoint.timestamp = self._now_us()
            self._goto_setpoint_publisher.publish(self._active_goto_setpoint)
        if not self._logged_first_state_publish:
            self._logged_first_state_publish = True
            self.get_logger().info(
                "published first vehicle_state "
                f"(connected={state_msg.connected}, armed={state_msg.armed}, landed={state_msg.landed}, "
                f"nav_state={state_msg.nav_state}, altitude_m={state_msg.altitude_m:.3f})",
            )

    def _now_us(self) -> int:
        return int(self.get_clock().now().nanoseconds / 1000)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = Px4BridgeNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
