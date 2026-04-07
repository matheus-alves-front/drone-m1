from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from typing import Any


def _serialize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {
            item.name: _serialize(getattr(value, item.name))
            for item in fields(value)
            if getattr(value, item.name) is not None
        }
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    return value


class SerializableModel:
    def to_dict(self) -> dict[str, Any]:
        return _serialize(self)


class SimulationSessionStatus(str, Enum):
    IDLE = "idle"
    STARTING = "starting"
    ACTIVE = "active"
    DEGRADED = "degraded"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class SessionMode(str, Enum):
    HEADLESS = "headless"
    VISUAL = "visual"


class RunStatus(str, Enum):
    QUEUED = "queued"
    STARTING = "starting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class MissionStatus(str, Enum):
    IDLE = "idle"
    ARMING = "arming"
    TAKEOFF = "takeoff"
    HOVER = "hover"
    PATROL = "patrol"
    RETURNING = "returning"
    LANDING = "landing"
    ABORTING = "aborting"
    COMPLETED = "completed"
    ABORTED = "aborted"
    FAILED = "failed"


class ActionCategory(str, Enum):
    SIMULATION = "simulation"
    SCENARIO = "scenario"
    MISSION = "mission"
    VEHICLE = "vehicle"
    SAFETY = "safety"
    PERCEPTION = "perception"
    TELEMETRY = "telemetry"
    DISCOVERY = "discovery"


class ActionSyncMode(str, Enum):
    SYNC = "sync"
    ASYNC = "async"
    STREAM = "stream"


class ActionExecutionStatus(str, Enum):
    ACCEPTED = "accepted"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class ActionAvailabilityScope(str, Enum):
    NONE = "none"
    SIMULATION_SESSION = "simulation_session"
    RUN = "run"
    MISSION = "mission"


class ScenarioExecutorType(str, Enum):
    MAVSDK = "mavsdk"
    ROS2_MISSION = "ros2_mission"
    ROS2_SAFETY = "ros2_safety"
    ROS2_PERCEPTION = "ros2_perception"
    SHELL = "shell"


class ControlPlaneErrorCode(str, Enum):
    INVALID_REQUEST = "invalid_request"
    INVALID_STATE = "invalid_state"
    NOT_SUPPORTED = "not_supported"
    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"
    TIMEOUT = "timeout"
    RUNTIME_FAILURE = "runtime_failure"


class SafetyLevel(str, Enum):
    NONE = "none"
    ADVISORY = "advisory"
    GUARDED = "guarded"
    CRITICAL = "critical"


class CapabilityStatus(str, Enum):
    AVAILABLE = "available"
    EXPERIMENTAL = "experimental"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class VehiclePosition(SerializableModel):
    latitude_deg: float | None = None
    longitude_deg: float | None = None
    absolute_altitude_m: float | None = None
    relative_altitude_m: float | None = None


@dataclass(frozen=True)
class VehicleRecord(SerializableModel):
    vehicle_id: str
    vehicle_type: str
    armed: bool
    flight_mode: str
    position: VehiclePosition
    altitude_m: float | None
    connected: bool
    health_summary: str


@dataclass(frozen=True)
class SimulationComponent(SerializableModel):
    component_name: str
    component_type: str
    status: str
    health_summary: str = ""


@dataclass(frozen=True)
class SimulationEnvironment(SerializableModel):
    environment_name: str
    simulator_family: str
    vehicle_profile: str
    baseline: str


@dataclass(frozen=True)
class SimulationSession(SerializableModel):
    session_id: str
    status: SimulationSessionStatus
    mode: SessionMode
    environment: SimulationEnvironment
    components: tuple[SimulationComponent, ...]
    started_at: str | None = None
    stopped_at: str | None = None


@dataclass(frozen=True)
class RunRecord(SerializableModel):
    run_id: str
    run_kind: str
    name: str
    status: RunStatus
    session_id: str | None
    started_at: str | None = None
    ended_at: str | None = None
    artifacts: tuple[str, ...] = ()
    summary: str = ""


