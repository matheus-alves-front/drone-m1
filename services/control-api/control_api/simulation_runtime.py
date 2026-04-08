from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
from typing import Protocol

from control_plane.domain import (
    ControlPlaneErrorCode,
    SessionMode,
    SimulationComponent,
    SimulationSessionStatus,
)


@dataclass(frozen=True)
class SimulationRuntimePaths:
    session_id: str
    runtime_dir: Path
    log_dir: Path
    px4_pid_file: Path
    xrce_pid_file: Path


@dataclass(frozen=True)
class SimulationRuntimeInspection:
    status: SimulationSessionStatus
    components: tuple[SimulationComponent, ...]
    detail: str
    runtime_ready: bool


class SimulationRuntimeError(RuntimeError):
    def __init__(self, code: ControlPlaneErrorCode, message: str, detail: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail


class SimulationRuntimeAdapter(Protocol):
    def paths_for(self, session_id: str) -> SimulationRuntimePaths:
        raise NotImplementedError

    def check(self, session_id: str, mode: SessionMode) -> None:
        raise NotImplementedError

    def start(self, session_id: str, mode: SessionMode) -> SimulationRuntimePaths:
        raise NotImplementedError

    def stop(self, session_id: str, mode: SessionMode) -> SimulationRuntimePaths:
        raise NotImplementedError

    def inspect(
        self,
        session_id: str,
        mode: SessionMode,
        current_status: SimulationSessionStatus,
    ) -> SimulationRuntimeInspection:
        raise NotImplementedError


class ShellSimulationRuntimeAdapter:
    def __init__(
        self,
        repo_root: Path,
        *,
        runtime_root: Path | None = None,
        log_root: Path | None = None,
        start_script: Path | None = None,
        stop_script: Path | None = None,
        start_timeout_s: float = 900.0,
        stop_timeout_s: float = 60.0,
        preflight_timeout_s: float = 30.0,
    ) -> None:
        self._repo_root = repo_root
        self._runtime_root = runtime_root or repo_root / ".sim-runtime" / "control-api"
        self._log_root = log_root or repo_root / ".sim-logs" / "control-api"
        self._start_script = start_script or repo_root / "scripts" / "sim" / "start.sh"
        self._stop_script = stop_script or repo_root / "scripts" / "sim" / "stop.sh"
        self._start_timeout_s = start_timeout_s
        self._stop_timeout_s = stop_timeout_s
        self._preflight_timeout_s = preflight_timeout_s

    def paths_for(self, session_id: str) -> SimulationRuntimePaths:
        runtime_dir = self._runtime_root / session_id
        log_dir = self._log_root / session_id
        return SimulationRuntimePaths(
            session_id=session_id,
            runtime_dir=runtime_dir,
            log_dir=log_dir,
            px4_pid_file=runtime_dir / "px4_sitl.pid",
            xrce_pid_file=runtime_dir / "microxrce_agent.pid",
        )

    def check(self, session_id: str, mode: SessionMode) -> None:
        paths = self.paths_for(session_id)
        self._run_script(
            self._start_script,
            ["--check"],
            paths=paths,
            mode=mode,
            timeout_s=self._preflight_timeout_s,
            error_code=ControlPlaneErrorCode.DEPENDENCY_UNAVAILABLE,
            action_label="simulation preflight",
        )
        self._run_script(
            self._stop_script,
            ["--check"],
            paths=paths,
            mode=mode,
            timeout_s=self._preflight_timeout_s,
            error_code=ControlPlaneErrorCode.DEPENDENCY_UNAVAILABLE,
            action_label="simulation stop contract preflight",
        )

    def start(self, session_id: str, mode: SessionMode) -> SimulationRuntimePaths:
        paths = self.paths_for(session_id)
        self._run_script(
            self._start_script,
            [],
            paths=paths,
            mode=mode,
            timeout_s=self._start_timeout_s,
            error_code=ControlPlaneErrorCode.RUNTIME_FAILURE,
            action_label="simulation start",
        )
        return paths

    def stop(self, session_id: str, mode: SessionMode) -> SimulationRuntimePaths:
        paths = self.paths_for(session_id)
        self._run_script(
            self._stop_script,
            [],
            paths=paths,
            mode=mode,
            timeout_s=self._stop_timeout_s,
            error_code=ControlPlaneErrorCode.RUNTIME_FAILURE,
            action_label="simulation stop",
        )
        return paths

    def inspect(
        self,
        session_id: str,
        mode: SessionMode,
        current_status: SimulationSessionStatus,
    ) -> SimulationRuntimeInspection:
        paths = self.paths_for(session_id)
        px4_pid = self._resolve_px4_pid(paths)
        xrce_pid = self._resolve_xrce_pid(paths)
        px4_alive = px4_pid is not None
        xrce_alive = xrce_pid is not None

        if px4_alive and xrce_alive:
            status = SimulationSessionStatus.ACTIVE
            detail = "PX4 SITL and Micro XRCE-DDS agent are alive."
        elif px4_alive or xrce_alive:
            status = SimulationSessionStatus.DEGRADED
            detail = "Only part of the simulation runtime is alive."
        elif current_status == SimulationSessionStatus.STOPPING:
            status = SimulationSessionStatus.STOPPED
            detail = "Runtime stopped after the stop action."
        elif current_status in {
            SimulationSessionStatus.STARTING,
            SimulationSessionStatus.ACTIVE,
            SimulationSessionStatus.DEGRADED,
        }:
            status = SimulationSessionStatus.FAILED
            detail = "Runtime processes are no longer alive."
        elif paths.runtime_dir.exists() or paths.log_dir.exists():
            status = SimulationSessionStatus.STOPPED
            detail = "Runtime artifacts exist but no process is alive."
        else:
            status = SimulationSessionStatus.IDLE
            detail = "Runtime has not been started by the control plane."

        components = (
            SimulationComponent(
                component_name="px4_sitl",
                component_type="process",
                status="active" if px4_alive else "inactive",
                health_summary=self._health_summary(paths.px4_pid_file, px4_pid),
            ),
            SimulationComponent(
                component_name="micro_xrce_agent",
                component_type="process",
                status="active" if xrce_alive else "inactive",
                health_summary=self._health_summary(paths.xrce_pid_file, xrce_pid),
            ),
            SimulationComponent(
                component_name="runtime_paths",
                component_type="filesystem",
                status="ready" if paths.runtime_dir.exists() or paths.log_dir.exists() else "idle",
                health_summary=f"runtime_dir={paths.runtime_dir}; log_dir={paths.log_dir}; mode={mode.value}",
            ),
        )

        return SimulationRuntimeInspection(
            status=status,
            components=components,
            detail=detail,
            runtime_ready=px4_alive and xrce_alive,
        )

    def _run_script(
        self,
        script: Path,
        args: list[str],
        *,
        paths: SimulationRuntimePaths,
        mode: SessionMode,
        timeout_s: float,
        error_code: ControlPlaneErrorCode,
        action_label: str,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(
            {
                "PHASE1_RUNTIME_DIR": str(paths.runtime_dir),
                "PHASE1_LOG_DIR": str(paths.log_dir),
                "PHASE1_HEADLESS": "1" if mode == SessionMode.HEADLESS else "0",
                "PHASE1_GZ_PARTITION": f"control-api-{paths.session_id}",
            }
        )
        paths.runtime_dir.mkdir(parents=True, exist_ok=True)
        paths.log_dir.mkdir(parents=True, exist_ok=True)

        try:
            completed = subprocess.run(
                ["bash", str(script), *args],
                cwd=self._repo_root,
                capture_output=True,
                text=True,
                env=env,
                timeout=timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise SimulationRuntimeError(
                ControlPlaneErrorCode.TIMEOUT,
                f"{action_label} timed out",
                detail=str(exc),
            ) from exc

        if completed.returncode != 0:
            detail = "\n".join(part for part in [completed.stdout.strip(), completed.stderr.strip()] if part).strip()
            raise SimulationRuntimeError(
                error_code,
                f"{action_label} failed",
                detail=detail,
            )

        return completed

    def _health_summary(self, pid_file: Path, pid: int | None) -> str:
        if pid is None:
            return f"pid_file={pid_file}"
        return f"pid_file={pid_file}; pid={pid}"

    def _resolve_px4_pid(self, paths: SimulationRuntimePaths) -> int | None:
        px4_binary = self._repo_root / "third_party" / "PX4-Autopilot" / "build" / "px4_sitl_default" / "bin" / "px4"
        return self._resolve_process_pid(paths.px4_pid_file, str(px4_binary))

    def _resolve_xrce_pid(self, paths: SimulationRuntimePaths) -> int | None:
        return self._resolve_process_pid(paths.xrce_pid_file, "MicroXRCEAgent")

    def _resolve_process_pid(self, pid_file: Path, command_fragment: str) -> int | None:
        pid = self._read_pid_file(pid_file)
        if pid is not None and self._pid_exists(pid):
            return pid

        fallback_pid = self._find_process_pid(command_fragment)
        if fallback_pid is None:
            return None

        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(f"{fallback_pid}\n", encoding="utf-8")
        return fallback_pid

    def _find_process_pid(self, command_fragment: str) -> int | None:
        completed = subprocess.run(
            ["ps", "-eo", "pid=,args="],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            return None

        matches: list[int] = []
        for line in completed.stdout.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            try:
                raw_pid, command = stripped.split(None, 1)
            except ValueError:
                continue
            if command_fragment not in command:
                continue
            try:
                matches.append(int(raw_pid))
            except ValueError:
                continue

        if not matches:
            return None
        return max(matches)

    def _read_pid_file(self, pid_file: Path) -> int | None:
        if not pid_file.exists():
            return None

        try:
            return int(pid_file.read_text(encoding="utf-8").strip())
        except ValueError:
            return None

    def _pid_exists(self, pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True

    def _pid_alive(self, pid_file: Path) -> bool:
        pid = self._read_pid_file(pid_file)
        if pid is None:
            return False
        return self._pid_exists(pid)
