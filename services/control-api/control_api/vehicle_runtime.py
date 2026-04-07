from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shlex
import subprocess
import uuid
from typing import Any, Protocol

from control_plane.domain import ControlPlaneErrorCode


@dataclass(frozen=True)
class VehicleCommandDispatch:
    action_name: str
    command_name: str
    artifacts: tuple[dict[str, Any], ...]


class VehicleRuntimeError(RuntimeError):
    def __init__(self, code: ControlPlaneErrorCode, message: str, detail: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail


class VehicleRuntimeAdapter(Protocol):
    def supported_actions(self) -> set[str]:
        raise NotImplementedError

    def dispatch(self, action_name: str, payload: dict[str, Any]) -> VehicleCommandDispatch:
        raise NotImplementedError


class ShellRos2VehicleRuntimeAdapter:
    def __init__(
        self,
        repo_root: Path,
        *,
        state_root: Path | None = None,
        command_topic: str = "/drone/vehicle_command",
        command_type: str = "drone_msgs/msg/VehicleCommand",
        command_timeout_s: float = 15.0,
    ) -> None:
        self._repo_root = repo_root
        self._state_root = state_root or repo_root / ".sim-runtime" / "control-api-vehicle"
        self._state_root.mkdir(parents=True, exist_ok=True)
        self._logs_root = self._state_root / "commands"
        self._logs_root.mkdir(parents=True, exist_ok=True)
        self._command_topic = command_topic
        self._command_type = command_type
        self._command_timeout_s = command_timeout_s
        self._supported_actions = {
            "vehicle.arm",
            "vehicle.disarm",
            "vehicle.takeoff",
            "vehicle.land",
            "vehicle.return_to_home",
            "vehicle.goto",
        }

    def supported_actions(self) -> set[str]:
        return set(self._supported_actions)

    def dispatch(self, action_name: str, payload: dict[str, Any]) -> VehicleCommandDispatch:
        if action_name not in self._supported_actions:
            raise VehicleRuntimeError(
                ControlPlaneErrorCode.NOT_SUPPORTED,
                f"{action_name} is not materialized by the current vehicle runtime",
                detail="vehicle control in Mark 1 supports arm, disarm, takeoff, land, return_to_home and goto",
            )

        command_name = action_name.split(".", 1)[1]
        ros_message = self._build_message(command_name, payload)
        log_path = self._logs_root / f"{command_name}-{uuid.uuid4().hex[:12]}.log"

        ros_setup = Path("/opt/ros/humble/setup.bash")
        workspace_setup = self._repo_root / "robotics" / "ros2_ws" / "install" / "setup.bash"
        shell_lines = ["set -e"]
        if ros_setup.exists():
            shell_lines.append(f"source {shlex.quote(str(ros_setup))}")
        if workspace_setup.exists():
            shell_lines.append(f"source {shlex.quote(str(workspace_setup))}")
        shell_lines.append(
            "command -v ros2 >/dev/null 2>&1 || "
            "(echo 'ros2 CLI is not available for vehicle control' >&2; exit 127)"
        )
        shell_lines.append(
            "ros2 topic pub --once "
            f"{shlex.quote(self._command_topic)} "
            f"{shlex.quote(self._command_type)} "
            f"{shlex.quote(ros_message)}"
        )

        try:
            completed = subprocess.run(
                ["bash", "-lc", "\n".join(shell_lines)],
                cwd=self._repo_root,
                capture_output=True,
                text=True,
                timeout=self._command_timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise VehicleRuntimeError(
                ControlPlaneErrorCode.TIMEOUT,
                f"{action_name} timed out while dispatching to ROS 2",
                detail=str(exc),
            ) from exc

        log_body = "\n".join(
            part
            for part in [
                f"action_name={action_name}",
                f"command_name={command_name}",
                f"topic={self._command_topic}",
                completed.stdout.strip(),
                completed.stderr.strip(),
            ]
            if part
        )
        log_path.write_text(log_body + "\n", encoding="utf-8")

        if completed.returncode != 0:
            raise VehicleRuntimeError(
                ControlPlaneErrorCode.DEPENDENCY_UNAVAILABLE,
                f"{action_name} failed in the ROS 2 vehicle adapter",
                detail=log_body,
            )

        return VehicleCommandDispatch(
            action_name=action_name,
            command_name=command_name,
            artifacts=(
                {
                    "artifact_type": "vehicle_command_log",
                    "uri": str(log_path),
                    "description": f"{action_name} dispatch log",
                },
            ),
        )

    def _build_message(self, command_name: str, payload: dict[str, Any]) -> str:
        target_altitude_m = float(payload.get("target_altitude_m", 0.0))
        target_absolute_altitude_m = float(payload.get("target_absolute_altitude_m", 0.0))
        target_yaw_deg = float(payload.get("target_yaw_deg", 0.0))
        target_latitude_deg = float(payload.get("target_latitude_deg", 0.0))
        target_longitude_deg = float(payload.get("target_longitude_deg", 0.0))
        return (
            "{stamp: {sec: 0, nanosec: 0}, "
            f"command: \"{command_name}\", "
            f"target_altitude_m: {target_altitude_m}, "
            f"target_absolute_altitude_m: {target_absolute_altitude_m}, "
            f"target_yaw_deg: {target_yaw_deg}, "
            f"target_latitude_deg: {target_latitude_deg}, "
            f"target_longitude_deg: {target_longitude_deg}}}"
        )