@dataclass(frozen=True)
class MissionDefinition(SerializableModel):
    mission_id: str
    mission_type: str
    status: MissionStatus
    plan_ref: str
    constraints: dict[str, Any]
    fallback_policy: str
    required_capabilities: tuple[str, ...]


@dataclass(frozen=True)
class ScenarioDefinition(SerializableModel):
    scenario_name: str
    scenario_kind: str
    executor_type: ScenarioExecutorType
    input_contract: str
    output_contract: str
    supports_visual: bool
    supports_headless: bool


@dataclass(frozen=True)
class ScenarioStatus(SerializableModel):
    scenario_name: str
    status: RunStatus | None = None
    active_run_id: str | None = None
    last_run_id: str | None = None
    executor_type: ScenarioExecutorType | None = None
    summary: str = ""


@dataclass(frozen=True)
class SafetyFaultRecord(SerializableModel):
    fault_type: str
    active: bool
    value: float = 0.0
    detail: str = ""
    source: str = "operator"
    raised_at: str | None = None
    cleared_at: str | None = None


@dataclass(frozen=True)
class SafetyStatus(SerializableModel):
    state: str
    active_faults: tuple[SafetyFaultRecord, ...] = ()
    summary: str = ""


@dataclass(frozen=True)
class PerceptionStatus(SerializableModel):
    healthy: bool
    detections_available: bool
    detail: str = ""
    last_heartbeat_age_ms: int | None = None


@dataclass(frozen=True)
class PerceptionStreamStatus(SerializableModel):
    stream_available: bool
    source: str = ""
    detail: str = ""
    fps: float | None = None


@dataclass(frozen=True)
class RequestedBy(SerializableModel):
    type: str
    id: str


@dataclass(frozen=True)
class ArtifactRef(SerializableModel):
    artifact_type: str
    uri: str
    description: str = ""


@dataclass(frozen=True)
class ControlPlaneError(SerializableModel):
    code: ControlPlaneErrorCode
    message: str
    detail: str = ""


@dataclass(frozen=True)
class EmptyObject(SerializableModel):
    pass


@dataclass(frozen=True)
class SimulationStartRequest(SerializableModel):
    mode: SessionMode = SessionMode.HEADLESS
    environment_name: str | None = None
    baseline: str | None = None


@dataclass(frozen=True)
class SimulationStopRequest(SerializableModel):
    force: bool = False


@dataclass(frozen=True)
class SimulationRestartRequest(SerializableModel):
    mode: SessionMode | None = None
    force: bool = False


@dataclass(frozen=True)
class ScenarioRunRequest(SerializableModel):
    scenario_name: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ScenarioCancelRequest(SerializableModel):
    scenario_name: str
    run_id: str | None = None


@dataclass(frozen=True)
class ScenarioStatusQuery(SerializableModel):
    scenario_name: str
    run_id: str | None = None


@dataclass(frozen=True)
class MissionStartRequest(SerializableModel):
    mission_name: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MissionAbortRequest(SerializableModel):
    reason: str = ""


@dataclass(frozen=True)
class MissionResetRequest(SerializableModel):
    reason: str = ""


@dataclass(frozen=True)
class VehicleTakeoffRequest(SerializableModel):
    target_altitude_m: float | None = None


@dataclass(frozen=True)
class VehicleGotoRequest(SerializableModel):
    latitude_deg: float
    longitude_deg: float
    relative_altitude_m: float | None = None


@dataclass(frozen=True)
class SafetyFaultInjectionRequest(SerializableModel):
    fault_type: str
    value: float = 0.0
    detail: str = ""


@dataclass(frozen=True)
class SafetyFaultClearRequest(SerializableModel):
    fault_type: str


