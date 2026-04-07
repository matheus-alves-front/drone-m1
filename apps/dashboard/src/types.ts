export type ApiError = {
  code: string;
  message: string;
  detail?: string;
};

export type ApiEnvelope<T> = {
  status: string;
  data: T;
  errors: ApiError[];
};

export type ArtifactRef = {
  artifact_type: string;
  uri: string;
  description?: string;
};

export type ActionError = {
  code?: string;
  message?: string;
  detail?: string;
};

export type ActionResultPayload = {
  request_id: string;
  accepted: boolean;
  status: string;
  message: string;
  run_id?: string | null;
  artifacts: ArtifactRef[];
  errors: ActionError[];
};

export type SimulationEnvironment = {
  environment_name: string;
  simulator_family: string;
  vehicle_profile: string;
  baseline: string;
};

export type SimulationComponent = {
  component_name: string;
  component_type: string;
  status: string;
  health_summary: string;
};

export type SimulationSession = {
  session_id: string;
  status: string;
  mode: string;
  environment: SimulationEnvironment;
  components: SimulationComponent[];
  started_at?: string | null;
  stopped_at?: string | null;
};

export type RunRecord = {
  run_id: string;
  run_kind: string;
  name: string;
  status: string;
  session_id?: string | null;
  started_at?: string | null;
  ended_at?: string | null;
  artifacts: string[];
  summary: string;
};

export type TelemetryRunSummary = {
  run_id: string;
  session_id?: string | null;
  source?: string;
  started_at_ns?: number | null;
  updated_at_ns?: number | null;
  event_count: number;
  metrics_count: number;
  last_kind?: string | null;
  last_stamp_ns?: number | null;
};

export type RunListPayload = {
  runs: RunRecord[];
  telemetry_runs: TelemetryRunSummary[];
  current_telemetry_run_id?: string | null;
};

export type ControlStatusPayload = {
  service: {
    name: string;
    phase: string;
    mode: string;
    status: string;
  };
  session: SimulationSession;
  runs: {
    run_count: number;
    active_run: RunRecord | null;
  };
  catalog: {
    action_count: number;
    capability_count: number;
    scenario_count: number;
  };
};

export type CapabilityDefinition = {
  capability_name: string;
  status: string;
  action_names: string[];
  description?: string;
  constraints: Record<string, unknown>;
};

export type ScenarioEntry = {
  scenario_name: string;
  scenario_kind: string;
  input_contract: string;
  output_contract: string;
  supports_visual: boolean;
  supports_headless: boolean;
  objective: string;
  control_plane_status: string;
  phase_hint: string;
};

export type ScenarioStatusPayload = {
  scenario_name: string;
  status?: string | null;
  active_run_id?: string | null;
  last_run_id?: string | null;
  summary: string;
};

export type MissionDefinitionPayload = {
  mission_id: string;
  mission_type: string;
  status: string;
  plan_ref: string;
  constraints: Record<string, unknown>;
  fallback_policy: string;
  required_capabilities: string[];
};

export type SafetyFaultRecord = {
  fault_type: string;
  active: boolean;
  value?: number;
  detail?: string;
  source?: string;
  raised_at?: string | null;
  cleared_at?: string | null;
};

export type SafetySurfacePayload = {
  state: string;
  active_faults: SafetyFaultRecord[];
  summary: string;
};

export type PerceptionStatusPayload = {
  healthy: boolean;
  detections_available: boolean;
  detail?: string;
  last_heartbeat_age_ms?: number | null;
};

export type PerceptionStreamStatusPayload = {
  stream_available: boolean;
  detail?: string;
  stream_url?: string | null;
  source?: string | null;
  fps?: number | null;
};

export type StoredEnvelope = {
  run_id: string;
  session_id?: string | null;
  source: string;
  kind: string;
  topic: string;
  stamp_ns: number;
  payload: Record<string, unknown>;
  sequence: number;
  received_ns: number;
};

export type SnapshotResponse = {
  current_run_id?: string | null;
  run_id?: string | null;
  session_id?: string | null;
  updated_at_ns?: number | null;
  vehicle_state: Record<string, unknown>;
  vehicle_command_status: Record<string, unknown>;
  mission_status: Record<string, unknown>;
  safety_status: Record<string, unknown>;
  tracked_object: Record<string, unknown>;
  perception_heartbeat: Record<string, unknown>;
  perception_event: Record<string, unknown>;
  latest_by_kind: Record<string, StoredEnvelope>;
};

export type MetricRecord = {
  seq: number;
  run_id: string;
  session_id?: string | null;
  stamp_ns?: number;
  mission_phase?: string;
  mission_active?: boolean;
  altitude_m?: number | null;
  relative_altitude_m?: number | null;
  failsafe?: boolean | null;
  tracked?: boolean | null;
  perception_latency_s?: number | null;
  safety_rule?: string;
  safety_action?: string;
};

export type MetricsResponse = {
  run_id?: string | null;
  session_id?: string | null;
  metrics: MetricRecord[];
  source: string;
};

export type EventsResponse = {
  run_id?: string | null;
  session_id?: string | null;
  events: StoredEnvelope[];
  source: string;
};

export type ReplayPayload = {
  run_id: string;
  session_id?: string | null;
  snapshot: SnapshotResponse;
  events: StoredEnvelope[];
  metrics: MetricRecord[];
};

export type VehicleStatePayload = {
  connected?: boolean;
  armed?: boolean;
  landed?: boolean;
  failsafe?: boolean;
  preflight_checks_pass?: boolean;
  position_valid?: boolean;
  nav_state?: string;
  altitude_m?: number;
  relative_altitude_m?: number;
  absolute_altitude_m?: number;
  latitude_deg?: number;
  longitude_deg?: number;
};

export type MissionStatusPayload = {
  mission_id?: string;
  phase?: string;
  active?: boolean;
  completed?: boolean;
  aborted?: boolean;
  failed?: boolean;
  terminal?: boolean;
  succeeded?: boolean;
  detail?: string;
  current_waypoint_index?: number;
  total_waypoints?: number;
  last_command?: string;
};

export type SafetyStatusPayload = {
  active?: boolean;
  mission_abort_requested?: boolean;
  vehicle_command_sent?: boolean;
  rule?: string;
  action?: string;
  source?: string;
  detail?: string;
  trigger_count?: number;
};

export type TrackedObjectPayload = {
  tracked?: boolean;
  track_id?: number;
  label?: string;
  confidence?: number;
  center_x?: number;
  center_y?: number;
  width?: number;
  height?: number;
  age?: number;
  state?: string;
};

export type PerceptionHeartbeatPayload = {
  healthy?: boolean;
  pipeline_latency_s?: number;
  frame_age_s?: number;
};
