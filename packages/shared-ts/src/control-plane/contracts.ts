export const simulationSessionStatuses = [
  "idle",
  "starting",
  "active",
  "degraded",
  "stopping",
  "stopped",
  "failed",
] as const;
export type SimulationSessionStatus = (typeof simulationSessionStatuses)[number];

export const sessionModes = ["headless", "visual"] as const;
export type SessionMode = (typeof sessionModes)[number];

export const runStatuses = [
  "queued",
  "starting",
  "running",
  "completed",
  "failed",
  "cancelled",
  "timed_out",
] as const;
export type RunStatus = (typeof runStatuses)[number];

export const missionStatuses = [
  "idle",
  "arming",
  "takeoff",
  "hover",
  "patrol",
  "returning",
  "landing",
  "aborting",
  "completed",
  "aborted",
  "failed",
] as const;
export type MissionStatus = (typeof missionStatuses)[number];

export const actionCategories = [
  "simulation",
  "scenario",
  "mission",
  "vehicle",
  "safety",
  "perception",
  "telemetry",
  "discovery",
] as const;
export type ActionCategory = (typeof actionCategories)[number];

export const actionSyncModes = ["sync", "async", "stream"] as const;
export type ActionSyncMode = (typeof actionSyncModes)[number];

export const actionExecutionStatuses = [
  "accepted",
  "queued",
  "running",
  "completed",
  "failed",
  "rejected",
  "cancelled",
  "timed_out",
] as const;
export type ActionExecutionStatus = (typeof actionExecutionStatuses)[number];

export const actionAvailabilityScopes = [
  "none",
  "simulation_session",
  "run",
  "mission",
] as const;
export type ActionAvailabilityScope = (typeof actionAvailabilityScopes)[number];

export const scenarioExecutorTypes = [
  "mavsdk",
  "ros2_mission",
  "ros2_safety",
  "ros2_perception",
  "shell",
] as const;
export type ScenarioExecutorType = (typeof scenarioExecutorTypes)[number];

export const controlPlaneErrorCodes = [
  "invalid_request",
  "invalid_state",
  "not_supported",
  "dependency_unavailable",
  "timeout",
  "runtime_failure",
] as const;
export type ControlPlaneErrorCode = (typeof controlPlaneErrorCodes)[number];

export const safetyLevels = ["none", "advisory", "guarded", "critical"] as const;
export type SafetyLevel = (typeof safetyLevels)[number];

export const capabilityStatuses = ["available", "experimental", "unavailable"] as const;
export type CapabilityStatus = (typeof capabilityStatuses)[number];

export interface VehiclePosition {
  latitude_deg?: number;
  longitude_deg?: number;
  absolute_altitude_m?: number;
  relative_altitude_m?: number;
}

export interface VehicleRecord {
  vehicle_id: string;
  vehicle_type: string;
  armed: boolean;
  flight_mode: string;
  position: VehiclePosition;
  altitude_m?: number;
  connected: boolean;
  health_summary: string;
}

export interface SimulationComponent {
  component_name: string;
  component_type: string;
  status: string;
  health_summary?: string;
}

export interface SimulationEnvironment {
  environment_name: string;
  simulator_family: string;
  vehicle_profile: string;
  baseline: string;
}

export interface SimulationSession {
  session_id: string;
  status: SimulationSessionStatus;
  mode: SessionMode;
  environment: SimulationEnvironment;
  components: SimulationComponent[];
  started_at?: string;
  stopped_at?: string;
}

export interface RunRecord {
  run_id: string;
  run_kind: string;
  name: string;
  status: RunStatus;
  session_id?: string;
  started_at?: string;
  ended_at?: string;
  artifacts: string[];
  summary: string;
}

export interface MissionDefinition {
  mission_id: string;
  mission_type: string;
  status: MissionStatus;
  plan_ref: string;
  constraints: Record<string, unknown>;
  fallback_policy: string;
  required_capabilities: string[];
}

export interface ScenarioDefinition {
  scenario_name: string;
  scenario_kind: string;
  executor_type: ScenarioExecutorType;
  input_contract: string;
  output_contract: string;
  supports_visual: boolean;
  supports_headless: boolean;
}

export interface ScenarioStatus {
  scenario_name: string;
  status?: RunStatus;
  active_run_id?: string;
  last_run_id?: string;
  executor_type?: ScenarioExecutorType;
  summary?: string;
}

export interface SafetyFaultRecord {
  fault_type: string;
  active: boolean;
  value?: number;
  detail?: string;
  source?: string;
  raised_at?: string;
  cleared_at?: string;
}

export interface SafetyStatus {
  state: string;
  active_faults: SafetyFaultRecord[];
  summary?: string;
}

