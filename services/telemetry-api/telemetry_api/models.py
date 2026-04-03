from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TelemetryEnvelopeIn(BaseModel):
    run_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    stamp_ns: int = Field(ge=0)
    payload: dict[str, Any]


class TelemetryEnvelopeStored(TelemetryEnvelopeIn):
    sequence: int = Field(ge=1)
    received_ns: int = Field(ge=0)


class RunSummary(BaseModel):
    run_id: str
    event_count: int
    last_kind: str | None = None
    last_stamp_ns: int | None = None


class MetricsSnapshot(BaseModel):
    total_events: int
    counts_by_kind: dict[str, int]
    counts_by_run: dict[str, int]


class SnapshotResponse(BaseModel):
    current_run_id: str | None
    latest_by_kind: dict[str, dict[str, Any]]
