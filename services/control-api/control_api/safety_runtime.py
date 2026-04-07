from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import shlex
import subprocess
import uuid
from typing import Any, Protocol

from control_plane.domain import ControlPlaneErrorCode, SafetyFaultRecord


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class SafetyCommandDispatch:
    action_name: str
    fault_type: str
    artifacts: tuple[dict[str, Any], ...]


class SafetyRuntimeError(RuntimeError):
    def __init__(self, code: ControlPlaneErrorCode, message: str, detail: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail


class SafetyRuntimeAdapter(Protocol):
    def inject_fault(self, fault_type: str, *, value: float = 0.0, detail: str = "") -> SafetyCommandDispatch:
        raise NotImplementedError

    def clear_fault(self, fault_type: str) -> SafetyCommandDispatch:
        raise NotImplementedError

    def active_faults(self) -> tuple[SafetyFaultRecord, ...]:
        raise NotImplementedError


class ShellRos2SafetyRuntimeAdapter:
    def __init__(
        self,
        repo_root: Path,
        *,
        state_root: Path | None = None,
        fault_topic: str = "/drone/safety_fault",
        fault_type_name: str = "drone_msgs/msg/SafetyFault",
        command_timeout_s: float = 15.0,
    ) -> None:
        self._repo_root = repo_root
        self._state_root = state_root or repo_root / ".sim-runtime" / "control-api-safety"
        self._state_root.mkdir(parents=True, exist_ok=True)
        self._logs_root = self._state_root / "commands"
        self._logs_root.mkdir(parents=True, exist_ok=True)
        self._active_faults_file = self._state_root / "active-faults.json"
        self._fault_topic = fault_topic
        self._fault_type_name = fault_type_name
        self._command_timeout_s = command_timeout_s

    def inject_fault(self, fault_type: str, *, value: float = 0.0, detail: str = "") -> SafetyCommandDispatch:
        normalized_fault = self._normalize_fault_type(fault_type)
        artifacts = self._publish_fault(normalized_fault, active=True, value=value, detail=detail)
        active_faults = {item.fault_type: item for item in self.active_faults()}
        active_faults[normalized_fault] = SafetyFaultRecord(
            fault_type=normalized_fault,
            active=True,
            value=value,
            detail=detail,
            source="operator",
            raised_at=_now_iso(),
        )
        self._save_faults(tuple(active_faults.values()))
        return SafetyCommandDispatch(
            action_name="safety.inject_fault",
            fault_type=normalized_fault,
            artifacts=artifacts,
        )

    def clear_fault(self, fault_type: str) -> SafetyCommandDispatch:
        normalized_fault = self._normalize_fault_type(fault_type)
        artifacts = self._publish_fault(normalized_fault, active=False, value=0.0, detail="")
        active_faults = {item.fault_type: item for item in self.active_faults()}
        active_faults.pop(normalized_fault, None)
        self._save_faults(tuple(active_faults.values()))
        return SafetyCommandDispatch(
            action_name="safety.clear_fault",
            fault_type=normalized_fault,
            artifacts=artifacts,
        )

    def active_faults(self) -> tuple[SafetyFaultRecord, ...]:
        if not self._active_faults_file.exists():
            return ()
        payload = json.loads(self._active_faults_file.read_text(encoding="utf-8"))
        return tuple(
            SafetyFaultRecord(
                fault_type=str(item["fault_type"]),
                active=bool(item.get("active", True)),
                value=float(item.get("value", 0.0)),
                detail=str(item.get("detail", "")),
                source=str(item.get("source", "operator")),
                raised_at=item.get("raised_at"),
                cleared_at=item.get("cleared_at"),
            )
            for item in payload
        )

    def _publish_fault(
        self,
        fault_type: str,
        *,
        active: bool,
        value: float,
        detail: str,
    ) -> tuple[dict[str, Any], ...]:
        log_path = self._logs_root / f"{fault_type}-{'inject' if active else 'clear'}-{uuid.uuid4().hex[:12]}.log"
        ros_setup = Path("/opt/ros/humble/setup.bash")
        workspace_setup = self._repo_root / "robotics" / "ros2_ws" / "install" / "setup.bash"
        message = (
            "{stamp: {sec: 0, nanosec: 0}, "
            f"fault_type: \"{fault_type}\", "
            f"active: {'true' if active else 'false'}, "
            f"value: {float(value)}, "
            f"detail: \"{detail}\"}}"
        )
        shell_lines = ["set -e"]
        if ros_setup.exists():
            shell_lines.append(f"source {shlex.quote(str(ros_setup))}")
        if workspace_setup.exists():
            shell_lines.append(f"source {shlex.quote(str(workspace_setup))}")
        shell_lines.append(
            "command -v ros2 >/dev/null 2>&1 || "
            "(echo 'ros2 CLI is not available for safety control' >&2; exit 127)"
        )
        shell_lines.append(
            "ros2 topic pub --once "
            f"{shlex.quote(self._fault_topic)} "
            f"{shlex.quote(self._fault_type_name)} "
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
            raise SafetyRuntimeError(
                ControlPlaneErrorCode.TIMEOUT,
                f"safety fault command for {fault_type} timed out",
                detail=str(exc),
            ) from exc

        log_body = "\n".join(
            part
            for part in [
                f"fault_type={fault_type}",
                f"active={active}",
                f"topic={self._fault_topic}",
                completed.stdout.strip(),
                completed.stderr.strip(),
            ]
            if part
        )
        log_path.write_text(log_body + "\n", encoding="utf-8")
        if completed.returncode != 0:
            raise SafetyRuntimeError(
                ControlPlaneErrorCode.DEPENDENCY_UNAVAILABLE,
                f"safety fault command for {fault_type} failed",
                detail=log_body,
            )
        return (
            {
                "artifact_type": "safety_fault_log",
                "uri": str(log_path),
                "description": f"{fault_type} safety fault dispatch log",
            },
        )

    def _save_faults(self, active_faults: tuple[SafetyFaultRecord, ...]) -> None:
        payload = [
            {
                "fault_type": item.fault_type,
                "active": item.active,
                "value": item.value,
                "detail": item.detail,
                "source": item.source,
                "raised_at": item.raised_at,
                "cleared_at": item.cleared_at,
            }
            for item in active_faults
        ]
        self._active_faults_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _normalize_fault_type(self, fault_type: str) -> str:
        normalized = fault_type.strip().lower().replace("-", "_").replace(" ", "_")
        if not normalized:
            raise SafetyRuntimeError(
                ControlPlaneErrorCode.INVALID_REQUEST,
                "fault_type is required",
                detail="use one of the supported safety fault identifiers such as gps_loss or rc_loss",
            )
        return normalized
