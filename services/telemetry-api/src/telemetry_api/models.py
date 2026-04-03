from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TelemetryEnvelopeModel(BaseModel):
    run_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    stamp_ns: int = Field(ge=0)
    payload: dict[str, Any]


class SessionSummaryModel(BaseModel):
    run_id: str
    source: str
    started_at_ns: int
    updated_at_ns: int
    event_count: int
    metrics_count: int
    last_kind: str


class SnapshotModel(BaseModel):
    run_id: str
    updated_at_ns: int
    vehicle_state: dict[str, Any] = Field(default_factory=dict)
    vehicle_command_status: dict[str, Any] = Field(default_factory=dict)
    mission_status: dict[str, Any] = Field(default_factory=dict)
    safety_status: dict[str, Any] = Field(default_factory=dict)
    tracked_object: dict[str, Any] = Field(default_factory=dict)
    perception_heartbeat: dict[str, Any] = Field(default_factory=dict)
    perception_event: dict[str, Any] = Field(default_factory=dict)


class EventRecordModel(BaseModel):
    seq: int
    run_id: str
    source: str
    kind: str
    topic: str
    stamp_ns: int
    payload: dict[str, Any]


class MetricRecordModel(BaseModel):
    seq: int
    run_id: str
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


class ReplayModel(BaseModel):
    session: SessionSummaryModel
    snapshot: SnapshotModel
    events: list[EventRecordModel]
    metrics: list[MetricRecordModel]
