from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import threading
from typing import Any

from control_plane.domain import (
    RunRecord,
    RunStatus,
    SessionMode,
    SimulationComponent,
    SimulationEnvironment,
    SimulationSession,
    SimulationSessionStatus,
)


@dataclass(frozen=True)
class ScenarioState:
    scenario_name: str
    executor_type: str
    status: str | None = None
    active_run_id: str | None = None
    last_run_id: str | None = None
    process_id: int | None = None
    result_path: str | None = None
    log_path: str | None = None
    summary: str = ""
    started_at: str | None = None
    ended_at: str | None = None
    cancel_requested: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_name": self.scenario_name,
            "executor_type": self.executor_type,
            "status": self.status,
            "active_run_id": self.active_run_id,
            "last_run_id": self.last_run_id,
            "process_id": self.process_id,
            "result_path": self.result_path,
            "log_path": self.log_path,
            "summary": self.summary,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "cancel_requested": self.cancel_requested,
        }


@dataclass(frozen=True)
class MissionState:
    mission_id: str
    mission_type: str = "patrol"
    status: str = "idle"
    active_run_id: str | None = None
    last_run_id: str | None = None
    summary: str = "mission idle"
    last_command: str = ""
    current_waypoint_index: int = 0
    total_waypoints: int = 0
    started_at: str | None = None
    ended_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "mission_type": self.mission_type,
            "status": self.status,
            "active_run_id": self.active_run_id,
            "last_run_id": self.last_run_id,
            "summary": self.summary,
            "last_command": self.last_command,
            "current_waypoint_index": self.current_waypoint_index,
            "total_waypoints": self.total_waypoints,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
        }


def _default_environment() -> SimulationEnvironment:
    return SimulationEnvironment(
        environment_name="mark1-local-sim",
        simulator_family="px4-gazebo-harmonic",
        vehicle_profile="x500",
        baseline="ubuntu-22.04-ros2-humble",
    )


def _default_session() -> SimulationSession:
    return SimulationSession(
        session_id="session-local-default",
        status=SimulationSessionStatus.IDLE,
        mode=SessionMode.HEADLESS,
        environment=_default_environment(),
        components=(
            SimulationComponent(
                component_name="simulation_runtime",
                component_type="session",
                status="idle",
                health_summary="runtime not started by control plane yet",
            ),
            SimulationComponent(
                component_name="read_model",
                component_type="telemetry_api",
                status="external",
                health_summary="served through read model adapter",
            ),
        ),
    )


def _session_from_dict(payload: dict[str, Any]) -> SimulationSession:
    return SimulationSession(
        session_id=payload["session_id"],
        status=SimulationSessionStatus(payload["status"]),
        mode=SessionMode(payload["mode"]),
        environment=SimulationEnvironment(**payload["environment"]),
        components=tuple(SimulationComponent(**component) for component in payload["components"]),
        started_at=payload.get("started_at"),
        stopped_at=payload.get("stopped_at"),
    )


def _run_from_dict(payload: dict[str, Any]) -> RunRecord:
    return RunRecord(
        run_id=payload["run_id"],
        run_kind=payload["run_kind"],
        name=payload["name"],
        status=RunStatus(payload["status"]),
        session_id=payload.get("session_id"),
        started_at=payload.get("started_at"),
        ended_at=payload.get("ended_at"),
        artifacts=tuple(payload.get("artifacts", [])),
        summary=payload.get("summary", ""),
    )


def _scenario_state_from_dict(payload: dict[str, Any]) -> ScenarioState:
    return ScenarioState(
        scenario_name=payload["scenario_name"],
        executor_type=payload["executor_type"],
        status=payload.get("status"),
        active_run_id=payload.get("active_run_id"),
        last_run_id=payload.get("last_run_id"),
        process_id=payload.get("process_id"),
        result_path=payload.get("result_path"),
        log_path=payload.get("log_path"),
        summary=payload.get("summary", ""),
        started_at=payload.get("started_at"),
        ended_at=payload.get("ended_at"),
        cancel_requested=bool(payload.get("cancel_requested", False)),
    )


