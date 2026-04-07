from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TelemetryEnvelopeIn(BaseModel):
    run_id: str = Field(min_length=1)
    session_id: str | None = None
    source: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    stamp_ns: int = Field(ge=0)
    payload: dict[str, Any]


class TelemetryEnvelopeStored(TelemetryEnvelopeIn):
    sequence: int = Field(ge=1)
    received_ns: int = Field(ge=0)


class SessionSummary(BaseModel):
    run_id: str
    session_id: str | None = None
    source: str
    started_at_ns: int
    updated_at_ns: int
    event_count: int
    metrics_count: int
    last_kind: str


class TelemetrySnapshot(BaseModel):
    current_run_id: str | None = None
    run_id: str | None = None
    session_id: str | None = None
    updated_at_ns: int | None = None
    vehicle_state: dict[str, Any] = Field(default_factory=dict)
    vehicle_command_status: dict[str, Any] = Field(default_factory=dict)
    mission_status: dict[str, Any] = Field(default_factory=dict)
    safety_status: dict[str, Any] = Field(default_factory=dict)
    tracked_object: dict[str, Any] = Field(default_factory=dict)
    perception_heartbeat: dict[str, Any] = Field(default_factory=dict)
    perception_event: dict[str, Any] = Field(default_factory=dict)
    latest_by_kind: dict[str, Any] = Field(default_factory=dict)


class EventRecord(BaseModel):
    seq: int
    run_id: str
    session_id: str | None = None
    source: str
    kind: str
    topic: str
    stamp_ns: int
    payload: dict[str, Any]


class MetricRecord(BaseModel):
    seq: int
    run_id: str
    session_id: str | None = None
    stamp_ns: int
    mission_phase: str
    mission_active: bool
    altitude_m: float | None
    relative_altitude_m: float | None
    failsafe: bool | None
    tracked: bool | None
    perception_latency_s: float | None
    safety_rule: str
    safety_action: str


class MetricsSnapshot(BaseModel):
    total_events: int = 0
    counts_by_kind: dict[str, int] = Field(default_factory=dict)
    counts_by_run: dict[str, int] = Field(default_factory=dict)


class TelemetryMetricsResponse(BaseModel):
    run_id: str | None = None
    session_id: str | None = None
    metrics: list[MetricRecord] = Field(default_factory=list)
    source: str = "telemetry_api"


class TelemetryEventsResponse(BaseModel):
    run_id: str | None = None
    session_id: str | None = None
    events: list[TelemetryEnvelopeStored] = Field(default_factory=list)
    source: str = "telemetry_api"


class TelemetryReplayResponse(BaseModel):
    run_id: str
    session_id: str | None = None
    snapshot: TelemetrySnapshot = Field(default_factory=TelemetrySnapshot)
    events: list[TelemetryEnvelopeStored] = Field(default_factory=list)
    metrics: list[MetricRecord] = Field(default_factory=list)
