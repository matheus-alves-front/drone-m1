from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any

from .models import (
    EventRecordModel,
    MetricRecordModel,
    ReplayModel,
    SessionSummaryModel,
    SnapshotModel,
    TelemetryEnvelopeModel,
)


class SessionNotFoundError(FileNotFoundError):
    """Raised when a requested telemetry session does not exist."""


def _load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.is_file():
        return dict(default)
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True))
        handle.write("\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


class TelemetryStore:
    def __init__(self, storage_root: Path) -> None:
        self._storage_root = storage_root
        self._storage_root.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    @property
    def storage_root(self) -> Path:
        return self._storage_root

    def ingest(self, envelope: TelemetryEnvelopeModel) -> SessionSummaryModel:
        with self._lock:
            session_dir = self._session_dir(envelope.run_id)
            session_dir.mkdir(parents=True, exist_ok=True)

            session_path = session_dir / "session.json"
            snapshot_path = session_dir / "snapshot.json"
            events_path = session_dir / "events.jsonl"
            metrics_path = session_dir / "metrics.jsonl"

            session_payload = _load_json(
                session_path,
                {
                    "run_id": envelope.run_id,
                    "source": envelope.source,
                    "started_at_ns": envelope.stamp_ns,
                    "updated_at_ns": envelope.stamp_ns,
                    "event_count": 0,
                    "metrics_count": 0,
                    "last_kind": envelope.kind,
                },
            )
            snapshot_payload = _load_json(
                snapshot_path,
                {
                    "run_id": envelope.run_id,
                    "updated_at_ns": envelope.stamp_ns,
                    "vehicle_state": {},
                    "vehicle_command_status": {},
                    "mission_status": {},
                    "safety_status": {},
                    "tracked_object": {},
                    "perception_heartbeat": {},
                    "perception_event": {},
                },
            )

            session_payload["updated_at_ns"] = envelope.stamp_ns
            session_payload["last_kind"] = envelope.kind
            session_payload["event_count"] = int(session_payload.get("event_count", 0)) + 1
            snapshot_payload["updated_at_ns"] = envelope.stamp_ns
            snapshot_payload[envelope.kind] = envelope.payload

            event_record = {
                "seq": int(session_payload["event_count"]),
                "run_id": envelope.run_id,
                "source": envelope.source,
                "kind": envelope.kind,
                "topic": envelope.topic,
                "stamp_ns": envelope.stamp_ns,
                "payload": envelope.payload,
            }
            _append_jsonl(events_path, event_record)

            metric_record = self._build_metric_record(
                run_id=envelope.run_id,
                seq=int(session_payload["metrics_count"]) + 1,
                stamp_ns=envelope.stamp_ns,
                snapshot_payload=snapshot_payload,
            )
            session_payload["metrics_count"] = metric_record["seq"]
            _append_jsonl(metrics_path, metric_record)

            _write_json(snapshot_path, snapshot_payload)
            _write_json(session_path, session_payload)
            _write_json(self._storage_root / "current_session.json", {"run_id": envelope.run_id})

            return SessionSummaryModel.model_validate(session_payload)

    def list_sessions(self) -> list[SessionSummaryModel]:
        sessions: list[SessionSummaryModel] = []
        for session_path in sorted(self._storage_root.glob("*/session.json"), reverse=True):
            sessions.append(SessionSummaryModel.model_validate(_load_json(session_path, {})))
        return sorted(sessions, key=lambda item: item.updated_at_ns, reverse=True)

    def current_session(self) -> SessionSummaryModel:
        pointer_path = self._storage_root / "current_session.json"
        pointer = _load_json(pointer_path, {})
        run_id = str(pointer.get("run_id", "")).strip()
        if not run_id:
            sessions = self.list_sessions()
            if not sessions:
                raise SessionNotFoundError("no telemetry sessions available")
            return sessions[0]
        return self.get_session(run_id)

    def get_session(self, run_id: str) -> SessionSummaryModel:
        session_path = self._session_dir(run_id) / "session.json"
        if not session_path.is_file():
            raise SessionNotFoundError(f"telemetry session not found: {run_id}")
        return SessionSummaryModel.model_validate(_load_json(session_path, {}))

    def get_snapshot(self, run_id: str) -> SnapshotModel:
        snapshot_path = self._session_dir(run_id) / "snapshot.json"
        if not snapshot_path.is_file():
            raise SessionNotFoundError(f"telemetry snapshot not found: {run_id}")
        return SnapshotModel.model_validate(_load_json(snapshot_path, {}))

    def get_events(self, run_id: str, *, limit: int | None = None) -> list[EventRecordModel]:
        events = [
            EventRecordModel.model_validate(record)
            for record in _read_jsonl(self._session_dir(run_id) / "events.jsonl")
        ]
        if limit is None or limit <= 0:
            return events
        return events[-limit:]

    def get_metrics(self, run_id: str, *, limit: int | None = None) -> list[MetricRecordModel]:
        metrics = [
            MetricRecordModel.model_validate(record)
            for record in _read_jsonl(self._session_dir(run_id) / "metrics.jsonl")
        ]
        if limit is None or limit <= 0:
            return metrics
        return metrics[-limit:]

    def get_replay(self, run_id: str) -> ReplayModel:
        return ReplayModel(
            session=self.get_session(run_id),
            snapshot=self.get_snapshot(run_id),
            events=self.get_events(run_id),
            metrics=self.get_metrics(run_id),
        )

    def _session_dir(self, run_id: str) -> Path:
        return self._storage_root / run_id

    @staticmethod
    def _build_metric_record(
        *,
        run_id: str,
        seq: int,
        stamp_ns: int,
        snapshot_payload: dict[str, Any],
    ) -> dict[str, Any]:
        vehicle_state = snapshot_payload.get("vehicle_state", {})
        mission_status = snapshot_payload.get("mission_status", {})
        safety_status = snapshot_payload.get("safety_status", {})
        tracked_object = snapshot_payload.get("tracked_object", {})
        perception_heartbeat = snapshot_payload.get("perception_heartbeat", {})
        return {
            "seq": seq,
            "run_id": run_id,
            "stamp_ns": stamp_ns,
            "mission_phase": str(mission_status.get("phase", "")),
            "mission_active": bool(mission_status.get("active", False)),
            "altitude_m": _optional_float(vehicle_state.get("altitude_m")),
            "relative_altitude_m": _optional_float(vehicle_state.get("relative_altitude_m")),
            "failsafe": _optional_bool(vehicle_state.get("failsafe")),
            "tracked": _optional_bool(tracked_object.get("tracked")),
            "perception_latency_s": _optional_float(perception_heartbeat.get("pipeline_latency_s")),
            "safety_rule": str(safety_status.get("rule", "")),
            "safety_action": str(safety_status.get("action", "")),
        }


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)