def _mission_state_from_dict(payload: dict[str, Any]) -> MissionState:
    return MissionState(
        mission_id=payload["mission_id"],
        mission_type=payload.get("mission_type", "patrol"),
        status=payload.get("status", "idle"),
        active_run_id=payload.get("active_run_id"),
        last_run_id=payload.get("last_run_id"),
        summary=payload.get("summary", "mission idle"),
        last_command=payload.get("last_command", ""),
        current_waypoint_index=int(payload.get("current_waypoint_index", 0)),
        total_waypoints=int(payload.get("total_waypoints", 0)),
        started_at=payload.get("started_at"),
        ended_at=payload.get("ended_at"),
    )


class SessionStore:
    def __init__(self, state_file: Path) -> None:
        self._lock = threading.RLock()
        self._state_file = state_file
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        self._session = self._load()

    def current(self) -> SimulationSession:
        with self._lock:
            return self._session

    def replace(self, session: SimulationSession) -> SimulationSession:
        with self._lock:
            self._session = session
            self._save()
            return self._session

    def _load(self) -> SimulationSession:
        if not self._state_file.exists():
            return _default_session()

        payload = json.loads(self._state_file.read_text(encoding="utf-8"))
        return _session_from_dict(payload)

    def _save(self) -> None:
        self._state_file.write_text(json.dumps(self._session.to_dict(), indent=2), encoding="utf-8")


class RunStore:
    def __init__(self, state_file: Path) -> None:
        self._lock = threading.RLock()
        self._state_file = state_file
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        self._runs = self._load()

    def list_runs(self) -> list[RunRecord]:
        with self._lock:
            return list(self._runs.values())

    def get(self, run_id: str) -> RunRecord | None:
        with self._lock:
            return self._runs.get(run_id)

    def upsert(self, run: RunRecord) -> RunRecord:
        with self._lock:
            self._runs[run.run_id] = run
            self._save()
            return run

    def active_run(self) -> RunRecord | None:
        with self._lock:
            for run in reversed(list(self._runs.values())):
                if run.status in {RunStatus.QUEUED, RunStatus.STARTING, RunStatus.RUNNING}:
                    return run
        return None

    def summary(self) -> dict[str, object]:
        active_run = self.active_run()
        return {
            "run_count": len(self.list_runs()),
            "active_run": active_run.to_dict() if active_run else None,
        }

    def _load(self) -> dict[str, RunRecord]:
        if not self._state_file.exists():
            return {}

        payload = json.loads(self._state_file.read_text(encoding="utf-8"))
        return {item["run_id"]: _run_from_dict(item) for item in payload}

    def _save(self) -> None:
        payload = [run.to_dict() for run in self._runs.values()]
        self._state_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class ScenarioStore:
    def __init__(self, state_file: Path) -> None:
        self._lock = threading.RLock()
        self._state_file = state_file
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        self._states = self._load()

    def get(self, scenario_name: str) -> ScenarioState | None:
        with self._lock:
            return self._states.get(scenario_name)

    def list_states(self) -> list[ScenarioState]:
        with self._lock:
            return list(self._states.values())

    def active_state(self) -> ScenarioState | None:
        with self._lock:
            for state in self._states.values():
                if state.active_run_id:
                    return state
        return None

    def replace(self, state: ScenarioState) -> ScenarioState:
        with self._lock:
            self._states[state.scenario_name] = state
            self._save()
            return state

    def _load(self) -> dict[str, ScenarioState]:
        if not self._state_file.exists():
            return {}

        payload = json.loads(self._state_file.read_text(encoding="utf-8"))
        return {item["scenario_name"]: _scenario_state_from_dict(item) for item in payload}

    def _save(self) -> None:
        payload = [state.to_dict() for state in self._states.values()]
        self._state_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class MissionStore:
    def __init__(self, state_file: Path) -> None:
        self._lock = threading.RLock()
        self._state_file = state_file
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        self._state = self._load()

    def current(self) -> MissionState | None:
        with self._lock:
            return self._state

    def replace(self, state: MissionState) -> MissionState:
        with self._lock:
            self._state = state
            self._save()
            return state

    def _load(self) -> MissionState | None:
        if not self._state_file.exists():
            return None

        payload = json.loads(self._state_file.read_text(encoding="utf-8"))
        return _mission_state_from_dict(payload)

    def _save(self) -> None:
        if self._state is None:
            return
        self._state_file.write_text(json.dumps(self._state.to_dict(), indent=2), encoding="utf-8")
