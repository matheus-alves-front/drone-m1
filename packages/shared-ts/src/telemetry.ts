export interface SessionSummary {
  run_id: string;
  source: string;
  started_at_ns: number;
  updated_at_ns: number;
  event_count: number;
  metrics_count: number;
  last_kind: string;
}

export interface VehicleStateSnapshot {
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
}

export interface MissionStatusSnapshot {
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
}

export interface SafetyStatusSnapshot {
  active?: boolean;
  mission_abort_requested?: boolean;
  vehicle_command_sent?: boolean;
  rule?: string;
  action?: string;
  source?: string;
  detail?: string;
  trigger_count?: number;
}

export interface TrackedObjectSnapshot {
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
}

export interface PerceptionHeartbeatSnapshot {
  healthy?: boolean;
  pipeline_latency_s?: number;
}

export interface PerceptionEventSnapshot {
  event_type?: string;
  track_id?: number;
  label?: string;
  confidence?: number;
  detail?: string;
}

export interface TelemetrySnapshot {
  run_id: string;
  updated_at_ns: number;
  vehicle_state: VehicleStateSnapshot;
  vehicle_command_status: Record<string, unknown>;
  mission_status: MissionStatusSnapshot;
  safety_status: SafetyStatusSnapshot;
  tracked_object: TrackedObjectSnapshot;
  perception_heartbeat: PerceptionHeartbeatSnapshot;
  perception_event: PerceptionEventSnapshot;
}

export interface EventRecord {
  seq: number;
  run_id: string;
  source: string;
  kind: string;
  topic: string;
  stamp_ns: number;
  payload: Record<string, unknown>;
}

export interface MetricRecord {
  seq: number;
  run_id: string;
  stamp_ns: number;
  mission_phase: string;
  mission_active: boolean;
  altitude_m: number | null;
  relative_altitude_m: number | null;
  failsafe: boolean | null;
  tracked: boolean | null;
  perception_latency_s: number | null;
  safety_rule: string;
  safety_action: string;
}

export interface ReplayPayload {
  session: SessionSummary;
  snapshot: TelemetrySnapshot;
  events: EventRecord[];
  metrics: MetricRecord[];
}

export interface TelemetryUpdateMessage {
  type: "telemetry_update";
  session: SessionSummary | null;
  snapshot?: TelemetrySnapshot;
  recent_events?: EventRecord[];
  latest_metric?: MetricRecord | null;
}
