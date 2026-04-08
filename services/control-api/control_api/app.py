from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import os
from pathlib import Path
import uuid
from typing import Any

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from control_plane.domain import (
    CapabilityStatus,
    INITIAL_ACTION_CATALOG,
    INITIAL_CAPABILITY_CATALOG,
    ActionExecutionStatus,
    ActionResult,
    ControlPlaneErrorCode,
    MissionDefinition,
    MissionStatus,
    PerceptionStatus,
    PerceptionStreamStatus,
    RunList,
    RunRecord,
    RunStatus,
    SafetyFaultRecord,
    SafetyStatus,
    SessionMode,
    SimulationComponent,
    SimulationSession,
    SimulationSessionStatus,
    ScenarioStatus,
    TelemetryEvents,
    TelemetryMetrics,
    TelemetryReplay,
    TelemetrySnapshot,
    VehiclePosition,
    VehicleRecord,
)

from .read_model import HttpReadModelAdapter, ReadModelAdapter
from .mission_runtime import (
    MissionRuntimeAdapter,
    MissionRuntimeError,
    MissionRuntimeObservation,
    ShellRos2MissionRuntimeAdapter,
)
from .scenarios import load_scenario_registry, public_scenario_definition
from .scenario_runtime import (
    ScenarioRuntimeAdapter,
    ScenarioRuntimeError,
    ShellScenarioRuntimeAdapter,
)
from .simulation_runtime import (
    ShellSimulationRuntimeAdapter,
    SimulationRuntimeAdapter,
    SimulationRuntimeError,
)
from .safety_runtime import (
    SafetyRuntimeAdapter,
    SafetyRuntimeError,
    ShellRos2SafetyRuntimeAdapter,
)
from .stores import RunStore, ScenarioState, ScenarioStore, SessionStore
from .vehicle_runtime import (
    ShellRos2VehicleRuntimeAdapter,
    VehicleRuntimeAdapter,
    VehicleRuntimeError,
)


class RequestedByIn(BaseModel):
    type: str = "control_api"
    id: str = "local-service"


class ActionInvocationIn(BaseModel):
    target: str = "default"
    session_id: str | None = None
    request_id: str | None = None
    input: dict[str, Any] = Field(default_factory=dict)
    requested_by: RequestedByIn = Field(default_factory=RequestedByIn)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso_from_ns(value: Any) -> str | None:
    if value in {None, ""}:
        return None
    try:
        stamp_ns = int(value)
    except (TypeError, ValueError):
        return None
    return datetime.fromtimestamp(stamp_ns / 1_000_000_000, tz=timezone.utc).isoformat()