@dataclass(frozen=True)
class TelemetrySnapshot(SerializableModel):
    current_run_id: str | None = None
    run_id: str | None = None
    session_id: str | None = None
    updated_at_ns: int | None = None
    vehicle_state: dict[str, Any] = field(default_factory=dict)
    vehicle_command_status: dict[str, Any] = field(default_factory=dict)
    mission_status: dict[str, Any] = field(default_factory=dict)
    safety_status: dict[str, Any] = field(default_factory=dict)
    tracked_object: dict[str, Any] = field(default_factory=dict)
    perception_heartbeat: dict[str, Any] = field(default_factory=dict)
    perception_event: dict[str, Any] = field(default_factory=dict)
    latest_by_kind: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TelemetryMetricsQuery(SerializableModel):
    run_id: str | None = None
    limit: int = 100


@dataclass(frozen=True)
class TelemetryMetrics(SerializableModel):
    run_id: str | None = None
    session_id: str | None = None
    metrics: tuple[dict[str, Any], ...] = ()
    source: str = "telemetry_api"


@dataclass(frozen=True)
class TelemetryEventsQuery(SerializableModel):
    run_id: str | None = None
    kind: str | None = None
    limit: int = 100


@dataclass(frozen=True)
class TelemetryEvents(SerializableModel):
    run_id: str | None = None
    session_id: str | None = None
    events: tuple[dict[str, Any], ...] = ()
    source: str = "telemetry_api"


@dataclass(frozen=True)
class RunList(SerializableModel):
    runs: tuple[RunRecord, ...] = ()
    telemetry_runs: tuple[dict[str, Any], ...] = ()
    current_telemetry_run_id: str | None = None


@dataclass(frozen=True)
class TelemetryReplayQuery(SerializableModel):
    run_id: str


@dataclass(frozen=True)
class TelemetryReplay(SerializableModel):
    run_id: str
    session_id: str | None = None
    snapshot: dict[str, Any] = field(default_factory=dict)
    events: tuple[dict[str, Any], ...] = ()
    metrics: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class ActionRequest(SerializableModel):
    action_name: str
    target: str
    request_id: str
    session_id: str | None
    input: dict[str, Any]
    requested_by: RequestedBy
    run_id: str | None = None


@dataclass(frozen=True)
class ActionResult(SerializableModel):
    request_id: str
    accepted: bool
    status: ActionExecutionStatus
    message: str
    run_id: str | None = None
    artifacts: tuple[ArtifactRef, ...] = ()
    errors: tuple[ControlPlaneError, ...] = ()


@dataclass(frozen=True)
class ActionAvailability(SerializableModel):
    scope: ActionAvailabilityScope
    allowed_statuses: tuple[str, ...] = ()


@dataclass(frozen=True)
class ActionDefinition(SerializableModel):
    action_name: str
    category: ActionCategory
    description: str
    input_schema: str
    result_schema: str
    target: str
    sync_mode: ActionSyncMode
    availability: tuple[ActionAvailability, ...] = ()
    owner_runtime: str = ""
    read_only: bool = False


@dataclass(frozen=True)
class CapabilityDefinition(SerializableModel):
    capability_name: str
    version: str
    description: str
    action_names: tuple[str, ...]
    required_runtime_components: tuple[str, ...]
    constraints: dict[str, Any]
    owner_runtime: str
    required_vehicle_type: str = "aerial_multirotor"
    required_payloads: tuple[str, ...] = ()
    required_actuators: tuple[str, ...] = ()
    required_environment: tuple[str, ...] = ("simulation",)
    safety_level: SafetyLevel = SafetyLevel.GUARDED
    status: CapabilityStatus = CapabilityStatus.AVAILABLE


@dataclass(frozen=True)
class ScenarioList(SerializableModel):
    scenarios: tuple[ScenarioDefinition, ...] = ()


@dataclass(frozen=True)
class CapabilityList(SerializableModel):
    capabilities: tuple[CapabilityDefinition, ...] = ()