export interface PerceptionStatus {
  healthy: boolean;
  detections_available: boolean;
  detail?: string;
  last_heartbeat_age_ms?: number;
}

export interface PerceptionStreamStatus {
  stream_available: boolean;
  source?: string;
  detail?: string;
  fps?: number;
}

export interface RequestedBy {
  type: string;
  id: string;
}

export interface ArtifactRef {
  artifact_type: string;
  uri: string;
  description?: string;
}

export interface ControlPlaneError {
  code: ControlPlaneErrorCode;
  message: string;
  detail?: string;
}

export interface EmptyObject {}

export interface SimulationStartRequest {
  mode?: SessionMode;
  environment_name?: string;
  baseline?: string;
}

export interface SimulationStopRequest {
  force?: boolean;
}

export interface SimulationRestartRequest {
  mode?: SessionMode;
  force?: boolean;
}

export interface ScenarioRunRequest {
  scenario_name: string;
  parameters?: Record<string, unknown>;
}

export interface ScenarioCancelRequest {
  scenario_name: string;
  run_id?: string;
}

export interface ScenarioStatusQuery {
  scenario_name: string;
  run_id?: string;
}

export interface MissionStartRequest {
  mission_name: string;
  parameters?: Record<string, unknown>;
}

export interface MissionAbortRequest {
  reason?: string;
}

export interface MissionResetRequest {
  reason?: string;
}

export interface VehicleTakeoffRequest {
  target_altitude_m?: number;
}

export interface VehicleGotoRequest {
  latitude_deg: number;
  longitude_deg: number;
  relative_altitude_m?: number;
}

export interface SafetyFaultInjectionRequest {
  fault_type: string;
  value?: number;
  detail?: string;
}

export interface SafetyFaultClearRequest {
  fault_type: string;
}

export interface TelemetrySnapshot {
  current_run_id?: string;
  run_id?: string;
  session_id?: string;
  updated_at_ns?: number;
  vehicle_state: Record<string, unknown>;
  vehicle_command_status: Record<string, unknown>;
  mission_status: Record<string, unknown>;
  safety_status: Record<string, unknown>;
  tracked_object: Record<string, unknown>;
  perception_heartbeat: Record<string, unknown>;
  perception_event: Record<string, unknown>;
  latest_by_kind: Record<string, unknown>;
}

export interface TelemetryMetricsQuery {
  run_id?: string;
  limit?: number;
}

export interface TelemetryMetrics {
  run_id?: string;
  session_id?: string;
  metrics: Record<string, unknown>[];
  source?: string;
}

export interface TelemetryEventsQuery {
  run_id?: string;
  kind?: string;
  limit?: number;
}

export interface TelemetryEvents {
  run_id?: string;
  session_id?: string;
  events: Record<string, unknown>[];
  source?: string;
}

export interface RunList {
  runs: RunRecord[];
  telemetry_runs?: Record<string, unknown>[];
  current_telemetry_run_id?: string;
}

export interface TelemetryReplayQuery {
  run_id: string;
}

export interface TelemetryReplay {
  run_id: string;
  session_id?: string;
  snapshot: Record<string, unknown>;
  events: Record<string, unknown>[];
  metrics: Record<string, unknown>[];
}

export interface ActionRequest {
  action_name: string;
  target: string;
  request_id: string;
  session_id?: string;
  run_id?: string;
  input: Record<string, unknown>;
  requested_by: RequestedBy;
}

export interface ActionResult {
  request_id: string;
  accepted: boolean;
  status: ActionExecutionStatus;
  message: string;
  run_id?: string;
  artifacts: ArtifactRef[];
  errors: ControlPlaneError[];
}

export interface ActionAvailability {
  scope: ActionAvailabilityScope;
  allowed_statuses: string[];
}

export interface ActionDefinition {
  action_name: string;
  category: ActionCategory;
  description: string;
  input_schema: string;
  result_schema: string;
  target: string;
  sync_mode: ActionSyncMode;
  availability: ActionAvailability[];
  owner_runtime: string;
  read_only?: boolean;
}

export interface CapabilityDefinition {
  capability_name: string;
  version: string;
  description: string;
  action_names: string[];
  required_runtime_components: string[];
  constraints: Record<string, unknown>;
  owner_runtime: string;
  required_vehicle_type?: string;
  required_payloads?: string[];
  required_actuators?: string[];
  required_environment?: string[];
  safety_level?: SafetyLevel;
  status?: CapabilityStatus;
}

export interface ScenarioList {
  scenarios: ScenarioDefinition[];
}

export interface CapabilityList {
  capabilities: CapabilityDefinition[];
}