def _response_envelope(
    data: Any,
    *,
    status: str = "ok",
    errors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {"status": status, "data": data, "errors": errors or []}


def _error_response(
    *,
    status_code: int,
    code: ControlPlaneErrorCode,
    message: str,
    detail: str = "",
    data: Any = None,
    status: str = "error",
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=_response_envelope(
            data,
            status=status,
            errors=[{"code": code.value, "message": message, "detail": detail}],
        ),
    )


def _build_action_result(
    *,
    payload: ActionInvocationIn,
    accepted: bool,
    status: ActionExecutionStatus,
    message: str,
    run_id: str | None = None,
    artifacts: tuple[dict[str, Any], ...] = (),
    errors: tuple[dict[str, Any], ...] = (),
) -> dict[str, Any]:
    result = ActionResult(
        request_id=payload.request_id or f"req_{uuid.uuid4().hex[:12]}",
        accepted=accepted,
        status=status,
        message=message,
        run_id=run_id,
        artifacts=tuple(),
        errors=tuple(),
    ).to_dict()
    result["artifacts"] = list(artifacts)
    result["errors"] = list(errors)
    return result


def _status_code_for_runtime_error(error: SimulationRuntimeError) -> int:
    if error.code == ControlPlaneErrorCode.DEPENDENCY_UNAVAILABLE:
        return 503
    if error.code == ControlPlaneErrorCode.TIMEOUT:
        return 504
    return 500


def _status_code_for_control_plane_code(code: ControlPlaneErrorCode) -> int:
    if code == ControlPlaneErrorCode.DEPENDENCY_UNAVAILABLE:
        return 503
    if code == ControlPlaneErrorCode.TIMEOUT:
        return 504
    if code == ControlPlaneErrorCode.INVALID_STATE:
        return 409
    if code == ControlPlaneErrorCode.INVALID_REQUEST:
        return 400
    if code == ControlPlaneErrorCode.NOT_SUPPORTED:
        return 501
    return 500


def _cors_allow_origins() -> list[str]:
    configured = os.environ.get("CONTROL_API_CORS_ALLOW_ORIGINS", "").strip()
    if configured:
        if configured == "*":
            return ["*"]
        return [item.strip() for item in configured.split(",") if item.strip()]
    return [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ]


def create_app(
    *,
    telemetry_api_base_url: str = "http://127.0.0.1:8080",
    read_model_adapter: ReadModelAdapter | None = None,
    scenarios_root: Path | None = None,
    simulation_runtime: SimulationRuntimeAdapter | None = None,
    scenario_runtime: ScenarioRuntimeAdapter | None = None,
    mission_runtime: MissionRuntimeAdapter | None = None,
    vehicle_runtime: VehicleRuntimeAdapter | None = None,
    safety_runtime: SafetyRuntimeAdapter | None = None,
    state_root: Path | None = None,
) -> FastAPI:
    repo_root = Path(__file__).resolve().parents[3]
    control_state_root = state_root or repo_root / ".sim-runtime" / "control-api-state"
    session_store = SessionStore(control_state_root / "session.json")
    run_store = RunStore(control_state_root / "runs.json")
    scenario_store = ScenarioStore(control_state_root / "scenarios.json")
    read_adapter = read_model_adapter or HttpReadModelAdapter(telemetry_api_base_url)
    runtime = simulation_runtime or ShellSimulationRuntimeAdapter(repo_root)
    scenario_runtime_adapter = scenario_runtime or ShellScenarioRuntimeAdapter(repo_root)
    mission_runtime_adapter = mission_runtime or ShellRos2MissionRuntimeAdapter(
        repo_root,
        telemetry_api_base_url=telemetry_api_base_url,
        state_root=control_state_root / "mission-runtime",
    )
    vehicle_runtime_adapter = vehicle_runtime or ShellRos2VehicleRuntimeAdapter(
        repo_root,
        state_root=control_state_root / "vehicle-runtime",
    )
    safety_runtime_adapter = safety_runtime or ShellRos2SafetyRuntimeAdapter(
        repo_root,
        state_root=control_state_root / "safety-runtime",
    )
    registry = load_scenario_registry(scenarios_root or repo_root / "simulation" / "scenarios")
    registry_by_name = {entry["scenario_name"]: entry for entry in registry}
    action_catalog = {definition.action_name: definition for definition in INITIAL_ACTION_CATALOG}

    implemented_action_names = {
        "simulation.start",
        "simulation.stop",
        "simulation.restart",
        "simulation.status.get",
        "capabilities.list",
        "scenario.list",
        "scenario.run",
        "scenario.cancel",
        "scenario.status.get",
        "mission.start",
        "mission.abort",
        "mission.reset",
        "mission.status.get",
        "vehicle.arm",
        "vehicle.disarm",
        "vehicle.takeoff",
        "vehicle.land",
        "vehicle.return_to_home",
        "vehicle.goto",
        "safety.inject_fault",
        "safety.clear_fault",
        "safety.status.get",
        "telemetry.snapshot.get",
        "telemetry.metrics.get",
        "telemetry.events.get",
        "telemetry.runs.list",
        "telemetry.replay.get",
    }
    exposed_action_names = set(action_catalog)
    scenario_runtime_supported = scenario_runtime_adapter.supported_scenarios()
    mission_runtime_supported = mission_runtime_adapter.supported_missions()
    vehicle_runtime_supported = vehicle_runtime_adapter.supported_actions()
    mission_backed_scenarios = {"patrol_basic"} & mission_runtime_supported
    scenario_surface_supported = scenario_runtime_supported | mission_backed_scenarios

    def resolve_capability_catalog() -> list[dict[str, Any]]:
        resolved = []
        for definition in INITIAL_CAPABILITY_CATALOG:
            action_names = set(definition.action_names)
            implemented = sorted(name for name in definition.action_names if name in implemented_action_names)
            missing = sorted(name for name in definition.action_names if name not in exposed_action_names)

            scenario_name = definition.constraints.get("scenario_name")
            if scenario_name and scenario_name not in registry_by_name:
                status = CapabilityStatus.UNAVAILABLE
            elif scenario_name and scenario_name not in scenario_surface_supported:
                status = CapabilityStatus.EXPERIMENTAL
            elif action_names and action_names.issubset(implemented_action_names):
                status = CapabilityStatus.AVAILABLE
            elif missing:
                status = CapabilityStatus.UNAVAILABLE
            else:
                status = CapabilityStatus.EXPERIMENTAL

            constraints = {
                **definition.constraints,
                "runtime_action_coverage": {
                    "implemented_actions": implemented,
                    "missing_actions": missing,
                },
            }
            resolved.append(replace(definition, status=status, constraints=constraints).to_dict())
        return resolved

    def runtime_artifacts(session_id: str) -> tuple[dict[str, Any], ...]:
        paths = runtime.paths_for(session_id)
        return (
            {
                "artifact_type": "runtime_dir",
                "uri": str(paths.runtime_dir),
                "description": "control-plane managed runtime directory",
            },
            {
                "artifact_type": "log_dir",
                "uri": str(paths.log_dir),
                "description": "control-plane managed log directory",
            },
        )

    def runtime_components_for_transition(
        *,
        mode: SessionMode,
        session_id: str,
        phase: str,
    ) -> tuple[SimulationComponent, ...]:
        paths = runtime.paths_for(session_id)
        return (
            SimulationComponent(
                component_name="px4_sitl",
                component_type="process",
                status=phase,
                health_summary=f"pid_file={paths.px4_pid_file}",
            ),
            SimulationComponent(
                component_name="micro_xrce_agent",
                component_type="process",
                status=phase,
                health_summary=f"pid_file={paths.xrce_pid_file}",
            ),
            SimulationComponent(
                component_name="runtime_paths",
                component_type="filesystem",
                status="ready",
                health_summary=f"runtime_dir={paths.runtime_dir}; log_dir={paths.log_dir}; mode={mode.value}",
            ),
        )

    def rebuild_session(
        current: SimulationSession,
        *,
        status: SimulationSessionStatus,
        mode: SessionMode | None = None,
        session_id: str | None = None,
        components: tuple[SimulationComponent, ...] | None = None,
        started_at: str | None = None,
        stopped_at: str | None = None,
    ) -> SimulationSession:
        return SimulationSession(
            session_id=session_id or current.session_id,
            status=status,
            mode=mode or current.mode,
            environment=current.environment,
            components=components or current.components,
            started_at=started_at if started_at is not None else current.started_at,
            stopped_at=stopped_at if stopped_at is not None else current.stopped_at,
        )

    def refresh_session() -> SimulationSession:
        current = session_store.current()
        if current.session_id == "session-local-default" and current.status == SimulationSessionStatus.IDLE:
            return current

        inspection = runtime.inspect(current.session_id, current.mode, current.status)
        refreshed = rebuild_session(
            current,
            status=inspection.status,
            components=inspection.components,
            stopped_at=_now_iso() if inspection.status == SimulationSessionStatus.STOPPED else current.stopped_at,
        )
        return session_store.replace(refreshed)

    def require_scenario(scenario_name: str) -> dict[str, Any] | JSONResponse:
        scenario = registry_by_name.get(scenario_name)
        if scenario is None:
            return _error_response(
                status_code=404,
                code=ControlPlaneErrorCode.INVALID_REQUEST,
                message=f"unknown scenario: {scenario_name}",
                detail=f"supported scenarios: {', '.join(sorted(registry_by_name))}",
            )
        return scenario

    def create_run(name: str, session_id: str | None, *, run_kind: str) -> RunRecord:
        run = RunRecord(
            run_id=f"run_{uuid.uuid4().hex[:12]}",
            run_kind=run_kind,
            name=name,
            status=RunStatus.STARTING,
            session_id=session_id,
            started_at=_now_iso(),
            summary="control-plane lifecycle action started",
        )
        return run_store.upsert(run)

    def finish_run(
        run: RunRecord,
        *,
        status: RunStatus,
        summary: str,
        artifacts: tuple[dict[str, Any], ...] = (),
    ) -> RunRecord:
        updated = RunRecord(
            run_id=run.run_id,
            run_kind=run.run_kind,
            name=run.name,
            status=status,
            session_id=run.session_id,
            started_at=run.started_at,
            ended_at=_now_iso(),
            artifacts=tuple(artifact["uri"] for artifact in artifacts),
            summary=summary,
        )
        return run_store.upsert(updated)

    def correlated_session_id(run_id: str | None = None) -> str | None:
        current_session = session_store.current()
        if current_session.session_id == "session-local-default":
            return None
        _ = run_id
        return current_session.session_id

    def enrich_snapshot_payload(snapshot: dict[str, Any]) -> dict[str, Any]:
        enriched = dict(snapshot)
        if enriched.get("current_run_id") is None and enriched.get("run_id") is not None:
            enriched["current_run_id"] = enriched.get("run_id")
        if enriched.get("session_id") is None:
            enriched["session_id"] = correlated_session_id(str(enriched.get("run_id") or "") or None)
        return enriched

    def enrich_collection_payload(payload: dict[str, Any], *, run_id: str | None = None) -> dict[str, Any]:
        enriched = dict(payload)
        resolved_run_id = str(enriched.get("run_id") or run_id or "") or None
        if enriched.get("session_id") is None:
            enriched["session_id"] = correlated_session_id(resolved_run_id)
        return enriched

    def enrich_telemetry_run_summary(summary: dict[str, Any]) -> dict[str, Any]:
        enriched = dict(summary)
        if enriched.get("session_id") is None:
            enriched["session_id"] = correlated_session_id(str(enriched.get("run_id") or "") or None)
        return enriched

    def refresh_all_scenarios() -> None:
        for state in scenario_store.list_states():
            if state.active_run_id:
                try:
                    refresh_scenario_state(state.scenario_name)
                except (MissionRuntimeError, ScenarioRuntimeError):
                    continue

    def mission_observation(mission_name: str | None = None) -> MissionRuntimeObservation:
        observation = mission_runtime_adapter.get_status(mission_name)
        mission_run = mission_execution_run(observation.mission_id)
        if (
            mission_run is not None
            and mission_run.status in {RunStatus.QUEUED, RunStatus.STARTING, RunStatus.RUNNING}
            and observation.status in {MissionStatus.COMPLETED, MissionStatus.ABORTED, MissionStatus.FAILED}
        ):
            finish_run(
                mission_run,
                status=mission_run_status(observation),
                summary=observation.detail or f"{observation.mission_id} reached {observation.status.value}",
            )
        return observation

    def mission_definition_payload(mission_name: str | None = None) -> dict[str, Any]:
        observation = mission_observation(mission_name)
        effective_mission_name = mission_name or observation.mission_id or "patrol_basic"
        plan_ref = f"simulation/scenarios/{effective_mission_name}.json" if effective_mission_name in registry_by_name else ""
        payload = MissionDefinition(
            mission_id=effective_mission_name,
            mission_type="patrol" if effective_mission_name == "patrol_basic" else effective_mission_name,
            status=observation.status,
            plan_ref=plan_ref,
            constraints={
                "active": observation.active,
                "terminal": observation.terminal,
                "detail": observation.detail,
                "last_command": observation.last_command,
                "current_waypoint_index": observation.current_waypoint_index,
                "total_waypoints": observation.total_waypoints,
                "samples": observation.samples,
            },
            fallback_policy="return_to_home" if effective_mission_name == "patrol_basic" else "operator_defined",
            required_capabilities=("mission.control",),
        )
        return payload.to_dict()

    def mission_run_status(observation: MissionRuntimeObservation, *, cancel_requested: bool = False) -> RunStatus:
        if observation.status == MissionStatus.IDLE and not observation.active:
            return RunStatus.CANCELLED if cancel_requested else RunStatus.COMPLETED
        if observation.status == MissionStatus.COMPLETED:
            return RunStatus.COMPLETED
        if observation.status == MissionStatus.ABORTED:
            return RunStatus.CANCELLED if cancel_requested else RunStatus.FAILED
        if observation.status == MissionStatus.FAILED:
            return RunStatus.FAILED
        return RunStatus.RUNNING

    async def read_model_snapshot() -> dict[str, Any]:
        return await read_adapter.get_snapshot()

    def build_vehicle_record(snapshot: dict[str, Any]) -> VehicleRecord | None:
        vehicle_state = snapshot.get("vehicle_state") or {}
        if not vehicle_state:
            return None
        return VehicleRecord(
            vehicle_id="mark1-sim-vehicle",
            vehicle_type="x500",
            armed=bool(vehicle_state.get("armed", False)),
            flight_mode=str(vehicle_state.get("nav_state", "")),
            position=VehiclePosition(
                latitude_deg=float(vehicle_state["latitude_deg"]) if vehicle_state.get("latitude_deg") is not None else None,
                longitude_deg=float(vehicle_state["longitude_deg"]) if vehicle_state.get("longitude_deg") is not None else None,
                absolute_altitude_m=float(vehicle_state["absolute_altitude_m"]) if vehicle_state.get("absolute_altitude_m") is not None else None,
                relative_altitude_m=float(vehicle_state["relative_altitude_m"]) if vehicle_state.get("relative_altitude_m") is not None else None,
            ),
            altitude_m=float(vehicle_state["altitude_m"]) if vehicle_state.get("altitude_m") is not None else None,
            connected=bool(vehicle_state.get("connected", False)),
            health_summary=(
                f"connected={bool(vehicle_state.get('connected', False))}; "
                f"armed={bool(vehicle_state.get('armed', False))}; "
                f"failsafe={bool(vehicle_state.get('failsafe', False))}"
            ),
        )

    def build_safety_status(snapshot: dict[str, Any]) -> SafetyStatus:
        payload = snapshot.get("safety_status") or {}
        active_faults = tuple(safety_runtime_adapter.active_faults())
        active = bool(payload.get("active", False)) or bool(active_faults)
        state = "active" if active else "clear"
        detail = str(payload.get("detail", ""))
        rule = str(payload.get("rule", ""))
        action = str(payload.get("action", ""))
        summary_parts = [part for part in [rule, action, detail] if part]
        return SafetyStatus(
            state=state,
            active_faults=active_faults,
            summary=" | ".join(summary_parts) if summary_parts else "safety state clear",
        )

    def build_perception_status(snapshot: dict[str, Any]) -> dict[str, Any]:
        heartbeat = snapshot.get("perception_heartbeat") or {}
        tracked_object = snapshot.get("tracked_object") or {}
        latest_event = snapshot.get("perception_event") or {}
        latest_event_kind = None
        latest_by_kind = snapshot.get("latest_by_kind") or {}
        if isinstance(latest_by_kind.get("perception_event"), dict):
            latest_event_kind = str(latest_by_kind["perception_event"].get("kind") or "") or None
        if latest_event_kind is None:
            latest_event_kind = str(latest_event.get("kind") or latest_event.get("event_type") or "") or None

        heartbeat_healthy = bool(heartbeat.get("healthy", False))
        tracked = bool(tracked_object.get("tracked", False))
        label = str(tracked_object.get("label", "")).strip() or None
        pipeline_latency = heartbeat.get("pipeline_latency_s")
        frame_age = heartbeat.get("frame_age_s")

        detail_parts = []
        detail_parts.append("heartbeat ok" if heartbeat_healthy else "heartbeat stale")
        detail_parts.append("tracked object present" if tracked else "no tracked object")
        if label:
            detail_parts.append(f"label={label}")
        if latest_event_kind:
            detail_parts.append(f"event={latest_event_kind}")
        if pipeline_latency is not None:
            detail_parts.append(f"latency={float(pipeline_latency):.3f}s")

        payload = PerceptionStatus(
            healthy=heartbeat_healthy,
            detections_available=tracked or bool(latest_event),
            detail=" | ".join(detail_parts),
            last_heartbeat_age_ms=(int(float(frame_age) * 1000) if frame_age is not None else None),
        ).to_dict()
        payload.update(
            {
                "status": "healthy" if heartbeat_healthy else "degraded",
                "tracked": tracked,
                "label": label,
                "confidence": (
                    float(tracked_object["confidence"]) if tracked_object.get("confidence") is not None else None
                ),
                "pipeline_latency_s": (float(pipeline_latency) if pipeline_latency is not None else None),
                "frame_age_s": (float(frame_age) if frame_age is not None else None),
                "summary": payload["detail"],
                "last_event_kind": latest_event_kind,
            }
        )
        return payload

    def build_perception_stream_status(snapshot: dict[str, Any]) -> dict[str, Any]:
        heartbeat = snapshot.get("perception_heartbeat") or {}
        stream_url = (
            os.getenv("MARK1_CAMERA_STREAM_URL", "").strip()
            or os.getenv("CONTROL_API_PERCEPTION_STREAM_URL", "").strip()
        )
        stream_source = os.getenv("CONTROL_API_PERCEPTION_STREAM_SOURCE", "").strip()
        if stream_url:
            payload = PerceptionStreamStatus(
                stream_available=True,
                source=stream_source or stream_url,
                detail="camera stream proxy configured for operator access",
                fps=float(heartbeat["fps"]) if heartbeat.get("fps") is not None else None,
            ).to_dict()
            payload.update(
                {
                    "available": True,
                    "mode": "proxy",
                    "summary": payload["detail"],
                    "stream_url": stream_url,
                }
            )
            return payload
        payload = PerceptionStreamStatus(
            stream_available=False,
            source="",
            detail=(
                "configure MARK1_CAMERA_STREAM_URL or publish the simulated camera feed via "
                "robotics/ros2_ws/scripts/publish_sim_camera_stream.py"
            ),
            fps=float(heartbeat["fps"]) if heartbeat.get("fps") is not None else None,
        ).to_dict()
        payload.update(
            {
                "available": False,
                "mode": "unavailable",
                "summary": payload["detail"],
                "stream_url": None,
            }
        )
        return payload

    async def read_vehicle_record() -> VehicleRecord | None:
        snapshot = await read_model_snapshot()
        return build_vehicle_record(snapshot)

    def telemetry_session_to_run(payload: dict[str, Any], *, current_run_id: str | None) -> RunRecord:
        run_id = str(payload.get("run_id", "")).strip()
        status = RunStatus.RUNNING if run_id and run_id == current_run_id else RunStatus.COMPLETED
        summary_parts = [f"{int(payload.get('event_count', 0))} events", f"{int(payload.get('metrics_count', 0))} metrics"]
        last_kind = str(payload.get("last_kind", "")).strip()
        if last_kind:
            summary_parts.append(f"last={last_kind}")
        raw_session_id = payload.get("session_id")
        session_id = None
        if raw_session_id is not None:
            session_id = str(raw_session_id).strip() or None
        if session_id is None:
            session_id = correlated_session_id(run_id or None)
        return RunRecord(
            run_id=run_id,
            run_kind="telemetry_session",
            name=f"telemetry:{run_id}",
            status=status,
            session_id=session_id,
            started_at=_iso_from_ns(payload.get("started_at_ns")),
            ended_at=None if status == RunStatus.RUNNING else _iso_from_ns(payload.get("updated_at_ns")),
            summary=", ".join(summary_parts),
        )

    def scenario_artifacts(*, scenario_name: str, result_path: str | None, log_path: str | None) -> tuple[dict[str, Any], ...]:
        artifacts: list[dict[str, Any]] = []
        if result_path:
            artifacts.append(
                {
                    "artifact_type": "scenario_result",
                    "uri": result_path,
                    "description": f"{scenario_name} result payload",
                }
            )
        if log_path:
            artifacts.append(
                {
                    "artifact_type": "scenario_log",
                    "uri": log_path,
                    "description": f"{scenario_name} runtime log",
                }
            )
        return tuple(artifacts)

    def create_scenario_state(*, scenario: dict[str, Any]) -> ScenarioState:
        current = scenario_store.get(scenario["scenario_name"])
        if current is not None:
            return current
        created = ScenarioState(
            scenario_name=scenario["scenario_name"],
            executor_type=scenario["executor_type"],
            summary="scenario has not been executed by the control plane yet",
        )
        return scenario_store.replace(created)

    def refresh_scenario_state(scenario_name: str) -> ScenarioState | None:
        scenario = registry_by_name.get(scenario_name)
        if scenario is None:
            return None

        current = create_scenario_state(scenario=scenario)
        if not current.active_run_id:
            return current

        if current.scenario_name in mission_backed_scenarios:
            observation = mission_observation(current.scenario_name)
            inspection_status = mission_run_status(observation, cancel_requested=current.cancel_requested)
            inspection_summary = observation.detail or f"mission phase={observation.status.value}"
            if inspection_status == RunStatus.RUNNING:
                if current.status != inspection_status.value or current.summary != inspection_summary:
                    current = scenario_store.replace(
                        ScenarioState(
                            scenario_name=current.scenario_name,
                            executor_type=current.executor_type,
                            status=inspection_status.value,
                            active_run_id=current.active_run_id,
                            last_run_id=current.last_run_id,
                            process_id=current.process_id,
                            result_path=current.result_path,
                            log_path=current.log_path,
                            summary=inspection_summary,
                            started_at=current.started_at,
                            ended_at=current.ended_at,
                            cancel_requested=current.cancel_requested,
                        )
                    )
                return current

            run = run_store.get(current.active_run_id)
            if run is not None and run.status in {RunStatus.STARTING, RunStatus.RUNNING, RunStatus.QUEUED}:
                finish_run(
                    run,
                    status=inspection_status,
                    summary=inspection_summary,
                )

            completed = ScenarioState(
                scenario_name=current.scenario_name,
                executor_type=current.executor_type,
                status=inspection_status.value,
                active_run_id=None,
                last_run_id=current.last_run_id,
                process_id=None,
                result_path=current.result_path,
                log_path=current.log_path,
                summary=inspection_summary,
                started_at=current.started_at,
                ended_at=_now_iso(),
                cancel_requested=current.cancel_requested,
            )
            return scenario_store.replace(completed)

        inspection = scenario_runtime_adapter.inspect(
            scenario_name=current.scenario_name,
            run_id=current.active_run_id,
        )

        if inspection.status in {RunStatus.STARTING, RunStatus.RUNNING}:
            if current.status != inspection.status.value or current.summary != inspection.summary:
                current = scenario_store.replace(
                    ScenarioState(
                        scenario_name=current.scenario_name,
                        executor_type=current.executor_type,
                        status=inspection.status.value,
                        active_run_id=current.active_run_id,
                        last_run_id=current.last_run_id,
                        process_id=current.process_id,
                        result_path=current.result_path,
                        log_path=current.log_path,
                        summary=inspection.summary,
                        started_at=current.started_at,
                        ended_at=current.ended_at,
                        cancel_requested=current.cancel_requested,
                    )
                )
            return current

        run = run_store.get(current.active_run_id)
        if run is not None and run.status in {RunStatus.STARTING, RunStatus.RUNNING}:
            finish_run(
                run,
                status=inspection.status,
                summary=inspection.summary,
                artifacts=inspection.artifacts,
            )

        completed = ScenarioState(
            scenario_name=current.scenario_name,
            executor_type=current.executor_type,
            status=inspection.status.value,
            active_run_id=None,
            last_run_id=current.last_run_id,
            process_id=None,
            result_path=current.result_path,
            log_path=current.log_path,
            summary=inspection.summary,
            started_at=current.started_at,
            ended_at=_now_iso(),
            cancel_requested=current.cancel_requested,
        )
        return scenario_store.replace(completed)

    def scenario_status_payload(scenario_name: str) -> dict[str, Any]:
        scenario = registry_by_name[scenario_name]
        state = refresh_scenario_state(scenario_name) or create_scenario_state(scenario=scenario)
        payload = ScenarioStatus(
            scenario_name=scenario_name,
            status=RunStatus(state.status) if state.status else None,
            active_run_id=state.active_run_id,
            last_run_id=state.last_run_id,
            summary=state.summary,
        )
        return payload.to_dict()

    def scenario_run_target(scenario_name: str) -> RunRecord | None:
        for run in reversed(run_store.list_runs()):
            if run.run_kind == "scenario_execution" and run.name == f"scenario.run:{scenario_name}":
                return run
        return None

    def mission_execution_run(mission_name: str) -> RunRecord | None:
        for run in reversed(run_store.list_runs()):
            if run.run_kind == "mission_execution" and run.name == f"mission.start:{mission_name}":
                return run
        return None

    def active_scenario_state() -> ScenarioState | None:
        active = scenario_store.active_state()
        if active is None:
            return None
        return refresh_scenario_state(active.scenario_name)

    def scenario_run_request_run_id(payload: ActionInvocationIn) -> str | None:
        raw_run_id = payload.input.get("run_id")
        if raw_run_id is None:
            return None
        return str(raw_run_id)

    def extract_mission_name(payload: ActionInvocationIn, *, default: str | None = None) -> str | JSONResponse:
        raw_name = payload.input.get("mission_name", default)
        if raw_name is None:
            return _error_response(
                status_code=400,
                code=ControlPlaneErrorCode.INVALID_REQUEST,
                message="mission_name is required",
                detail="use mission_name=patrol_basic for the Mark 1 mission surface",
            )
        return str(raw_name)

    def extract_mode(payload: ActionInvocationIn, *, fallback: SessionMode = SessionMode.HEADLESS) -> SessionMode | JSONResponse:
        raw_mode = payload.input.get("mode")
        if raw_mode is None:
            return fallback
        try:
            return SessionMode(str(raw_mode))
        except ValueError:
            return _error_response(
                status_code=400,
                code=ControlPlaneErrorCode.INVALID_REQUEST,
                message=f"unsupported simulation mode: {raw_mode}",
                detail="use one of: headless, visual",
            )

    app = FastAPI(title="drone control api", version="0.1.0")
    cors_origins = _cors_allow_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.session_store = session_store
    app.state.run_store = run_store
    app.state.scenario_store = scenario_store
    app.state.read_model_adapter = read_adapter
    app.state.scenario_registry = registry
    app.state.simulation_runtime = runtime
    app.state.scenario_runtime = scenario_runtime_adapter
    app.state.mission_runtime = mission_runtime_adapter
    app.state.vehicle_runtime = vehicle_runtime_adapter
    app.state.safety_runtime = safety_runtime_adapter
    app.state.control_state_root = control_state_root

    @app.get("/api/v1/health")
    async def health() -> dict[str, Any]:
        current = refresh_session()
        return {
            "status": "ok",
            "simulation_runtime_ready": current.status == SimulationSessionStatus.ACTIVE,
        }

    @app.get("/api/v1/control/status")
    async def control_status() -> dict[str, Any]:
        current = refresh_session()
        refresh_all_scenarios()
        return _response_envelope(
            {
                "service": {
                    "name": "control-api",
                    "phase": "R15",
                    "mode": "final-acceptance",
                    "status": "ok",
                },
                "session": current.to_dict(),
                "runs": run_store.summary(),
                "catalog": {
                    "action_count": len(INITIAL_ACTION_CATALOG),
                    "capability_count": len(resolve_capability_catalog()),
                    "scenario_count": len(registry),
                },
            }
        )

    @app.get("/api/v1/control/simulation/status")
    async def simulation_status() -> dict[str, Any]:
        return _response_envelope(refresh_session().to_dict())

    @app.get("/api/v1/control/actions")
    async def actions() -> dict[str, Any]:
        return _response_envelope([definition.to_dict() for definition in INITIAL_ACTION_CATALOG])

    @app.get("/api/v1/control/capabilities")
    async def capabilities() -> dict[str, Any]:
        return _response_envelope(resolve_capability_catalog())

    @app.get("/api/v1/control/scenarios")
    async def scenarios() -> dict[str, Any]:
        return _response_envelope([public_scenario_definition(entry) for entry in registry])

    @app.get("/api/v1/control/scenarios/{scenario_name}/status")
    async def scenario_status(scenario_name: str):
        scenario = require_scenario(scenario_name)
        if isinstance(scenario, JSONResponse):
            return scenario
        return _response_envelope(scenario_status_payload(scenario_name))

    @app.get("/api/v1/control/missions/status", response_model=None)
    async def mission_status():
        try:
            return _response_envelope(mission_definition_payload("patrol_basic"))
        except MissionRuntimeError as exc:
            return _error_response(
                status_code=_status_code_for_control_plane_code(exc.code),
                code=exc.code,
                message=exc.message,
                detail=exc.detail,
            )

    @app.get("/api/v1/control/safety/status", response_model=None)
    async def safety_status():
        try:
            snapshot = await read_model_snapshot()
        except Exception as exc:
            return _error_response(
                status_code=502,
                code=ControlPlaneErrorCode.DEPENDENCY_UNAVAILABLE,
                message="read model adapter unavailable for safety status",
                detail=str(exc),
            )
        return _response_envelope(build_safety_status(snapshot).to_dict())

    @app.get("/api/v1/control/perception/status", response_model=None)
    async def perception_status():
        try:
            snapshot = await read_model_snapshot()
        except Exception as exc:
            return _error_response(
                status_code=502,
                code=ControlPlaneErrorCode.DEPENDENCY_UNAVAILABLE,
                message="read model adapter unavailable for perception status",
                detail=str(exc),
            )
        return _response_envelope(build_perception_status(snapshot))

    @app.get("/api/v1/control/perception/stream/status", response_model=None)
    async def perception_stream_status():
        try:
            snapshot = await read_model_snapshot()
        except Exception as exc:
            return _error_response(
                status_code=502,
                code=ControlPlaneErrorCode.DEPENDENCY_UNAVAILABLE,
                message="read model adapter unavailable for perception stream status",
                detail=str(exc),
            )
        return _response_envelope(build_perception_stream_status(snapshot))

    @app.get("/api/v1/read/snapshot", response_model=None)
    async def read_snapshot():
        try:
            snapshot = enrich_snapshot_payload(await read_adapter.get_snapshot())
        except Exception as exc:
            return _error_response(
                status_code=502,
                code=ControlPlaneErrorCode.DEPENDENCY_UNAVAILABLE,
                message="read model adapter unavailable",
                detail=str(exc),
            )
        return _response_envelope(TelemetrySnapshot(**snapshot).to_dict())

    @app.get("/api/v1/read/metrics", response_model=None)
    async def read_metrics(run_id: str | None = Query(default=None), limit: int = Query(default=100, ge=1, le=5000)):
        try:
            metrics = enrich_collection_payload(await read_adapter.get_metrics(run_id=run_id, limit=limit), run_id=run_id)
        except Exception as exc:
            return _error_response(
                status_code=502,
                code=ControlPlaneErrorCode.DEPENDENCY_UNAVAILABLE,
                message="read model adapter unavailable for metrics",
                detail=str(exc),
            )
        return _response_envelope(
            TelemetryMetrics(
                run_id=metrics.get("run_id"),
                session_id=metrics.get("session_id"),
                metrics=tuple(metrics.get("metrics", [])),
                source=str(metrics.get("source", "telemetry_api")),
            ).to_dict()
        )

    @app.get("/api/v1/read/events", response_model=None)
    async def read_events(
        run_id: str | None = Query(default=None),
        kind: str | None = Query(default=None),
        limit: int = Query(default=100, ge=1, le=5000),
    ):
        try:
            events = enrich_collection_payload(
                await read_adapter.get_events(run_id=run_id, kind=kind, limit=limit),
                run_id=run_id,
            )
        except Exception as exc:
            return _error_response(
                status_code=502,
                code=ControlPlaneErrorCode.DEPENDENCY_UNAVAILABLE,
                message="read model adapter unavailable for events",
                detail=str(exc),
            )
        return _response_envelope(
            TelemetryEvents(
                run_id=events.get("run_id"),
                session_id=events.get("session_id"),
                events=tuple(events.get("events", [])),
                source=str(events.get("source", "telemetry_api")),
            ).to_dict()
        )

    @app.get("/api/v1/read/runs")
    async def read_runs() -> dict[str, Any]:
        refresh_all_scenarios()
        merged_runs: dict[str, RunRecord] = {item.run_id: item for item in run_store.list_runs()}
        current_telemetry_run_id: str | None = None
        try:
            snapshot = enrich_snapshot_payload(await read_adapter.get_snapshot())
            current_telemetry_run_id = str(snapshot.get("current_run_id") or snapshot.get("run_id") or "").strip() or None
            telemetry_summaries = await read_adapter.list_runs()
        except Exception as exc:
            return _error_response(
                status_code=502,
                code=ControlPlaneErrorCode.DEPENDENCY_UNAVAILABLE,
                message="read model adapter unavailable for runs",
                detail=str(exc),
            )

        enriched_telemetry_summaries = [enrich_telemetry_run_summary(item) for item in telemetry_summaries]
        for item in enriched_telemetry_summaries:
            telemetry_run = telemetry_session_to_run(item, current_run_id=current_telemetry_run_id)
            if telemetry_run.run_id and telemetry_run.run_id not in merged_runs:
                merged_runs[telemetry_run.run_id] = telemetry_run

        return _response_envelope(
            RunList(
                runs=tuple(merged_runs.values()),
                telemetry_runs=tuple(enriched_telemetry_summaries),
                current_telemetry_run_id=current_telemetry_run_id,
            ).to_dict()
        )

    @app.get("/api/v1/read/replay", response_model=None)
    async def read_replay(run_id: str = Query(...), limit: int = Query(default=500, ge=1, le=5000)):
        try:
            replay = enrich_collection_payload(await read_adapter.get_replay(run_id=run_id, limit=limit), run_id=run_id)
            replay_snapshot = replay.get("snapshot")
            if isinstance(replay_snapshot, dict):
                replay["snapshot"] = enrich_snapshot_payload(replay_snapshot)
        except Exception as exc:
            return _error_response(
                status_code=502,
                code=ControlPlaneErrorCode.DEPENDENCY_UNAVAILABLE,
                message="read model adapter unavailable for replay",
                detail=str(exc),
            )
        return _response_envelope(
            TelemetryReplay(
                run_id=str(replay.get("run_id", run_id)),
                session_id=replay.get("session_id"),
                snapshot=dict(replay.get("snapshot", {})),
                events=tuple(replay.get("events", [])),
                metrics=tuple(replay.get("metrics", [])),
            ).to_dict()
        )

    @app.post("/api/v1/control/simulation/start", response_model=None)
    async def simulation_start(payload: ActionInvocationIn):
        current = refresh_session()
        if current.status in {
            SimulationSessionStatus.STARTING,
            SimulationSessionStatus.ACTIVE,
            SimulationSessionStatus.DEGRADED,
        }:
            return _error_response(
                status_code=409,
                code=ControlPlaneErrorCode.INVALID_STATE,
                message="simulation runtime is already active",
                detail=f"current session status is {current.status.value}",
            )

        mode = extract_mode(payload)
        if isinstance(mode, JSONResponse):
            return mode

        session_id = f"session_{uuid.uuid4().hex[:12]}"
        starting_session = rebuild_session(
            current,
            status=SimulationSessionStatus.STARTING,
            session_id=session_id,
            mode=mode,
            components=runtime_components_for_transition(
                mode=mode,
                session_id=session_id,
                phase="starting",
            ),
            started_at=_now_iso(),
            stopped_at=None,
        )
        session_store.replace(starting_session)
        run = create_run("simulation.start", session_id, run_kind="simulation_lifecycle")

        try:
            runtime.check(session_id, mode)
            runtime.start(session_id, mode)
            inspection = runtime.inspect(session_id, mode, SimulationSessionStatus.STARTING)
        except SimulationRuntimeError as exc:
            failed_session = rebuild_session(
                starting_session,
                status=SimulationSessionStatus.FAILED,
                components=runtime_components_for_transition(
                    mode=mode,
                    session_id=session_id,
                    phase="failed",
                ),
            )
            session_store.replace(failed_session)
            finish_run(run, status=RunStatus.FAILED, summary=exc.message)
            return _error_response(
                status_code=_status_code_for_runtime_error(exc),
                code=exc.code,
                message=exc.message,
                detail=exc.detail,
            )

        active_session = rebuild_session(
            starting_session,
            status=inspection.status,
            components=inspection.components,
        )
        session_store.replace(active_session)
        artifacts = runtime_artifacts(session_id)
        finish_run(run, status=RunStatus.COMPLETED, summary="simulation session started", artifacts=artifacts)
        return _response_envelope(
            _build_action_result(
                payload=payload,
                accepted=True,
                status=ActionExecutionStatus.COMPLETED,
                message="simulation session started",
                run_id=run.run_id,
                artifacts=artifacts,
            )
        )

    @app.post("/api/v1/control/simulation/stop", response_model=None)
    async def simulation_stop(payload: ActionInvocationIn):
        current = refresh_session()
        if current.status not in {
            SimulationSessionStatus.STARTING,
            SimulationSessionStatus.ACTIVE,
            SimulationSessionStatus.DEGRADED,
            SimulationSessionStatus.FAILED,
        }:
            return _error_response(
                status_code=409,
                code=ControlPlaneErrorCode.INVALID_STATE,
                message="simulation runtime is not active",
                detail=f"current session status is {current.status.value}",
            )

        stopping_session = rebuild_session(
            current,
            status=SimulationSessionStatus.STOPPING,
            components=runtime_components_for_transition(
                mode=current.mode,
                session_id=current.session_id,
                phase="stopping",
            ),
        )
        session_store.replace(stopping_session)
        run = create_run("simulation.stop", current.session_id, run_kind="simulation_lifecycle")

        try:
            runtime.stop(current.session_id, current.mode)
        except SimulationRuntimeError as exc:
            failed_session = rebuild_session(stopping_session, status=SimulationSessionStatus.FAILED)
            session_store.replace(failed_session)
            finish_run(run, status=RunStatus.FAILED, summary=exc.message)
            return _error_response(
                status_code=_status_code_for_runtime_error(exc),
                code=exc.code,
                message=exc.message,
                detail=exc.detail,
            )

        stopped_session = rebuild_session(
            stopping_session,
            status=SimulationSessionStatus.STOPPED,
            components=runtime_components_for_transition(
                mode=current.mode,
                session_id=current.session_id,
                phase="stopped",
            ),
            stopped_at=_now_iso(),
        )
        session_store.replace(stopped_session)
        artifacts = runtime_artifacts(current.session_id)
        finish_run(run, status=RunStatus.COMPLETED, summary="simulation session stopped", artifacts=artifacts)
        return _response_envelope(
            _build_action_result(
                payload=payload,
                accepted=True,
                status=ActionExecutionStatus.COMPLETED,
                message="simulation session stopped",
                run_id=run.run_id,
                artifacts=artifacts,
            )
        )

    @app.post("/api/v1/control/simulation/restart", response_model=None)
    async def simulation_restart(payload: ActionInvocationIn):
        current = refresh_session()
        mode = extract_mode(payload, fallback=current.mode)
        if isinstance(mode, JSONResponse):
            return mode

        if current.status in {
            SimulationSessionStatus.STARTING,
            SimulationSessionStatus.ACTIVE,
            SimulationSessionStatus.DEGRADED,
            SimulationSessionStatus.FAILED,
        }:
            try:
                runtime.stop(current.session_id, current.mode)
            except SimulationRuntimeError as exc:
                return _error_response(
                    status_code=_status_code_for_runtime_error(exc),
                    code=exc.code,
                    message=f"simulation restart failed during stop: {exc.message}",
                    detail=exc.detail,
                )

        session_id = f"session_{uuid.uuid4().hex[:12]}"
        restarting_session = rebuild_session(
            current,
            status=SimulationSessionStatus.STARTING,
            session_id=session_id,
            mode=mode,
            components=runtime_components_for_transition(
                mode=mode,
                session_id=session_id,
                phase="starting",
            ),
            started_at=_now_iso(),
            stopped_at=None,
        )
        session_store.replace(restarting_session)
        run = create_run("simulation.restart", session_id, run_kind="simulation_lifecycle")

        try:
            runtime.check(session_id, mode)
            runtime.start(session_id, mode)
            inspection = runtime.inspect(session_id, mode, SimulationSessionStatus.STARTING)
        except SimulationRuntimeError as exc:
            failed_session = rebuild_session(restarting_session, status=SimulationSessionStatus.FAILED)
            session_store.replace(failed_session)
            finish_run(run, status=RunStatus.FAILED, summary=exc.message)
            return _error_response(
                status_code=_status_code_for_runtime_error(exc),
                code=exc.code,
                message=exc.message,
                detail=exc.detail,
            )

        active_session = rebuild_session(
            restarting_session,
            status=inspection.status,
            components=inspection.components,
        )
        session_store.replace(active_session)
        artifacts = runtime_artifacts(session_id)
        finish_run(run, status=RunStatus.COMPLETED, summary="simulation session restarted", artifacts=artifacts)
        return _response_envelope(
            _build_action_result(
                payload=payload,
                accepted=True,
                status=ActionExecutionStatus.COMPLETED,
                message="simulation session restarted",
                run_id=run.run_id,
                artifacts=artifacts,
            )
        )

    @app.post("/api/v1/control/scenarios/{scenario_name}/run", response_model=None)
    async def scenario_run(scenario_name: str, payload: ActionInvocationIn):
        scenario = require_scenario(scenario_name)
        if isinstance(scenario, JSONResponse):
            return scenario

        current_session = refresh_session()
        if current_session.status not in {SimulationSessionStatus.ACTIVE, SimulationSessionStatus.DEGRADED}:
            return _error_response(
                status_code=409,
                code=ControlPlaneErrorCode.INVALID_STATE,
                message="scenario.run requires an active simulation session",
                detail=f"current session status is {current_session.status.value}",
            )

        active_state = scenario_store.active_state()
        if active_state is not None:
            active_state = refresh_scenario_state(active_state.scenario_name) or active_state
        if active_state is not None and active_state.active_run_id:
            return _error_response(
                status_code=409,
                code=ControlPlaneErrorCode.INVALID_STATE,
                message="another scenario is already running",
                detail=f"active scenario is {active_state.scenario_name}",
            )

        if scenario["control_plane_status"] != "available" or scenario_name not in scenario_surface_supported:
            return _error_response(
                status_code=501,
                code=ControlPlaneErrorCode.NOT_SUPPORTED,
                message=f"{scenario_name} is registered but not executable through the current scenario runtime",
                detail=str(scenario.get("phase_hint", "future Mark 1 phase")),
            )

        run = create_run(f"scenario.run:{scenario_name}", current_session.session_id, run_kind="scenario_execution")
        if scenario_name in mission_backed_scenarios:
            observation = mission_observation(scenario_name)
            if observation.status != MissionStatus.IDLE:
                finish_run(run, status=RunStatus.FAILED, summary=f"{scenario_name} is not idle")
                return _error_response(
                    status_code=409,
                    code=ControlPlaneErrorCode.INVALID_STATE,
                    message=f"{scenario_name} requires an idle mission state before a new run",
                    detail=f"current mission status is {observation.status.value}",
                )
            try:
                launch_artifacts = mission_runtime_adapter.start(scenario_name, payload.input)
            except MissionRuntimeError as exc:
                finish_run(run, status=RunStatus.FAILED, summary=exc.message)
                return _error_response(
                    status_code=_status_code_for_control_plane_code(exc.code),
                    code=exc.code,
                    message=exc.message,
                    detail=exc.detail,
                )
            process_id = None
            result_path = ""
            log_path = ""
            running_summary = f"{scenario_name} accepted by mission control"
        else:
            try:
                launch = scenario_runtime_adapter.start(
                    run_id=run.run_id,
                    scenario_name=scenario_name,
                    parameters=payload.input,
                )
            except ScenarioRuntimeError as exc:
                finish_run(run, status=RunStatus.FAILED, summary=exc.message)
                return _error_response(
                    status_code=_status_code_for_control_plane_code(exc.code),
                    code=exc.code,
                    message=exc.message,
                    detail=exc.detail,
                )

            process_id = launch.process_id
            launch_artifacts = launch.artifacts
            result_path = str(launch.result_path)
            log_path = str(launch.log_path)
            running_summary = f"{scenario_name} accepted by scenario runtime"
        running_run = RunRecord(
            run_id=run.run_id,
            run_kind=run.run_kind,
            name=run.name,
            status=RunStatus.RUNNING,
            session_id=run.session_id,
            started_at=run.started_at,
            ended_at=None,
            artifacts=tuple(artifact["uri"] for artifact in launch_artifacts),
            summary=running_summary,
        )
        run_store.upsert(running_run)
        scenario_store.replace(
            ScenarioState(
                scenario_name=scenario_name,
                executor_type=scenario["executor_type"],
                status=RunStatus.RUNNING.value,
                active_run_id=run.run_id,
                last_run_id=run.run_id,
                process_id=process_id,
                result_path=result_path,
                log_path=log_path,
                summary=f"{scenario_name} is running through the unified scenario surface",
                started_at=_now_iso(),
                cancel_requested=False,
            )
        )
        return _response_envelope(
            _build_action_result(
                payload=payload,
                accepted=True,
                status=ActionExecutionStatus.RUNNING,
                message=f"{scenario_name} started through the unified scenario surface",
                run_id=run.run_id,
                artifacts=launch_artifacts,
            )
        )

    @app.post("/api/v1/control/scenarios/{scenario_name}/cancel", response_model=None)
    async def scenario_cancel(scenario_name: str, payload: ActionInvocationIn):
        scenario = require_scenario(scenario_name)
        if isinstance(scenario, JSONResponse):
            return scenario
        state = refresh_scenario_state(scenario_name) or create_scenario_state(scenario=scenario)
        if not state.active_run_id:
            return _error_response(
                status_code=409,
                code=ControlPlaneErrorCode.INVALID_STATE,
                message=f"{scenario_name} has no active run to cancel",
                detail=state.summary,
            )

        cancel_run = create_run(f"scenario.cancel:{scenario_name}", refresh_session().session_id, run_kind="scenario_control")
        if scenario_name in mission_backed_scenarios:
            try:
                artifacts = mission_runtime_adapter.abort(scenario_name, reason="scenario.cancel requested by control plane")
            except MissionRuntimeError as exc:
                finish_run(cancel_run, status=RunStatus.FAILED, summary=exc.message)
                return _error_response(
                    status_code=_status_code_for_control_plane_code(exc.code),
                    code=exc.code,
                    message=exc.message,
                    detail=exc.detail,
                )
            inspection = None
        else:
            inspection = scenario_runtime_adapter.cancel(
                scenario_name=scenario_name,
                run_id=state.active_run_id,
            )
            artifacts = inspection.artifacts
        cancelled_state = scenario_store.replace(
            ScenarioState(
                scenario_name=scenario_name,
                executor_type=scenario["executor_type"],
                status=(inspection.status.value if inspection is not None else RunStatus.RUNNING.value),
                active_run_id=(None if inspection is not None else state.active_run_id),
                last_run_id=state.last_run_id,
                process_id=(None if inspection is not None else state.process_id),
                result_path=state.result_path,
                log_path=state.log_path,
                summary=(inspection.summary if inspection is not None else f"{scenario_name} abort requested through mission control"),
                started_at=state.started_at,
                ended_at=(_now_iso() if inspection is not None else state.ended_at),
                cancel_requested=True,
            )
        )
        original_run = run_store.get(state.active_run_id)
        if inspection is not None and original_run is not None and original_run.status in {RunStatus.STARTING, RunStatus.RUNNING}:
            finish_run(
                original_run,
                status=inspection.status,
                summary=inspection.summary,
                artifacts=artifacts,
            )
        finish_run(
            cancel_run,
            status=RunStatus.COMPLETED,
            summary=f"{scenario_name} cancellation requested through the control plane",
            artifacts=artifacts,
        )
        return _response_envelope(
            _build_action_result(
                payload=payload,
                accepted=True,
                status=ActionExecutionStatus.COMPLETED,
                message=f"{scenario_name} cancelled",
                run_id=cancel_run.run_id,
                artifacts=artifacts,
            )
        )

    @app.post("/api/v1/control/missions/start", response_model=None)
    async def mission_start(payload: ActionInvocationIn):
        current_session = refresh_session()
        if current_session.status not in {SimulationSessionStatus.ACTIVE, SimulationSessionStatus.DEGRADED}:
            return _error_response(
                status_code=409,
                code=ControlPlaneErrorCode.INVALID_STATE,
                message="mission.start requires an active simulation session",
                detail=f"current session status is {current_session.status.value}",
            )

        mission_name = extract_mission_name(payload, default="patrol_basic")
        if isinstance(mission_name, JSONResponse):
            return mission_name
        if mission_name not in mission_runtime_supported:
            return _error_response(
                status_code=501,
                code=ControlPlaneErrorCode.NOT_SUPPORTED,
                message=f"{mission_name} is not executable through the current mission surface",
                detail="only patrol_basic is materialized in R5",
            )

        active_state = scenario_store.active_state()
        if active_state is not None:
            active_state = refresh_scenario_state(active_state.scenario_name) or active_state
        if active_state is not None and active_state.active_run_id:
            return _error_response(
                status_code=409,
                code=ControlPlaneErrorCode.INVALID_STATE,
                message="another scenario is already running",
                detail=f"active scenario is {active_state.scenario_name}",
            )

        observation = mission_observation(mission_name)
        if observation.status != MissionStatus.IDLE:
            return _error_response(
                status_code=409,
                code=ControlPlaneErrorCode.INVALID_STATE,
                message="mission.start requires an idle mission state",
                detail=f"current mission status is {observation.status.value}",
            )

        run = create_run(f"mission.start:{mission_name}", current_session.session_id, run_kind="mission_execution")
        try:
            artifacts = mission_runtime_adapter.start(mission_name, payload.input)
        except MissionRuntimeError as exc:
            finish_run(run, status=RunStatus.FAILED, summary=exc.message)
            return _error_response(
                status_code=_status_code_for_control_plane_code(exc.code),
                code=exc.code,
                message=exc.message,
                detail=exc.detail,
            )

        run_store.upsert(
            RunRecord(
                run_id=run.run_id,
                run_kind=run.run_kind,
                name=run.name,
                status=RunStatus.RUNNING,
                session_id=run.session_id,
                started_at=run.started_at,
                ended_at=None,
                artifacts=tuple(artifact["uri"] for artifact in artifacts),
                summary=f"{mission_name} accepted by mission control",
            )
        )
        if mission_name in registry_by_name:
            scenario = registry_by_name[mission_name]
            scenario_store.replace(
                ScenarioState(
                    scenario_name=mission_name,
                    executor_type=scenario["executor_type"],
                    status=RunStatus.RUNNING.value,
                    active_run_id=run.run_id,
                    last_run_id=run.run_id,
                    process_id=None,
                    result_path="",
                    log_path="",
                    summary=f"{mission_name} is running through the mission control surface",
                    started_at=_now_iso(),
                    cancel_requested=False,
                )
            )
        return _response_envelope(
            _build_action_result(
                payload=payload,
                accepted=True,
                status=ActionExecutionStatus.RUNNING,
                message=f"{mission_name} started through mission control",
                run_id=run.run_id,
                artifacts=artifacts,
            )
        )

    @app.post("/api/v1/control/missions/abort", response_model=None)
    async def mission_abort(payload: ActionInvocationIn):
        mission_name = extract_mission_name(payload, default="patrol_basic")
        if isinstance(mission_name, JSONResponse):
            return mission_name
        if mission_name not in mission_runtime_supported:
            return _error_response(
                status_code=501,
                code=ControlPlaneErrorCode.NOT_SUPPORTED,
                message=f"{mission_name} is not executable through the current mission surface",
                detail="only patrol_basic is materialized in R5",
            )
        observation = mission_observation(mission_name)
        if observation.status in {MissionStatus.IDLE, MissionStatus.COMPLETED, MissionStatus.ABORTED, MissionStatus.FAILED}:
            return _error_response(
                status_code=409,
                code=ControlPlaneErrorCode.INVALID_STATE,
                message="mission is not active",
                detail=f"current mission status is {observation.status.value}",
            )

        run = create_run(f"mission.abort:{mission_name}", refresh_session().session_id, run_kind="mission_control")
        try:
            artifacts = mission_runtime_adapter.abort(mission_name, reason=str(payload.input.get("reason", "")))
        except MissionRuntimeError as exc:
            finish_run(run, status=RunStatus.FAILED, summary=exc.message)
            return _error_response(
                status_code=_status_code_for_control_plane_code(exc.code),
                code=exc.code,
                message=exc.message,
                detail=exc.detail,
            )

        state = scenario_store.get(mission_name)
        if state is not None and state.active_run_id:
            scenario_store.replace(
                ScenarioState(
                    scenario_name=state.scenario_name,
                    executor_type=state.executor_type,
                    status=state.status,
                    active_run_id=state.active_run_id,
                    last_run_id=state.last_run_id,
                    process_id=state.process_id,
                    result_path=state.result_path,
                    log_path=state.log_path,
                    summary=f"{mission_name} abort requested through mission control",
                    started_at=state.started_at,
                    ended_at=state.ended_at,
                    cancel_requested=True,
                )
            )
        finish_run(run, status=RunStatus.COMPLETED, summary=f"{mission_name} abort requested through mission control", artifacts=artifacts)
        return _response_envelope(
            _build_action_result(
                payload=payload,
                accepted=True,
                status=ActionExecutionStatus.COMPLETED,
                message=f"{mission_name} abort requested",
                run_id=run.run_id,
                artifacts=artifacts,
            )
        )

    @app.post("/api/v1/control/missions/reset", response_model=None)
    async def mission_reset(payload: ActionInvocationIn):
        mission_name = extract_mission_name(payload, default="patrol_basic")
        if isinstance(mission_name, JSONResponse):
            return mission_name
        if mission_name not in mission_runtime_supported:
            return _error_response(
                status_code=501,
                code=ControlPlaneErrorCode.NOT_SUPPORTED,
                message=f"{mission_name} is not executable through the current mission surface",
                detail="only patrol_basic is materialized in R5",
            )
        observation = mission_observation(mission_name)
        if observation.status not in {MissionStatus.COMPLETED, MissionStatus.ABORTED, MissionStatus.FAILED}:
            return _error_response(
                status_code=409,
                code=ControlPlaneErrorCode.INVALID_STATE,
                message="mission.reset requires a terminal mission state",
                detail=f"current mission status is {observation.status.value}",
            )

        run = create_run(f"mission.reset:{mission_name}", refresh_session().session_id, run_kind="mission_control")
        try:
            artifacts = mission_runtime_adapter.reset(mission_name, reason=str(payload.input.get("reason", "")))
        except MissionRuntimeError as exc:
            finish_run(run, status=RunStatus.FAILED, summary=exc.message)
            return _error_response(
                status_code=_status_code_for_control_plane_code(exc.code),
                code=exc.code,
                message=exc.message,
                detail=exc.detail,
            )

        finish_run(run, status=RunStatus.COMPLETED, summary=f"{mission_name} reset requested through mission control", artifacts=artifacts)
        return _response_envelope(
            _build_action_result(
                payload=payload,
                accepted=True,
                status=ActionExecutionStatus.COMPLETED,
                message=f"{mission_name} reset requested",
                run_id=run.run_id,
                artifacts=artifacts,
            )
        )

    @app.post("/api/v1/control/vehicles/{command}", response_model=None)
    async def vehicle_command(command: str, payload: ActionInvocationIn):
        action_name = f"vehicle.{command}"
        if action_name not in action_catalog:
            return _error_response(
                status_code=400,
                code=ControlPlaneErrorCode.INVALID_REQUEST,
                message=f"unsupported vehicle action: {command}",
                detail="use one of: arm, disarm, takeoff, land, return_to_home, goto",
            )
        if action_name not in vehicle_runtime_supported:
            return _error_response(
                status_code=501,
                code=ControlPlaneErrorCode.NOT_SUPPORTED,
                message=f"{action_name} is not supported by the current vehicle runtime",
                detail="vehicle runtime does not materialize this action in the current environment",
            )

        current_session = refresh_session()
        if current_session.status not in {SimulationSessionStatus.ACTIVE, SimulationSessionStatus.DEGRADED}:
            return _error_response(
                status_code=409,
                code=ControlPlaneErrorCode.INVALID_STATE,
                message=f"{action_name} requires an active simulation session",
                detail=f"current session status is {current_session.status.value}",
            )

        dispatch_payload = dict(payload.input)
        if action_name == "vehicle.goto":
            if dispatch_payload.get("latitude_deg") is None or dispatch_payload.get("longitude_deg") is None:
                return _error_response(
                    status_code=400,
                    code=ControlPlaneErrorCode.INVALID_REQUEST,
                    message="vehicle.goto requires latitude_deg and longitude_deg",
                    detail="provide product-level target coordinates in the action input",
                )
            if dispatch_payload.get("target_absolute_altitude_m") is None and dispatch_payload.get("relative_altitude_m") is not None:
                try:
                    vehicle = await read_vehicle_record()
                except Exception as exc:
                    return _error_response(
                        status_code=502,
                        code=ControlPlaneErrorCode.DEPENDENCY_UNAVAILABLE,
                        message="read model adapter unavailable for vehicle.goto altitude resolution",
                        detail=str(exc),
                    )
                if vehicle is None or vehicle.position.absolute_altitude_m is None:
                    return _error_response(
                        status_code=409,
                        code=ControlPlaneErrorCode.INVALID_STATE,
                        message="vehicle.goto requires absolute altitude context",
                        detail="vehicle absolute altitude is not yet available in the read model",
                    )
                dispatch_payload["target_absolute_altitude_m"] = (
                    float(vehicle.position.absolute_altitude_m) + float(dispatch_payload["relative_altitude_m"])
                )

        run = create_run(action_name, current_session.session_id, run_kind="vehicle_control")
        try:
            dispatch = vehicle_runtime_adapter.dispatch(action_name, dispatch_payload)
        except VehicleRuntimeError as exc:
            finish_run(run, status=RunStatus.FAILED, summary=exc.message)
            return _error_response(
                status_code=_status_code_for_control_plane_code(exc.code),
                code=exc.code,
                message=exc.message,
                detail=exc.detail,
            )

        finish_run(
            run,
            status=RunStatus.COMPLETED,
            summary=f"{action_name} requested through the vehicle control surface",
            artifacts=dispatch.artifacts,
        )
        return _response_envelope(
            _build_action_result(
                payload=payload,
                accepted=True,
                status=ActionExecutionStatus.COMPLETED,
                message=f"{action_name} requested",
                run_id=run.run_id,
                artifacts=dispatch.artifacts,
            )
        )

    @app.post("/api/v1/control/safety/faults/inject", response_model=None)
    async def safety_inject(payload: ActionInvocationIn):
        current_session = refresh_session()
        if current_session.status not in {SimulationSessionStatus.ACTIVE, SimulationSessionStatus.DEGRADED}:
            return _error_response(
                status_code=409,
                code=ControlPlaneErrorCode.INVALID_STATE,
                message="safety.inject_fault requires an active simulation session",
                detail=f"current session status is {current_session.status.value}",
            )
        fault_type = str(payload.input.get("fault_type", "")).strip()
        if not fault_type:
            return _error_response(
                status_code=400,
                code=ControlPlaneErrorCode.INVALID_REQUEST,
                message="fault_type is required",
                detail="provide a safety fault identifier such as gps_loss, rc_loss or data_link_loss",
            )
        run = create_run("safety.inject_fault", current_session.session_id, run_kind="safety_control")
        try:
            dispatch = safety_runtime_adapter.inject_fault(
                fault_type,
                value=float(payload.input.get("value", 0.0)),
                detail=str(payload.input.get("detail", "")),
            )
        except SafetyRuntimeError as exc:
            finish_run(run, status=RunStatus.FAILED, summary=exc.message)
            return _error_response(
                status_code=_status_code_for_control_plane_code(exc.code),
                code=exc.code,
                message=exc.message,
                detail=exc.detail,
            )
        finish_run(
            run,
            status=RunStatus.COMPLETED,
            summary=f"{dispatch.fault_type} injected through the safety control surface",
            artifacts=dispatch.artifacts,
        )
        return _response_envelope(
            _build_action_result(
                payload=payload,
                accepted=True,
                status=ActionExecutionStatus.COMPLETED,
                message=f"safety fault {dispatch.fault_type} injected",
                run_id=run.run_id,
                artifacts=dispatch.artifacts,
            )
        )

    @app.post("/api/v1/control/safety/faults/clear", response_model=None)
    async def safety_clear(payload: ActionInvocationIn):
        current_session = refresh_session()
        if current_session.status not in {SimulationSessionStatus.ACTIVE, SimulationSessionStatus.DEGRADED}:
            return _error_response(
                status_code=409,
                code=ControlPlaneErrorCode.INVALID_STATE,
                message="safety.clear_fault requires an active simulation session",
                detail=f"current session status is {current_session.status.value}",
            )
        fault_type = str(payload.input.get("fault_type", "")).strip()
        if not fault_type:
            return _error_response(
                status_code=400,
                code=ControlPlaneErrorCode.INVALID_REQUEST,
                message="fault_type is required",
                detail="provide the safety fault identifier to clear",
            )
        run = create_run("safety.clear_fault", current_session.session_id, run_kind="safety_control")
        try:
            dispatch = safety_runtime_adapter.clear_fault(fault_type)
        except SafetyRuntimeError as exc:
            finish_run(run, status=RunStatus.FAILED, summary=exc.message)
            return _error_response(
                status_code=_status_code_for_control_plane_code(exc.code),
                code=exc.code,
                message=exc.message,
                detail=exc.detail,
            )
        finish_run(
            run,
            status=RunStatus.COMPLETED,
            summary=f"{dispatch.fault_type} cleared through the safety control surface",
            artifacts=dispatch.artifacts,
        )
        return _response_envelope(
            _build_action_result(
                payload=payload,
                accepted=True,
                status=ActionExecutionStatus.COMPLETED,
                message=f"safety fault {dispatch.fault_type} cleared",
                run_id=run.run_id,
                artifacts=dispatch.artifacts,
            )
        )

    return app
