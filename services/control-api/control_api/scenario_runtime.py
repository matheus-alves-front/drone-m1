from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import time
from typing import Any, Protocol

from control_plane.domain import ControlPlaneErrorCode, RunStatus


@dataclass(frozen=True)
class ScenarioRunPaths:
    run_id: str
    workspace_dir: Path
    launcher_script: Path
    pid_file: Path
    result_file: Path
    stderr_file: Path
    exit_code_file: Path
    cancelled_file: Path


@dataclass(frozen=True)
class ScenarioRuntimeInspection:
    status: RunStatus
    summary: str
    artifacts: tuple[dict[str, Any], ...]
    result_payload: dict[str, Any] | None = None


@dataclass(frozen=True)
class ScenarioRuntimeLaunch:
    process_id: int | None
    result_path: Path
    log_path: Path
    artifacts: tuple[dict[str, Any], ...]


class ScenarioRuntimeError(RuntimeError):
    def __init__(self, code: ControlPlaneErrorCode, message: str, detail: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail


class ScenarioRuntimeAdapter(Protocol):
    def supported_scenarios(self) -> set[str]:
        raise NotImplementedError

    def supports_run(self, scenario_name: str) -> bool:
        raise NotImplementedError

    def paths_for(self, run_id: str) -> ScenarioRunPaths:
        raise NotImplementedError

    def start(
        self,
        *,
        scenario_name: str,
        run_id: str,
        scenario_contract_path: str | None = None,
        parameters: dict[str, Any],
    ) -> ScenarioRuntimeLaunch:
        raise NotImplementedError

    def inspect(self, *, scenario_name: str, run_id: str) -> ScenarioRuntimeInspection:
        raise NotImplementedError

    def cancel(
        self,
        *,
        scenario_name: str,
        run_id: str | None = None,
        process_id: int | None = None,
        result_path: str | None = None,
        log_path: str | None = None,
    ) -> ScenarioRuntimeInspection:
        raise NotImplementedError


class ShellScenarioRuntimeAdapter:
    def __init__(
        self,
        repo_root: Path,
        *,
        state_root: Path | None = None,
    ) -> None:
        self._repo_root = repo_root
        self._state_root = state_root or repo_root / ".sim-runtime" / "control-api-scenarios"
        self._runner_script = repo_root / "scripts" / "scenarios" / "run_scenario.sh"
        self._supported_scenarios = {"takeoff_land"}

    def supported_scenarios(self) -> set[str]:
        return set(self._supported_scenarios)

    def supports_run(self, scenario_name: str) -> bool:
        return scenario_name in self._supported_scenarios

    def paths_for(self, run_id: str) -> ScenarioRunPaths:
        workspace_dir = self._state_root / run_id
        return ScenarioRunPaths(
            run_id=run_id,
            workspace_dir=workspace_dir,
            launcher_script=workspace_dir / "launch.sh",
            pid_file=workspace_dir / "scenario.pid",
            result_file=workspace_dir / "result.json",
            stderr_file=workspace_dir / "stderr.log",
            exit_code_file=workspace_dir / "exit_code.txt",
            cancelled_file=workspace_dir / "cancelled.flag",
        )

    def start(
        self,
        *,
        scenario_name: str,
        run_id: str,
        scenario_contract_path: str | None = None,
        parameters: dict[str, Any],
    ) -> ScenarioRuntimeLaunch:
        if not self.supports_run(scenario_name):
            raise ScenarioRuntimeError(
                ControlPlaneErrorCode.NOT_SUPPORTED,
                f"scenario runtime is not available for {scenario_name}",
                detail="control plane does not materialize this scenario in the current phase",
            )

        paths = self.paths_for(run_id)
        paths.workspace_dir.mkdir(parents=True, exist_ok=True)
        paths.cancelled_file.unlink(missing_ok=True)
        paths.exit_code_file.unlink(missing_ok=True)

        scenario_file = Path(scenario_contract_path) if scenario_contract_path else self._repo_root / "simulation" / "scenarios" / f"{scenario_name}.json"
        if not scenario_file.exists():
            raise ScenarioRuntimeError(
                ControlPlaneErrorCode.INVALID_REQUEST,
                f"scenario contract missing for {scenario_name}",
                detail=str(scenario_file),
            )

        command = [
            "bash",
            str(self._runner_script),
            str(scenario_file),
            "--output",
            "json",
        ]
        if parameters.get("backend"):
            command.extend(["--backend", str(parameters["backend"])])
        if parameters.get("system_address"):
            command.extend(["--system-address", str(parameters["system_address"])])

        launcher_body = "\n".join(
            [
                "#!/usr/bin/env bash",
                "set +e",
                f"echo $$ > {shlex.quote(str(paths.pid_file))}",
                f"{shlex.join(command)} > {shlex.quote(str(paths.result_file))} 2> {shlex.quote(str(paths.stderr_file))}",
                "status=$?",
                f"printf '%s' \"$status\" > {shlex.quote(str(paths.exit_code_file))}",
                "exit \"$status\"",
                "",
            ]
        )
        paths.launcher_script.write_text(launcher_body, encoding="utf-8")
        paths.launcher_script.chmod(0o755)

        try:
            subprocess.Popen(  # noqa: S603
                ["bash", str(paths.launcher_script)],
                cwd=self._repo_root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid,
            )
        except OSError as exc:
            raise ScenarioRuntimeError(
                ControlPlaneErrorCode.DEPENDENCY_UNAVAILABLE,
                "scenario runtime launcher could not be started",
                detail=str(exc),
            ) from exc

        deadline = time.time() + 5.0
        while time.time() < deadline:
            if paths.pid_file.exists():
                return ScenarioRuntimeLaunch(
                    process_id=self._read_pid(paths.pid_file),
                    result_path=paths.result_file,
                    log_path=paths.stderr_file,
                    artifacts=self._artifacts(paths),
                )
            time.sleep(0.05)

        raise ScenarioRuntimeError(
            ControlPlaneErrorCode.RUNTIME_FAILURE,
            "scenario runtime did not publish its pid file",
            detail=str(paths.pid_file),
        )

    def inspect(self, *, scenario_name: str, run_id: str) -> ScenarioRuntimeInspection:
        _ = scenario_name
        paths = self.paths_for(run_id)
        artifacts = self._artifacts(paths)

        if paths.cancelled_file.exists():
            return ScenarioRuntimeInspection(
                status=RunStatus.CANCELLED,
                summary="scenario run cancelled by control plane",
                artifacts=artifacts,
            )

        if paths.exit_code_file.exists():
            exit_code = self._read_exit_code(paths.exit_code_file)
            result_payload = self._read_result_payload(paths.result_file)
            if exit_code == 0:
                return ScenarioRuntimeInspection(
                    status=RunStatus.COMPLETED,
                    summary=(result_payload or {}).get("detail", "scenario run completed successfully"),
                    artifacts=artifacts,
                    result_payload=result_payload,
                )
            if result_payload and result_payload.get("status") == "timeout":
                return ScenarioRuntimeInspection(
                    status=RunStatus.TIMED_OUT,
                    summary=result_payload.get("detail", "scenario run timed out"),
                    artifacts=artifacts,
                    result_payload=result_payload,
                )
            return ScenarioRuntimeInspection(
                status=RunStatus.FAILED,
                summary=(result_payload or {}).get("detail", f"scenario run exited with code {exit_code}"),
                artifacts=artifacts,
                result_payload=result_payload,
            )

        if self._pid_alive(paths.pid_file):
            return ScenarioRuntimeInspection(
                status=RunStatus.RUNNING,
                summary="scenario run is active",
                artifacts=artifacts,
            )

        return ScenarioRuntimeInspection(
            status=RunStatus.FAILED,
            summary="scenario run ended without a terminal result contract",
            artifacts=artifacts,
        )

    def cancel(
        self,
        *,
        scenario_name: str,
        run_id: str | None = None,
        process_id: int | None = None,
        result_path: str | None = None,
        log_path: str | None = None,
    ) -> ScenarioRuntimeInspection:
        _ = scenario_name
        if run_id is None and result_path is None:
            raise ScenarioRuntimeError(
                ControlPlaneErrorCode.INVALID_REQUEST,
                "scenario cancellation requires run_id or result_path",
            )
        paths = self.paths_for(run_id) if run_id is not None else self._paths_from_result_path(Path(str(result_path)))
        pid = process_id if process_id is not None else self._read_pid(paths.pid_file)
        paths.cancelled_file.write_text("cancelled\n", encoding="utf-8")

        if pid is not None:
            try:
                os.killpg(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            else:
                deadline = time.time() + 5.0
                while time.time() < deadline and self._pid_alive(paths.pid_file):
                    time.sleep(0.05)
                if self._pid_alive(paths.pid_file):
                    try:
                        os.killpg(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass

        return ScenarioRuntimeInspection(
            status=RunStatus.CANCELLED,
            summary="scenario run cancelled by control plane",
            artifacts=self._artifacts(paths),
        )

    def _paths_from_result_path(self, result_file: Path) -> ScenarioRunPaths:
        workspace_dir = result_file.parent
        run_id = workspace_dir.name
        return ScenarioRunPaths(
            run_id=run_id,
            workspace_dir=workspace_dir,
            launcher_script=workspace_dir / "launch.sh",
            pid_file=workspace_dir / "scenario.pid",
            result_file=result_file,
            stderr_file=workspace_dir / "stderr.log",
            exit_code_file=workspace_dir / "exit_code.txt",
            cancelled_file=workspace_dir / "cancelled.flag",
        )

    def _artifacts(self, paths: ScenarioRunPaths) -> tuple[dict[str, Any], ...]:
        return (
            {"artifact_type": "scenario_workspace", "uri": str(paths.workspace_dir)},
            {"artifact_type": "pid_file", "uri": str(paths.pid_file)},
            {"artifact_type": "result_file", "uri": str(paths.result_file)},
            {"artifact_type": "stderr_log", "uri": str(paths.stderr_file)},
            {"artifact_type": "exit_code_file", "uri": str(paths.exit_code_file)},
        )

    def _read_pid(self, pid_file: Path) -> int | None:
        if not pid_file.exists():
            return None
        try:
            return int(pid_file.read_text(encoding="utf-8").strip())
        except ValueError:
            return None

    def _pid_alive(self, pid_file: Path) -> bool:
        pid = self._read_pid(pid_file)
        if pid is None:
            return False
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True

    def _read_exit_code(self, exit_code_file: Path) -> int:
        try:
            return int(exit_code_file.read_text(encoding="utf-8").strip())
        except ValueError:
            return 1

    def _read_result_payload(self, result_file: Path) -> dict[str, Any] | None:
        if not result_file.exists():
            return None
        try:
            return json.loads(result_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
