from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from control_plane.domain import (
    ControlPlaneErrorCode,
    MissionStatus,
    RunStatus,
    SafetyFaultRecord,
    SessionMode,
    SimulationComponent,
    SimulationSessionStatus,
)
from control_api.app import create_app
from control_api.mission_runtime import MissionRuntimeObservation
from control_api.scenario_runtime import ScenarioRuntimeError, ScenarioRuntimeInspection, ScenarioRuntimeLaunch
from control_api.simulation_runtime import SimulationRuntimeError, SimulationRuntimeInspection, SimulationRuntimePaths


class StubReadModelAdapter:
    def __init__(self, snapshot: dict[str, Any] | None = None, *, should_fail: bool = False) -> None:
        self._snapshot = snapshot or {"current_run_id": None, "latest_by_kind": {}}
        self._metrics = {
            "run_id": self._snapshot.get("run_id"),
            "session_id": self._snapshot.get("session_id"),
            "metrics": [],
            "source": "stub_read_model",
        }
        self._events = {
            "run_id": self._snapshot.get("run_id"),
            "session_id": self._snapshot.get("session_id"),
            "events": [],
            "source": "stub_read_model",
        }
        self._runs: list[dict[str, Any]] = []
        self._replays: dict[str, dict[str, Any]] = {}
        self._should_fail = should_fail

    async def get_snapshot(self, run_id: str | None = None) -> dict[str, Any]:
        if self._should_fail:
            raise RuntimeError("telemetry api unavailable")
        if run_id is not None and self._replays.get(run_id):
            return self._replays[run_id]["snapshot"]
        return self._snapshot

    async def get_metrics(self, run_id: str | None = None, *, limit: int = 100) -> dict[str, Any]:
        if self._should_fail:
            raise RuntimeError("telemetry api unavailable")
        payload = self._replays.get(run_id, {}).get("metrics_payload") if run_id is not None else None
        resolved = dict(payload or self._metrics)
        resolved["metrics"] = list(resolved.get("metrics", []))[-limit:]
        return resolved

    async def get_events(
        self,
        run_id: str | None = None,
        *,
        kind: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        if self._should_fail:
            raise RuntimeError("telemetry api unavailable")
        payload = self._replays.get(run_id, {}).get("events_payload") if run_id is not None else None
        resolved = dict(payload or self._events)
        events = list(resolved.get("events", []))
        if kind is not None:
            events = [item for item in events if item.get("kind") == kind]
        resolved["events"] = events[-limit:]
        return resolved

    async def list_runs(self) -> list[dict[str, Any]]:
        if self._should_fail:
            raise RuntimeError("telemetry api unavailable")
        return list(self._runs)

    async def get_replay(self, run_id: str, *, limit: int = 500) -> dict[str, Any]:
        if self._should_fail:
            raise RuntimeError("telemetry api unavailable")
        replay = dict(self._replays.get(run_id, {"run_id": run_id, "snapshot": {}, "events": [], "metrics": []}))
        replay["events"] = list(replay.get("events", []))[-limit:]
        replay["metrics"] = list(replay.get("metrics", []))[-limit:]
        return replay

    def set_snapshot(self, snapshot: dict[str, Any]) -> None:
        self._snapshot = snapshot

    def set_metrics(self, metrics: dict[str, Any]) -> None:
        self._metrics = metrics

    def set_events(self, events: dict[str, Any]) -> None:
        self._events = events

    def set_runs(self, runs: list[dict[str, Any]]) -> None:
        self._runs = runs

    def set_replay(self, run_id: str, replay: dict[str, Any]) -> None:
        self._replays[run_id] = replay


class StubSimulationRuntime:
    def __init__(self, root: Path, *, fail_check: bool = False, fail_start: bool = False, fail_stop: bool = False) -> None:
        self._runtime_root = root / "runtime"
        self._log_root = root / "logs"
        self._active_session_id: str | None = None
        self._fail_check = fail_check
        self._fail_start = fail_start
        self._fail_stop = fail_stop

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
        _ = mode
        if self._fail_check:
            raise SimulationRuntimeError(
                ControlPlaneErrorCode.DEPENDENCY_UNAVAILABLE,
                "simulation preflight failed",
                detail=f"session_id={session_id}",
            )

    def start(self, session_id: str, mode: SessionMode) -> SimulationRuntimePaths:
        _ = mode
        if self._fail_start:
            raise SimulationRuntimeError(
                ControlPlaneErrorCode.RUNTIME_FAILURE,
                "simulation start failed",
                detail=f"session_id={session_id}",
            )

        paths = self.paths_for(session_id)
        paths.runtime_dir.mkdir(parents=True, exist_ok=True)
        paths.log_dir.mkdir(parents=True, exist_ok=True)
        paths.px4_pid_file.write_text("1234", encoding="utf-8")
        paths.xrce_pid_file.write_text("5678", encoding="utf-8")
        self._active_session_id = session_id
        return paths

    def stop(self, session_id: str, mode: SessionMode) -> SimulationRuntimePaths:
        _ = mode
        if self._fail_stop:
            raise SimulationRuntimeError(
                ControlPlaneErrorCode.RUNTIME_FAILURE,
                "simulation stop failed",
                detail=f"session_id={session_id}",
            )

        paths = self.paths_for(session_id)
        paths.px4_pid_file.unlink(missing_ok=True)
        paths.xrce_pid_file.unlink(missing_ok=True)
        self._active_session_id = None
        return paths

    def inspect(
        self,
        session_id: str,
        mode: SessionMode,
        current_status: SimulationSessionStatus,
    ) -> SimulationRuntimeInspection:
        paths = self.paths_for(session_id)
        active = self._active_session_id == session_id
        if active:
            status = SimulationSessionStatus.ACTIVE
            detail = "stub runtime active"
            process_status = "active"
        elif current_status == SimulationSessionStatus.STOPPING:
            status = SimulationSessionStatus.STOPPED
            detail = "stub runtime stopped"
            process_status = "inactive"
        elif current_status in {
            SimulationSessionStatus.STARTING,
            SimulationSessionStatus.ACTIVE,
            SimulationSessionStatus.DEGRADED,
        }:
            status = SimulationSessionStatus.FAILED
            detail = "stub runtime unexpectedly inactive"
            process_status = "inactive"
        else:
            status = SimulationSessionStatus.STOPPED if paths.runtime_dir.exists() else SimulationSessionStatus.IDLE
            detail = "stub runtime idle"
            process_status = "inactive"

        components = (
            SimulationComponent(
                component_name="px4_sitl",
                component_type="process",
                status=process_status,
                health_summary=f"pid_file={paths.px4_pid_file}",
            ),
            SimulationComponent(
                component_name="micro_xrce_agent",
                component_type="process",
                status=process_status,
                health_summary=f"pid_file={paths.xrce_pid_file}",
            ),
            SimulationComponent(
                component_name="runtime_paths",
                component_type="filesystem",
                status="ready",
                health_summary=f"runtime_dir={paths.runtime_dir}; log_dir={paths.log_dir}; mode={mode.value}",
            ),
        )
        return SimulationRuntimeInspection(
            status=status,
            components=components,
            detail=detail,
            runtime_ready=active,
        )


class StubScenarioRuntime:
    def __init__(self, root: Path) -> None:
        self._root = root / "scenario-runtime"
        self._runs: dict[str, dict[str, Any]] = {}

    def supported_scenarios(self) -> set[str]:
        return {"takeoff_land"}

    def start(
        self,
        *,
        scenario_name: str,
        run_id: str,
        scenario_contract_path: str | None = None,
        parameters: dict[str, Any],
    ) -> ScenarioRuntimeLaunch:
        _ = scenario_contract_path
        if scenario_name != "takeoff_land":
            raise ScenarioRuntimeError(
                ControlPlaneErrorCode.NOT_SUPPORTED,
                f"{scenario_name} is not executable in the stub scenario runtime",
            )

        work_dir = self._root / run_id
        work_dir.mkdir(parents=True, exist_ok=True)
        result_path = work_dir / "result.json"
        log_path = work_dir / "stderr.log"
        result_path.write_text("", encoding="utf-8")
        log_path.write_text("", encoding="utf-8")
        process_id = 9000 + len(self._runs)
        self._runs[run_id] = {
            "scenario_name": scenario_name,
            "status": RunStatus.RUNNING,
            "summary": "takeoff_land is running in the stub scenario runtime",
            "result_path": result_path,
            "log_path": log_path,
            "process_id": process_id,
            "parameters": dict(parameters),
        }
        return ScenarioRuntimeLaunch(
            process_id=process_id,
            result_path=result_path,
            log_path=log_path,
            artifacts=(
                {"artifact_type": "scenario_result", "uri": str(result_path)},
                {"artifact_type": "scenario_log", "uri": str(log_path)},
            ),
        )

    def inspect(self, *, scenario_name: str, run_id: str) -> ScenarioRuntimeInspection:
        state = self._runs[run_id]
        assert state["scenario_name"] == scenario_name
        return ScenarioRuntimeInspection(
            status=state["status"],
            summary=state["summary"],
            artifacts=(
                {"artifact_type": "scenario_result", "uri": str(state["result_path"])},
                {"artifact_type": "scenario_log", "uri": str(state["log_path"])},
            ),
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
        _ = process_id
        _ = result_path
        _ = log_path
        assert run_id is not None
        self.complete(run_id, status=RunStatus.CANCELLED, summary="scenario cancelled by control plane")
        return self.inspect(scenario_name="takeoff_land", run_id=run_id)

    def complete(self, run_id: str, *, status: RunStatus, summary: str) -> None:
        state = self._runs[run_id]
        state["status"] = status
        state["summary"] = summary


class StubMissionRuntime:
    def __init__(self) -> None:
        self._observation = MissionRuntimeObservation(
            mission_id="patrol_basic",
            status=MissionStatus.IDLE,
            active=False,
            terminal=False,
            detail="mission idle",
            last_command="",
            current_waypoint_index=0,
            total_waypoints=3,
            samples=0,
        )

    def supported_missions(self) -> set[str]:
        return {"patrol_basic"}

    def start(self, mission_name: str, parameters: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        _ = parameters
        self._observation = MissionRuntimeObservation(
            mission_id=mission_name,
            status=MissionStatus.ARMING,
            active=True,
            terminal=False,
            detail="mission start requested through stub runtime",
            last_command="start",
            current_waypoint_index=0,
            total_waypoints=3,
            samples=self._observation.samples + 1,
        )
        return (
            {"artifact_type": "mission_command_topic", "uri": "/drone/mission_command"},
            {"artifact_type": "mission_plan", "uri": f"simulation/scenarios/{mission_name}.json"},
        )

    def abort(self, mission_name: str, *, reason: str = "") -> tuple[dict[str, Any], ...]:
        detail = "mission abort requested through stub runtime"
        if reason:
            detail = f"{detail}: {reason}"
        self._observation = MissionRuntimeObservation(
            mission_id=mission_name,
            status=MissionStatus.ABORTING,
            active=True,
            terminal=False,
            detail=detail,
            last_command="abort",
            current_waypoint_index=self._observation.current_waypoint_index,
            total_waypoints=self._observation.total_waypoints,
            samples=self._observation.samples + 1,
        )
        return ({"artifact_type": "mission_command_topic", "uri": "/drone/mission_command"},)

    def reset(self, mission_name: str, *, reason: str = "") -> tuple[dict[str, Any], ...]:
        detail = "mission reset requested through stub runtime"
        if reason:
            detail = f"{detail}: {reason}"
        self._observation = MissionRuntimeObservation(
            mission_id=mission_name,
            status=MissionStatus.IDLE,
            active=False,
            terminal=False,
            detail=detail,
            last_command="reset",
            current_waypoint_index=0,
            total_waypoints=self._observation.total_waypoints,
            samples=self._observation.samples + 1,
        )
        return ({"artifact_type": "mission_command_topic", "uri": "/drone/mission_command"},)

    def get_status(self, mission_name: str | None = None) -> MissionRuntimeObservation:
        if mission_name is not None and mission_name != self._observation.mission_id:
            return MissionRuntimeObservation(
                mission_id=mission_name,
                status=MissionStatus.IDLE,
                active=False,
                terminal=False,
                detail="mission idle",
                total_waypoints=3,
            )
        return self._observation

    def set_status(
        self,
        status: MissionStatus,
        *,
        detail: str,
        active: bool,
        terminal: bool,
        last_command: str,
        current_waypoint_index: int = 0,
        total_waypoints: int = 3,
    ) -> None:
        self._observation = MissionRuntimeObservation(
            mission_id="patrol_basic",
            status=status,
            active=active,
            terminal=terminal,
            detail=detail,
            last_command=last_command,
            current_waypoint_index=current_waypoint_index,
            total_waypoints=total_waypoints,
            samples=self._observation.samples + 1,
        )


class StubVehicleRuntime:
    def __init__(self) -> None:
        self.commands: list[tuple[str, dict[str, Any]]] = []

    def supported_actions(self) -> set[str]:
        return {
            "vehicle.arm",
            "vehicle.disarm",
            "vehicle.takeoff",
            "vehicle.land",
            "vehicle.return_to_home",
            "vehicle.goto",
        }

    def dispatch(self, action_name: str, payload: dict[str, Any]):
        self.commands.append((action_name, dict(payload)))
        return type(
            "VehicleDispatch",
            (),
            {
                "action_name": action_name,
                "command_name": action_name.split(".", 1)[1],
                "artifacts": (
                    {"artifact_type": "vehicle_command_topic", "uri": "/drone/vehicle_command"},
                ),
            },
        )()


class StubSafetyRuntime:
    def __init__(self) -> None:
        self._active_faults: dict[str, dict[str, Any]] = {}

    def inject_fault(self, fault_type: str, *, value: float = 0.0, detail: str = ""):
        self._active_faults[fault_type] = {
            "fault_type": fault_type,
            "active": True,
            "value": value,
            "detail": detail,
            "source": "operator",
            "raised_at": "2026-04-07T00:00:00+00:00",
        }
        return type(
            "SafetyDispatch",
            (),
            {
                "action_name": "safety.inject_fault",
                "fault_type": fault_type,
                "artifacts": (
                    {"artifact_type": "safety_fault_topic", "uri": "/drone/safety_fault"},
                ),
            },
        )()

    def clear_fault(self, fault_type: str):
        self._active_faults.pop(fault_type, None)
        return type(
            "SafetyDispatch",
            (),
            {
                "action_name": "safety.clear_fault",
                "fault_type": fault_type,
                "artifacts": (
                    {"artifact_type": "safety_fault_topic", "uri": "/drone/safety_fault"},
                ),
            },
        )()

    def active_faults(self):
        return tuple(
            SafetyFaultRecord(
                fault_type=item["fault_type"],
                active=item["active"],
                value=item["value"],
                detail=item["detail"],
                source=item["source"],
                raised_at=item["raised_at"],
            )
            for item in self._active_faults.values()
        )


def test_control_status_reports_runtime_orchestrator_state(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    client = TestClient(
        create_app(
            read_model_adapter=StubReadModelAdapter(),
            simulation_runtime=runtime,
            mission_runtime=mission_runtime,
            state_root=tmp_path / "state",
        )
    )

    response = client.get("/api/v1/control/status")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["service"]["phase"] == "R15"
    assert payload["service"]["mode"] == "final-acceptance"
    assert payload["session"]["status"] == "idle"


def test_perception_status_and_stream_surface_use_read_model(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MARK1_CAMERA_STREAM_URL", "http://127.0.0.1:8181/mjpeg")
    client = TestClient(
        create_app(
            read_model_adapter=StubReadModelAdapter(
                snapshot={
                    "run_id": "telemetry-run",
                    "session_id": "session-1",
                    "perception_heartbeat": {
                        "healthy": True,
                        "frame_age_s": 0.08,
                        "pipeline_latency_s": 0.12,
                    },
                    "tracked_object": {
                        "tracked": True,
                        "label": "person",
                        "confidence": 0.94,
                    },
                    "perception_event": {
                        "event_type": "tracking_locked",
                    },
                    "latest_by_kind": {},
                }
            ),
            state_root=tmp_path / "state",
        )
    )

    perception_status = client.get("/api/v1/control/perception/status")
    assert perception_status.status_code == 200
    assert perception_status.json()["data"]["healthy"] is True
    assert perception_status.json()["data"]["detections_available"] is True
    assert perception_status.json()["data"]["last_heartbeat_age_ms"] == 80

    stream_status = client.get("/api/v1/control/perception/stream/status")
    assert stream_status.status_code == 200
    assert stream_status.json()["data"]["stream_available"] is True
    assert stream_status.json()["data"]["source"] == "http://127.0.0.1:8181/mjpeg"


def test_health_reflects_runtime_readiness(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    client = TestClient(
        create_app(
            read_model_adapter=StubReadModelAdapter(),
            simulation_runtime=runtime,
            mission_runtime=mission_runtime,
            state_root=tmp_path / "state",
        )
    )

    idle_health = client.get("/api/v1/health")
    assert idle_health.status_code == 200
    assert idle_health.json()["simulation_runtime_ready"] is False

    assert client.post("/api/v1/control/simulation/start", json={}).status_code == 200

    active_health = client.get("/api/v1/health")
    assert active_health.status_code == 200
    assert active_health.json()["simulation_runtime_ready"] is True


def test_simulation_start_stop_and_run_history_work_through_api(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    client = TestClient(
        create_app(
            read_model_adapter=StubReadModelAdapter(),
            simulation_runtime=runtime,
            mission_runtime=mission_runtime,
            state_root=tmp_path / "state",
        )
    )

    start = client.post(
        "/api/v1/control/simulation/start",
        json={"input": {"mode": "headless"}, "requested_by": {"type": "operator_ui", "id": "local-user"}},
    )
    assert start.status_code == 200
    start_payload = start.json()["data"]
    session_status = client.get("/api/v1/control/simulation/status")
    assert session_status.json()["data"]["status"] == "active"
    assert start_payload["status"] == "completed"
    assert start_payload["run_id"]

    stop = client.post("/api/v1/control/simulation/stop", json={})
    assert stop.status_code == 200
    assert stop.json()["data"]["status"] == "completed"

    runs = client.get("/api/v1/read/runs")
    assert runs.status_code == 200
    assert len(runs.json()["data"]["runs"]) == 2
    assert {item["name"] for item in runs.json()["data"]["runs"]} == {"simulation.start", "simulation.stop"}


def test_simulation_restart_creates_new_session_and_persists_it(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    state_root = tmp_path / "state"
    client = TestClient(
        create_app(
            read_model_adapter=StubReadModelAdapter(),
            simulation_runtime=runtime,
            mission_runtime=mission_runtime,
            state_root=state_root,
        )
    )

    start = client.post("/api/v1/control/simulation/start", json={})
    first_session_id = client.get("/api/v1/control/simulation/status").json()["data"]["session_id"]
    assert start.status_code == 200

    restart = client.post("/api/v1/control/simulation/restart", json={"input": {"mode": "visual"}})
    assert restart.status_code == 200

    current = client.get("/api/v1/control/simulation/status").json()["data"]
    assert current["status"] == "active"
    assert current["mode"] == "visual"
    assert current["session_id"] != first_session_id

    persisted_runtime = StubSimulationRuntime(tmp_path)
    persisted_runtime._active_session_id = current["session_id"]
    reloaded_client = TestClient(
        create_app(
            read_model_adapter=StubReadModelAdapter(),
            simulation_runtime=persisted_runtime,
            mission_runtime=mission_runtime,
            state_root=state_root,
        )
    )
    reloaded = reloaded_client.get("/api/v1/control/simulation/status")
    assert reloaded.status_code == 200
    assert reloaded.json()["data"]["session_id"] == current["session_id"]


def test_simulation_start_rejects_when_runtime_is_already_active(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    client = TestClient(
        create_app(
            read_model_adapter=StubReadModelAdapter(),
            simulation_runtime=runtime,
            mission_runtime=mission_runtime,
            state_root=tmp_path / "state",
        )
    )

    assert client.post("/api/v1/control/simulation/start", json={}).status_code == 200
    second_start = client.post("/api/v1/control/simulation/start", json={})

    assert second_start.status_code == 409
    assert second_start.json()["errors"][0]["code"] == "invalid_state"


def test_simulation_preflight_failure_is_normalized(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path, fail_check=True)
    mission_runtime = StubMissionRuntime()
    client = TestClient(
        create_app(
            read_model_adapter=StubReadModelAdapter(),
            simulation_runtime=runtime,
            mission_runtime=mission_runtime,
            state_root=tmp_path / "state",
        )
    )

    response = client.post("/api/v1/control/simulation/start", json={})

    assert response.status_code == 503
    assert response.json()["errors"][0]["code"] == "dependency_unavailable"


def test_capability_discovery_marks_simulation_lifecycle_as_available_in_r3(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    client = TestClient(
        create_app(
            read_model_adapter=StubReadModelAdapter(),
            simulation_runtime=runtime,
            mission_runtime=mission_runtime,
            state_root=tmp_path / "state",
        )
    )

    response = client.get("/api/v1/control/capabilities")

    assert response.status_code == 200
    capabilities = {item["capability_name"]: item for item in response.json()["data"]}
    assert capabilities["simulation.lifecycle"]["status"] == "available"
    assert capabilities["telemetry.read_model"]["status"] == "available"


def test_scenario_list_hides_executor_and_exposes_control_plane_status(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    scenario_runtime = StubScenarioRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    client = TestClient(
        create_app(
            read_model_adapter=StubReadModelAdapter(),
            simulation_runtime=runtime,
            scenario_runtime=scenario_runtime,
            mission_runtime=mission_runtime,
            state_root=tmp_path / "state",
        )
    )

    response = client.get("/api/v1/control/scenarios")

    assert response.status_code == 200
    scenarios = {item["scenario_name"]: item for item in response.json()["data"]}
    assert "executor_type" not in scenarios["takeoff_land"]
    assert scenarios["takeoff_land"]["control_plane_status"] == "available"
    assert scenarios["patrol_basic"]["control_plane_status"] == "available"


def test_takeoff_land_runs_through_control_plane_and_status_is_consultable(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    scenario_runtime = StubScenarioRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    client = TestClient(
        create_app(
            read_model_adapter=StubReadModelAdapter(),
            simulation_runtime=runtime,
            scenario_runtime=scenario_runtime,
            mission_runtime=mission_runtime,
            state_root=tmp_path / "state",
        )
    )

    assert client.post("/api/v1/control/simulation/start", json={}).status_code == 200

    run_response = client.post("/api/v1/control/scenarios/takeoff_land/run", json={"input": {"backend": "fake-success"}})
    assert run_response.status_code == 200
    payload = run_response.json()["data"]
    assert payload["status"] == "running"
    run_id = payload["run_id"]

    running_status = client.get("/api/v1/control/scenarios/takeoff_land/status")
    assert running_status.status_code == 200
    assert running_status.json()["data"]["status"] == "running"
    assert running_status.json()["data"]["active_run_id"] == run_id

    scenario_runtime.complete(run_id, status=RunStatus.COMPLETED, summary="scenario completed successfully")

    completed_status = client.get("/api/v1/control/scenarios/takeoff_land/status")
    assert completed_status.status_code == 200
    completed_payload = completed_status.json()["data"]
    assert completed_payload["status"] == "completed"
    assert completed_payload.get("active_run_id") is None
    assert completed_payload["last_run_id"] == run_id

    runs = client.get("/api/v1/read/runs").json()["data"]["runs"]
    names = {item["name"] for item in runs}
    assert "scenario.run:takeoff_land" in names


def test_scenario_cancel_marks_run_cancelled_and_auditable(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    scenario_runtime = StubScenarioRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    client = TestClient(
        create_app(
            read_model_adapter=StubReadModelAdapter(),
            simulation_runtime=runtime,
            scenario_runtime=scenario_runtime,
            mission_runtime=mission_runtime,
            state_root=tmp_path / "state",
        )
    )

    assert client.post("/api/v1/control/simulation/start", json={}).status_code == 200
    run_response = client.post("/api/v1/control/scenarios/takeoff_land/run", json={})
    run_id = run_response.json()["data"]["run_id"]

    cancel = client.post("/api/v1/control/scenarios/takeoff_land/cancel", json={})
    assert cancel.status_code == 200
    assert cancel.json()["data"]["status"] == "completed"

    status = client.get("/api/v1/control/scenarios/takeoff_land/status")
    assert status.status_code == 200
    assert status.json()["data"]["status"] == "cancelled"
    assert status.json()["data"]["last_run_id"] == run_id

    runs = client.get("/api/v1/read/runs").json()["data"]["runs"]
    names = {item["name"] for item in runs}
    assert "scenario.cancel:takeoff_land" in names


def test_scenario_run_requires_active_simulation_session(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    scenario_runtime = StubScenarioRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    client = TestClient(
        create_app(
            read_model_adapter=StubReadModelAdapter(),
            simulation_runtime=runtime,
            scenario_runtime=scenario_runtime,
            mission_runtime=mission_runtime,
            state_root=tmp_path / "state",
        )
    )

    response = client.post("/api/v1/control/scenarios/takeoff_land/run", json={})

    assert response.status_code == 409
    assert response.json()["errors"][0]["code"] == "invalid_state"


def test_patrol_basic_runs_through_mission_surface_and_converges_status(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    scenario_runtime = StubScenarioRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    client = TestClient(
        create_app(
            read_model_adapter=StubReadModelAdapter(),
            simulation_runtime=runtime,
            scenario_runtime=scenario_runtime,
            mission_runtime=mission_runtime,
            state_root=tmp_path / "state",
        )
    )

    assert client.post("/api/v1/control/simulation/start", json={}).status_code == 200
    response = client.post("/api/v1/control/scenarios/patrol_basic/run", json={})

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["status"] == "running"
    run_id = payload["run_id"]

    running = client.get("/api/v1/control/scenarios/patrol_basic/status")
    assert running.status_code == 200
    assert running.json()["data"]["status"] == "running"
    assert running.json()["data"]["active_run_id"] == run_id

    mission_runtime.set_status(
        MissionStatus.COMPLETED,
        detail="mission completed successfully",
        active=False,
        terminal=True,
        last_command="land",
        current_waypoint_index=3,
        total_waypoints=3,
    )

    completed = client.get("/api/v1/control/scenarios/patrol_basic/status")
    assert completed.status_code == 200
    assert completed.json()["data"]["status"] == "completed"
    assert completed.json()["data"]["last_run_id"] == run_id
    assert completed.json()["data"].get("active_run_id") is None


def test_capability_discovery_marks_patrol_vehicle_and_safety_available_in_r6(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    scenario_runtime = StubScenarioRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    vehicle_runtime = StubVehicleRuntime()
    safety_runtime = StubSafetyRuntime()
    client = TestClient(
        create_app(
            read_model_adapter=StubReadModelAdapter(),
            simulation_runtime=runtime,
            scenario_runtime=scenario_runtime,
            mission_runtime=mission_runtime,
            vehicle_runtime=vehicle_runtime,
            safety_runtime=safety_runtime,
            state_root=tmp_path / "state",
        )
    )

    response = client.get("/api/v1/control/capabilities")

    assert response.status_code == 200
    capabilities = {item["capability_name"]: item for item in response.json()["data"]}
    assert capabilities["scenario.takeoff_land.run"]["status"] == "available"
    assert capabilities["scenario.patrol_basic.run"]["status"] == "available"
    assert capabilities["mission.control"]["status"] == "available"
    assert capabilities["vehicle.basic_control"]["status"] == "available"
    assert capabilities["safety.fault_injection"]["status"] == "available"


def test_vehicle_commands_and_safety_faults_work_through_control_plane(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    vehicle_runtime = StubVehicleRuntime()
    safety_runtime = StubSafetyRuntime()
    read_model = StubReadModelAdapter(
        {
            "run_id": "telemetry-run",
            "vehicle_state": {
                "connected": True,
                "armed": True,
                "failsafe": False,
                "nav_state": "POSCTL",
                "altitude_m": 100.0,
                "relative_altitude_m": 2.0,
                "absolute_altitude_m": 100.0,
                "latitude_deg": -22.9985,
                "longitude_deg": -43.3658,
            },
            "safety_status": {
                "active": False,
                "rule": "",
                "action": "",
                "source": "",
                "detail": "safety state clear",
            },
            "latest_by_kind": {},
        }
    )
    client = TestClient(
        create_app(
            read_model_adapter=read_model,
            simulation_runtime=runtime,
            mission_runtime=mission_runtime,
            vehicle_runtime=vehicle_runtime,
            safety_runtime=safety_runtime,
            state_root=tmp_path / "state",
        )
    )

    assert client.post("/api/v1/control/simulation/start", json={}).status_code == 200

    arm = client.post("/api/v1/control/vehicles/arm", json={})
    assert arm.status_code == 200
    assert arm.json()["data"]["status"] == "completed"

    goto = client.post(
        "/api/v1/control/vehicles/goto",
        json={
            "input": {
                "latitude_deg": -22.9984,
                "longitude_deg": -43.3657,
                "relative_altitude_m": 3.0,
            }
        },
    )
    assert goto.status_code == 200
    assert vehicle_runtime.commands[-1][0] == "vehicle.goto"
    assert vehicle_runtime.commands[-1][1]["target_absolute_altitude_m"] == 103.0

    inject = client.post(
        "/api/v1/control/safety/faults/inject",
        json={"input": {"fault_type": "gps_loss", "value": 1.0, "detail": "operator test"}},
    )
    assert inject.status_code == 200

    clear = client.post(
        "/api/v1/control/safety/faults/clear",
        json={"input": {"fault_type": "gps_loss"}},
    )
    assert clear.status_code == 200

    run_names = {item["name"] for item in client.get("/api/v1/read/runs").json()["data"]["runs"]}
    assert "vehicle.arm" in run_names
    assert "vehicle.goto" in run_names
    assert "safety.inject_fault" in run_names
    assert "safety.clear_fault" in run_names


def test_vehicle_command_requires_active_session(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    vehicle_runtime = StubVehicleRuntime()
    safety_runtime = StubSafetyRuntime()
    client = TestClient(
        create_app(
            read_model_adapter=StubReadModelAdapter(),
            simulation_runtime=runtime,
            mission_runtime=mission_runtime,
            vehicle_runtime=vehicle_runtime,
            safety_runtime=safety_runtime,
            state_root=tmp_path / "state",
        )
    )

    response = client.post("/api/v1/control/vehicles/arm", json={})

    assert response.status_code == 409
    assert response.json()["errors"][0]["code"] == "invalid_state"


def test_safety_status_uses_read_model_and_fault_registry(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    vehicle_runtime = StubVehicleRuntime()
    safety_runtime = StubSafetyRuntime()
    read_model = StubReadModelAdapter(
        {
            "run_id": "telemetry-run",
            "safety_status": {
                "active": True,
                "rule": "gps_loss",
                "action": "land",
                "source": "safety_manager",
                "detail": "gps lost for 1.5s",
            },
            "latest_by_kind": {},
        }
    )
    client = TestClient(
        create_app(
            read_model_adapter=read_model,
            simulation_runtime=runtime,
            mission_runtime=mission_runtime,
            vehicle_runtime=vehicle_runtime,
            safety_runtime=safety_runtime,
            state_root=tmp_path / "state",
        )
    )

    assert client.post("/api/v1/control/simulation/start", json={}).status_code == 200
    assert client.post(
        "/api/v1/control/safety/faults/inject",
        json={"input": {"fault_type": "gps_loss", "value": 1.0, "detail": "operator test"}},
    ).status_code == 200

    response = client.get("/api/v1/control/safety/status")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["state"] == "active"
    assert payload["active_faults"][0]["fault_type"] == "gps_loss"
    assert "land" in payload["summary"]


def test_perception_status_and_stream_status_use_read_model_and_env(tmp_path: Path, monkeypatch) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    read_model = StubReadModelAdapter(
        {
            "run_id": "telemetry-run",
            "tracked_object": {
                "tracked": True,
                "label": "person",
                "confidence": 0.93,
            },
            "perception_heartbeat": {
                "healthy": True,
                "pipeline_latency_s": 0.11,
                "frame_age_s": 0.18,
                "fps": 24,
            },
            "perception_event": {
                "event_type": "tracking_update",
                "detail": "target reacquired",
            },
            "latest_by_kind": {
                "perception_event": {
                    "kind": "perception_event",
                }
            },
        }
    )
    monkeypatch.setenv("MARK1_CAMERA_STREAM_URL", "http://127.0.0.1:9000/stream")
    client = TestClient(
        create_app(
            read_model_adapter=read_model,
            simulation_runtime=runtime,
            mission_runtime=mission_runtime,
            state_root=tmp_path / "state",
        )
    )

    perception = client.get("/api/v1/control/perception/status")
    assert perception.status_code == 200
    perception_payload = perception.json()["data"]
    assert perception_payload["healthy"] is True
    assert perception_payload["detections_available"] is True
    assert perception_payload["last_heartbeat_age_ms"] == 180
    assert "label=person" in perception_payload["detail"]

    stream = client.get("/api/v1/control/perception/stream/status")
    assert stream.status_code == 200
    stream_payload = stream.json()["data"]
    assert stream_payload["stream_available"] is True
    assert stream_payload["source"] == "http://127.0.0.1:9000/stream"
    assert stream_payload["fps"] == 24


def test_unknown_scenario_is_rejected_before_future_phase_handler(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    client = TestClient(
        create_app(
            read_model_adapter=StubReadModelAdapter(),
            simulation_runtime=runtime,
            mission_runtime=mission_runtime,
            state_root=tmp_path / "state",
        )
    )

    response = client.post("/api/v1/control/scenarios/not-a-real-scenario/run", json={})

    assert response.status_code == 404
    assert response.json()["errors"][0]["code"] == "invalid_request"


def test_read_snapshot_returns_dependency_error_when_adapter_fails(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    client = TestClient(
        create_app(
            read_model_adapter=StubReadModelAdapter(should_fail=True),
            simulation_runtime=runtime,
            mission_runtime=mission_runtime,
            state_root=tmp_path / "state",
        )
    )

    response = client.get("/api/v1/read/snapshot")

    assert response.status_code == 502
    assert response.json()["errors"][0]["code"] == "dependency_unavailable"


def test_read_model_endpoints_proxy_snapshot_metrics_events_runs_and_replay(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    read_model = StubReadModelAdapter(
        {
            "current_run_id": "telemetry-run",
            "run_id": "telemetry-run",
            "updated_at_ns": 123456789,
            "vehicle_state": {"connected": True, "armed": False},
            "mission_status": {"phase": "hover"},
            "safety_status": {"active": False},
            "latest_by_kind": {
                "vehicle_state": {
                    "run_id": "telemetry-run",
                    "kind": "vehicle_state",
                    "payload": {"connected": True, "armed": False},
                }
            },
        }
    )
    read_model.set_metrics(
        {
            "run_id": "telemetry-run",
            "metrics": [{"seq": 1, "altitude_m": 12.0}, {"seq": 2, "altitude_m": 12.5}],
            "source": "stub_read_model",
        }
    )
    read_model.set_events(
        {
            "run_id": "telemetry-run",
            "events": [
                {"sequence": 1, "kind": "vehicle_state"},
                {"sequence": 2, "kind": "mission_status"},
            ],
            "source": "stub_read_model",
        }
    )
    read_model.set_runs(
        [
            {
                "run_id": "telemetry-run",
                "source": "telemetry_bridge",
                "event_count": 2,
                "metrics_count": 2,
                "last_kind": "mission_status",
            }
        ]
    )
    read_model.set_replay(
        "telemetry-run",
        {
            "run_id": "telemetry-run",
            "snapshot": {
                "run_id": "telemetry-run",
                "vehicle_state": {"connected": True},
                "latest_by_kind": {},
            },
            "events": [{"sequence": 1, "kind": "vehicle_state"}],
            "metrics": [{"seq": 1, "altitude_m": 12.0}],
        },
    )
    client = TestClient(
        create_app(
            read_model_adapter=read_model,
            simulation_runtime=runtime,
            mission_runtime=mission_runtime,
            state_root=tmp_path / "state",
        )
    )

    assert client.post("/api/v1/control/simulation/start", json={}).status_code == 200

    snapshot = client.get("/api/v1/read/snapshot")
    assert snapshot.status_code == 200
    assert snapshot.json()["data"]["run_id"] == "telemetry-run"
    assert snapshot.json()["data"]["session_id"].startswith("session_")

    metrics = client.get("/api/v1/read/metrics", params={"run_id": "telemetry-run", "limit": 1})
    assert metrics.status_code == 200
    assert metrics.json()["data"]["run_id"] == "telemetry-run"
    assert len(metrics.json()["data"]["metrics"]) == 1

    events = client.get("/api/v1/read/events", params={"run_id": "telemetry-run", "kind": "mission_status"})
    assert events.status_code == 200
    assert len(events.json()["data"]["events"]) == 1
    assert events.json()["data"]["events"][0]["kind"] == "mission_status"

    runs = client.get("/api/v1/read/runs")
    assert runs.status_code == 200
    runs_payload = runs.json()["data"]
    telemetry_runs = {item["run_id"]: item for item in runs_payload["telemetry_runs"]}
    assert runs_payload["current_telemetry_run_id"] == "telemetry-run"
    assert telemetry_runs["telemetry-run"]["session_id"].startswith("session_")

    replay = client.get("/api/v1/read/replay", params={"run_id": "telemetry-run"})
    assert replay.status_code == 200
    assert replay.json()["data"]["run_id"] == "telemetry-run"
    assert replay.json()["data"]["snapshot"]["session_id"].startswith("session_")


def test_read_runs_returns_dependency_error_when_adapter_fails(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    client = TestClient(
        create_app(
            read_model_adapter=StubReadModelAdapter(should_fail=True),
            simulation_runtime=runtime,
            mission_runtime=mission_runtime,
            state_root=tmp_path / "state",
        )
    )

    response = client.get("/api/v1/read/runs")

    assert response.status_code == 502
    assert response.json()["errors"][0]["code"] == "dependency_unavailable"


def test_mission_status_exposes_consolidated_product_state(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    mission_runtime.set_status(
        MissionStatus.PATROL,
        detail="waypoint 1",
        active=True,
        terminal=False,
        last_command="goto",
        current_waypoint_index=1,
        total_waypoints=3,
    )
    client = TestClient(
        create_app(
            read_model_adapter=StubReadModelAdapter(),
            simulation_runtime=runtime,
            mission_runtime=mission_runtime,
            state_root=tmp_path / "state",
        )
    )

    response = client.get("/api/v1/control/missions/status")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["mission_id"] == "patrol_basic"
    assert payload["status"] == "patrol"
    assert payload["constraints"]["current_waypoint_index"] == 1
    assert payload["constraints"]["last_command"] == "goto"


def test_mission_start_requires_active_simulation_session(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    client = TestClient(
        create_app(
            read_model_adapter=StubReadModelAdapter(),
            simulation_runtime=runtime,
            mission_runtime=mission_runtime,
            state_root=tmp_path / "state",
        )
    )

    response = client.post("/api/v1/control/missions/start", json={})

    assert response.status_code == 409
    assert response.json()["errors"][0]["code"] == "invalid_state"


def test_mission_start_abort_and_reset_work_through_control_plane(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    client = TestClient(
        create_app(
            read_model_adapter=StubReadModelAdapter(),
            simulation_runtime=runtime,
            mission_runtime=mission_runtime,
            state_root=tmp_path / "state",
        )
    )

    assert client.post("/api/v1/control/simulation/start", json={}).status_code == 200

    start = client.post("/api/v1/control/missions/start", json={})
    assert start.status_code == 200
    assert start.json()["data"]["status"] == "running"
    scenario_status = client.get("/api/v1/control/scenarios/patrol_basic/status")
    assert scenario_status.status_code == 200
    assert scenario_status.json()["data"]["status"] == "running"

    mission_runtime.set_status(
        MissionStatus.PATROL,
        detail="mission in patrol",
        active=True,
        terminal=False,
        last_command="goto",
        current_waypoint_index=1,
        total_waypoints=3,
    )
    abort = client.post("/api/v1/control/missions/abort", json={"input": {"reason": "operator stop"}})
    assert abort.status_code == 200
    assert abort.json()["data"]["status"] == "completed"

    mission_runtime.set_status(
        MissionStatus.ABORTED,
        detail="mission aborted",
        active=False,
        terminal=True,
        last_command="abort",
        current_waypoint_index=1,
        total_waypoints=3,
    )
    reset = client.post("/api/v1/control/missions/reset", json={})
    assert reset.status_code == 200
    assert reset.json()["data"]["status"] == "completed"

    run_names = {item["name"] for item in client.get("/api/v1/read/runs").json()["data"]["runs"]}
    assert "mission.start:patrol_basic" in run_names
    assert "mission.abort:patrol_basic" in run_names
    assert "mission.reset:patrol_basic" in run_names


def test_mission_reset_requires_terminal_state(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    client = TestClient(
        create_app(
            read_model_adapter=StubReadModelAdapter(),
            simulation_runtime=runtime,
            mission_runtime=mission_runtime,
            state_root=tmp_path / "state",
        )
    )

    assert client.post("/api/v1/control/simulation/start", json={}).status_code == 200
    assert client.post("/api/v1/control/missions/start", json={}).status_code == 200

    response = client.post("/api/v1/control/missions/reset", json={})

    assert response.status_code == 409
    assert response.json()["errors"][0]["code"] == "invalid_state"


def test_vehicle_commands_dispatch_through_control_plane(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    vehicle_runtime = StubVehicleRuntime()
    read_model = StubReadModelAdapter(
        {
            "vehicle_state": {
                "connected": True,
                "armed": True,
                "nav_state": "AUTO_LOITER",
                "absolute_altitude_m": 100.0,
                "relative_altitude_m": 3.0,
                "altitude_m": 100.0,
                "latitude_deg": -22.9,
                "longitude_deg": -43.3,
            }
        }
    )
    client = TestClient(
        create_app(
            read_model_adapter=read_model,
            simulation_runtime=runtime,
            mission_runtime=mission_runtime,
            vehicle_runtime=vehicle_runtime,
            state_root=tmp_path / "state",
        )
    )

    assert client.post("/api/v1/control/simulation/start", json={}).status_code == 200

    for action_name in ["arm", "disarm", "takeoff", "land", "return_to_home"]:
        response = client.post(f"/api/v1/control/vehicles/{action_name}", json={})
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "completed"

    goto = client.post(
        "/api/v1/control/vehicles/goto",
        json={"input": {"latitude_deg": -22.91, "longitude_deg": -43.31, "relative_altitude_m": 5.0}},
    )
    assert goto.status_code == 200
    dispatched_action, dispatched_payload = vehicle_runtime.commands[-1]
    assert dispatched_action == "vehicle.goto"
    assert dispatched_payload["target_absolute_altitude_m"] == 105.0

    run_names = {item["name"] for item in client.get("/api/v1/read/runs").json()["data"]["runs"]}
    assert "vehicle.arm" in run_names
    assert "vehicle.goto" in run_names


def test_vehicle_commands_require_active_session(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    vehicle_runtime = StubVehicleRuntime()
    client = TestClient(
        create_app(
            read_model_adapter=StubReadModelAdapter(),
            simulation_runtime=runtime,
            mission_runtime=mission_runtime,
            vehicle_runtime=vehicle_runtime,
            state_root=tmp_path / "state",
        )
    )

    response = client.post("/api/v1/control/vehicles/arm", json={})

    assert response.status_code == 409
    assert response.json()["errors"][0]["code"] == "invalid_state"


def test_safety_fault_injection_clear_and_status_work_through_control_plane(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    safety_runtime = StubSafetyRuntime()
    read_model = StubReadModelAdapter(
        {
            "safety_status": {
                "active": True,
                "mission_abort_requested": True,
                "vehicle_command_sent": True,
                "rule": "gps_loss",
                "action": "land",
                "source": "operator",
                "detail": "gps loss injected",
                "trigger_count": 1,
            }
        }
    )
    client = TestClient(
        create_app(
            read_model_adapter=read_model,
            simulation_runtime=runtime,
            mission_runtime=mission_runtime,
            safety_runtime=safety_runtime,
            state_root=tmp_path / "state",
        )
    )

    assert client.post("/api/v1/control/simulation/start", json={}).status_code == 200

    inject = client.post(
        "/api/v1/control/safety/faults/inject",
        json={"input": {"fault_type": "gps_loss", "value": 1.0, "detail": "gps loss injected"}},
    )
    assert inject.status_code == 200
    assert inject.json()["data"]["status"] == "completed"

    status = client.get("/api/v1/control/safety/status")
    assert status.status_code == 200
    payload = status.json()["data"]
    assert payload["state"] == "active"
    assert payload["active_faults"][0]["fault_type"] == "gps_loss"
    assert "gps_loss" in payload["summary"]

    read_model.set_snapshot({"safety_status": {"active": False, "detail": "safety state clear"}})
    clear = client.post("/api/v1/control/safety/faults/clear", json={"input": {"fault_type": "gps_loss"}})
    assert clear.status_code == 200

    cleared = client.get("/api/v1/control/safety/status")
    assert cleared.status_code == 200
    assert cleared.json()["data"]["state"] == "clear"
    assert cleared.json()["data"]["active_faults"] == []


def test_perception_status_and_stream_status_are_exposed(tmp_path: Path, monkeypatch) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    read_model = StubReadModelAdapter(
        {
            "tracked_object": {
                "tracked": True,
                "label": "person",
                "confidence": 0.93,
                "state": "tracking",
            },
            "perception_heartbeat": {
                "healthy": True,
                "pipeline_latency_s": 0.08,
                "frame_age_s": 0.12,
            },
            "perception_event": {
                "event_type": "tracking_update",
                "detail": "target reacquired",
            },
            "latest_by_kind": {
                "perception_event": {
                    "kind": "perception_event",
                    "payload": {"event_type": "tracking_update"},
                }
            },
        }
    )
    monkeypatch.setenv("CONTROL_API_PERCEPTION_STREAM_URL", "http://127.0.0.1:9000/stream")
    monkeypatch.setenv("CONTROL_API_PERCEPTION_STREAM_SOURCE", "camera-proxy")
    client = TestClient(
        create_app(
            read_model_adapter=read_model,
            simulation_runtime=runtime,
            mission_runtime=mission_runtime,
            state_root=tmp_path / "state",
        )
    )

    perception = client.get("/api/v1/control/perception/status")
    assert perception.status_code == 200
    perception_payload = perception.json()["data"]
    assert perception_payload["status"] == "healthy"
    assert perception_payload["tracked"] is True
    assert perception_payload["label"] == "person"
    assert perception_payload["last_event_kind"] == "perception_event"

    stream = client.get("/api/v1/control/perception/stream/status")
    assert stream.status_code == 200
    stream_payload = stream.json()["data"]
    assert stream_payload["available"] is True
    assert stream_payload["stream_url"] == "http://127.0.0.1:9000/stream"
    assert stream_payload["source"] == "camera-proxy"


def test_patrol_cancel_routes_to_mission_abort_and_marks_run_cancelled(tmp_path: Path) -> None:
    runtime = StubSimulationRuntime(tmp_path)
    scenario_runtime = StubScenarioRuntime(tmp_path)
    mission_runtime = StubMissionRuntime()
    client = TestClient(
        create_app(
            read_model_adapter=StubReadModelAdapter(),
            simulation_runtime=runtime,
            scenario_runtime=scenario_runtime,
            mission_runtime=mission_runtime,
            state_root=tmp_path / "state",
        )
    )

    assert client.post("/api/v1/control/simulation/start", json={}).status_code == 200
    run_response = client.post("/api/v1/control/scenarios/patrol_basic/run", json={})
    run_id = run_response.json()["data"]["run_id"]

    cancel = client.post("/api/v1/control/scenarios/patrol_basic/cancel", json={})
    assert cancel.status_code == 200

    mission_runtime.set_status(
        MissionStatus.ABORTED,
        detail="mission aborted by control plane",
        active=False,
        terminal=True,
        last_command="abort",
        current_waypoint_index=1,
        total_waypoints=3,
    )
    status = client.get("/api/v1/control/scenarios/patrol_basic/status")
    assert status.status_code == 200
    assert status.json()["data"]["status"] == "cancelled"
    assert status.json()["data"]["last_run_id"] == run_id
