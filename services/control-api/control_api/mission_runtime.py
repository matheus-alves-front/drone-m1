from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shlex
import subprocess
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from control_plane.domain import ControlPlaneErrorCode, MissionStatus


@dataclass(frozen=True)
class MissionRuntimeObservation:
    mission_id: str
    status: MissionStatus
    active: bool
    terminal: bool
    detail: str
    last_command: str
    current_waypoint_index: int = 0
    total_waypoints: int = 0
    samples: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "status": self.status.value,
            "active": self.active,
            "terminal": self.terminal,
            "detail": self.detail,
            "last_command": self.last_command,
            "current_waypoint_index": self.current_waypoint_index,
            "total_waypoints": self.total_waypoints,
            "samples": self.samples,
        }


class MissionRuntimeError(RuntimeError):
    def __init__(self, code: ControlPlaneErrorCode, message: str, detail: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail


class MissionRuntimeAdapter(Protocol):
    def supported_missions(self) -> set[str]:
        raise NotImplementedError

    def start(self, mission_name: str, parameters: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        raise NotImplementedError

    def abort(self, mission_name: str, reason: str = "") -> tuple[dict[str, Any], ...]:
        raise NotImplementedError

    def reset(self, mission_name: str, reason: str = "") -> tuple[dict[str, Any], ...]:
        raise NotImplementedError

    def get_status(self, mission_name: str | None = None) -> MissionRuntimeObservation:
        raise NotImplementedError


class ShellRos2MissionRuntimeAdapter:
    def __init__(
        self,
        repo_root: Path,
        *,
        telemetry_api_base_url: str = "http://127.0.0.1:8080",
        state_root: Path | None = None,
        mission_command_topic: str = "/drone/mission_command",
        mission_command_type: str = "drone_msgs/msg/MissionCommand",
        command_timeout_s: float = 15.0,
    ) -> None:
        self._repo_root = repo_root
        self._telemetry_api_base_url = telemetry_api_base_url.rstrip("/")
        self._state_root = state_root or repo_root / ".sim-runtime" / "control-api-missions"
        self._state_root.mkdir(parents=True, exist_ok=True)
        self._state_file = self._state_root / "mission-status-cache.json"
        self._mission_command_topic = mission_command_topic
        self._mission_command_type = mission_command_type
        self._command_timeout_s = command_timeout_s
        self._supported_mission_contracts = {
            "patrol_basic": repo_root / "simulation" / "scenarios" / "patrol_basic.json",
        }

    def supported_missions(self) -> set[str]:
        return {
            mission_name
            for mission_name, mission_contract in self._supported_mission_contracts.items()
            if mission_contract.exists()
        }

    def start(self, mission_name: str, parameters: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        _ = parameters
        self._require_supported(mission_name)
        command = "start_patrol" if mission_name == "patrol_basic" else "start"
        self._publish_command(command)
        observation = MissionRuntimeObservation(
            mission_id=mission_name,
            status=MissionStatus.ARMING,
            active=True,
            terminal=False,
            detail=f"{mission_name} start requested through ROS 2 mission adapter",
            last_command=command,
            samples=max(self._cached_observation(mission_name).samples + 1, 1),
        )
        self._save_observation(observation)
        return self._artifacts(mission_name, command)

    def abort(self, mission_name: str, reason: str = "") -> tuple[dict[str, Any], ...]:
        self._require_supported(mission_name)
        self._publish_command("abort")
        detail = reason or f"{mission_name} abort requested through ROS 2 mission adapter"
        current = self.get_status(mission_name)
        observation = MissionRuntimeObservation(
            mission_id=mission_name,
            status=MissionStatus.ABORTING,
            active=True,
            terminal=False,
            detail=detail,
            last_command="abort",
            current_waypoint_index=current.current_waypoint_index,
            total_waypoints=current.total_waypoints,
            samples=max(current.samples + 1, 1),
        )
        self._save_observation(observation)
        return self._artifacts(mission_name, "abort")

    def reset(self, mission_name: str, reason: str = "") -> tuple[dict[str, Any], ...]:
        self._require_supported(mission_name)
        self._publish_command("reset")
        observation = MissionRuntimeObservation(
            mission_id=mission_name,
            status=MissionStatus.IDLE,
            active=False,
            terminal=False,
            detail=reason or "mission reset requested through ROS 2 mission adapter",
            last_command="reset",
            samples=max(self._cached_observation(mission_name).samples + 1, 1),
        )
        self._save_observation(observation)
        return self._artifacts(mission_name, "reset")

    def get_status(self, mission_name: str | None = None) -> MissionRuntimeObservation:
        effective_mission_name = mission_name or "patrol_basic"
        if effective_mission_name in self.supported_missions():
            snapshot = self._fetch_snapshot()
            observation = self._observation_from_snapshot(snapshot, effective_mission_name)
            if observation is not None:
                self._save_observation(observation)
                return observation
        return self._cached_observation(effective_mission_name)

    def _fetch_snapshot(self) -> dict[str, Any] | None:
        url = f"{self._telemetry_api_base_url}/api/v1/snapshot"
        try:
            with urlopen(url, timeout=3.0) as response:  # noqa: S310
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            return None

    def _observation_from_snapshot(
        self,
        snapshot: dict[str, Any] | None,
        mission_name: str,
    ) -> MissionRuntimeObservation | None:
        if not snapshot:
            return None

        raw = snapshot.get("mission_status")
        if not isinstance(raw, dict):
            return None

        mission_id = str(raw.get("mission_id") or mission_name)
        phase = str(raw.get("phase") or "idle")
        return MissionRuntimeObservation(
            mission_id=mission_id,
            status=self._map_phase_to_status(phase),
            active=bool(raw.get("active", False)),
            terminal=bool(raw.get("terminal", phase in {"completed", "aborted", "failed"})),
            detail=str(raw.get("detail", "")),
            last_command=str(raw.get("last_command", "")),
            current_waypoint_index=int(raw.get("current_waypoint_index", 0)),
            total_waypoints=int(raw.get("total_waypoints", 0)),
            samples=max(self._cached_observation(mission_name).samples + 1, 1),
        )

    def _map_phase_to_status(self, phase: str) -> MissionStatus:
        normalized_phase = phase.strip().lower().replace("-", "_").replace(" ", "_")
        mapping = {
            "idle": MissionStatus.IDLE,
            "waiting_for_system": MissionStatus.ARMING,
            "arming": MissionStatus.ARMING,
            "takeoff": MissionStatus.TAKEOFF,
            "hover": MissionStatus.HOVER,
            "patrol": MissionStatus.PATROL,
            "return_to_home": MissionStatus.RETURNING,
            "returning": MissionStatus.RETURNING,
            "landing": MissionStatus.LANDING,
            "aborting": MissionStatus.ABORTING,
            "completed": MissionStatus.COMPLETED,
            "aborted": MissionStatus.ABORTED,
            "failed": MissionStatus.FAILED,
        }
        return mapping.get(normalized_phase, MissionStatus.FAILED)

    def _publish_command(self, command: str) -> None:
        message = f"{{stamp: {{sec: 0, nanosec: 0}}, command: '{command}'}}"
        ros_setup = Path("/opt/ros/humble/setup.bash")
        workspace_setup = self._repo_root / "robotics" / "ros2_ws" / "install" / "setup.bash"
        shell_lines = ["set -e"]
        if ros_setup.exists():
            shell_lines.append(f"source {shlex.quote(str(ros_setup))}")
        if workspace_setup.exists():
            shell_lines.append(f"source {shlex.quote(str(workspace_setup))}")
        shell_lines.append(
            "command -v ros2 >/dev/null 2>&1 || "
            "(echo 'ros2 CLI is not available for mission control' >&2; exit 127)"
        )
        shell_lines.append(
            "ros2 topic pub --once "
            f"{shlex.quote(self._mission_command_topic)} "
            f"{shlex.quote(self._mission_command_type)} "
            f"{shlex.quote(message)}"
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
            raise MissionRuntimeError(
                ControlPlaneErrorCode.TIMEOUT,
                f"mission command {command} timed out",
                detail=str(exc),
            ) from exc
        except OSError as exc:
            raise MissionRuntimeError(
                ControlPlaneErrorCode.DEPENDENCY_UNAVAILABLE,
                f"mission command {command} could not be executed",
                detail=str(exc),
            ) from exc

        if completed.returncode != 0:
            detail = "\n".join(part for part in [completed.stdout.strip(), completed.stderr.strip()] if part).strip()
            raise MissionRuntimeError(
                ControlPlaneErrorCode.DEPENDENCY_UNAVAILABLE,
                f"mission command {command} failed",
                detail=detail or "ros2 topic pub returned a non-zero exit code",
            )

    def _require_supported(self, mission_name: str) -> None:
        if mission_name not in self.supported_missions():
            raise MissionRuntimeError(
                ControlPlaneErrorCode.NOT_SUPPORTED,
                f"{mission_name} is not materialized by the current mission runtime",
                detail="only patrol_basic is materialized in the Mark 1 mission surface",
            )

    def _cached_observation(self, mission_name: str) -> MissionRuntimeObservation:
        payload = self._load_cache().get(mission_name)
        if not isinstance(payload, dict):
            return MissionRuntimeObservation(
                mission_id=mission_name,
                status=MissionStatus.IDLE,
                active=False,
                terminal=False,
                detail="mission idle",
                last_command="",
                samples=0,
            )

        return MissionRuntimeObservation(
            mission_id=str(payload.get("mission_id", mission_name)),
            status=MissionStatus(str(payload.get("status", MissionStatus.IDLE.value))),
            active=bool(payload.get("active", False)),
            terminal=bool(payload.get("terminal", False)),
            detail=str(payload.get("detail", "mission idle")),
            last_command=str(payload.get("last_command", "")),
            current_waypoint_index=int(payload.get("current_waypoint_index", 0)),
            total_waypoints=int(payload.get("total_waypoints", 0)),
            samples=int(payload.get("samples", 0)),
        )

    def _save_observation(self, observation: MissionRuntimeObservation) -> None:
        payload = self._load_cache()
        payload[observation.mission_id] = observation.to_dict()
        self._state_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _load_cache(self) -> dict[str, Any]:
        if not self._state_file.exists():
            return {}
        try:
            return json.loads(self._state_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _artifacts(self, mission_name: str, command: str) -> tuple[dict[str, Any], ...]:
        mission_contract = self._supported_mission_contracts[mission_name]
        return (
            {
                "artifact_type": "mission_command",
                "uri": f"ros2://topic{self._mission_command_topic}?command={command}",
                "description": f"{mission_name} control-plane command forwarded to ROS 2",
            },
            {
                "artifact_type": "mission_contract",
                "uri": str(mission_contract),
                "description": f"{mission_name} contract used by the mission runtime",
            },
            {
                "artifact_type": "mission_status_cache",
                "uri": str(self._state_file),
                "description": "latest mission runtime observation cached by the control plane",
            },
        )
