export type StoredEnvelope = {
  run_id: string;
  source: string;
  kind: string;
  topic: string;
  stamp_ns: number;
  payload: Record<string, unknown>;
  sequence: number;
  received_ns: number;
};

export type SnapshotResponse = {
  current_run_id: string | null;
  latest_by_kind: Record<string, StoredEnvelope>;
};

export type MetricsResponse = {
  total_events: number;
  counts_by_kind: Record<string, number>;
  counts_by_run: Record<string, number>;
};

export type RunSummary = {
  run_id: string;
  event_count: number;
  last_kind: string | null;
  last_stamp_ns: number | null;
};

export type TelemetrySnapshotMessage = {
  type: "snapshot";
  snapshot: SnapshotResponse;
};

export type TelemetryEventMessage = {
  type: "telemetry_event";
  event: StoredEnvelope;
};

export type TelemetryMessage = TelemetrySnapshotMessage | TelemetryEventMessage;

export type VehicleStatePayload = {
  connected?: boolean;
  armed?: boolean;
  relative_altitude_m?: number;
  failsafe?: boolean;
  nav_state?: string;
};

export type MissionStatusPayload = {
  phase?: string;
  detail?: string;
  current_waypoint_index?: number;
  total_waypoints?: number;
  terminal?: boolean;
};

export type SafetyStatusPayload = {
  active?: boolean;
  rule?: string;
  action?: string;
  trigger_count?: number;
  mission_abort_requested?: boolean;
  vehicle_command_sent?: boolean;
};

export type TrackedObjectPayload = {
  tracked?: boolean;
  label?: string;
  confidence?: number;
};

export type PerceptionHeartbeatPayload = {
  healthy?: boolean;
  pipeline_latency_s?: number;
  frame_age_s?: number;
};
