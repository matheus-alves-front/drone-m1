from __future__ import annotations

import json
from pathlib import Path
import threading
import time
from typing import Any

from .models import MetricRecord, MetricsSnapshot, SessionSummary, TelemetryEnvelopeIn, TelemetryEnvelopeStored, TelemetryReplayResponse, TelemetrySnapshot


class SessionNotFoundError(FileNotFoundError):
    """Raised when a requested telemetry session does not exist."""


def _load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.is_file():
        return dict(default)
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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
    def __init__(self, data_root: Path) -> None:
        self._data_root = data_root
        self._runs_root = data_root / "runs"
        self._meta_path = data_root / "meta.json"
        self._current_session_path = data_root / "current_session.json"
        self._global_snapshot_path = data_root / "snapshot.json"
        self._global_metrics_path = data_root / "metrics.json"
        self._runs_root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

        meta = _load_json(
            self._meta_path,
            {
                "sequence": 0,
                "current_run_id": None,
                "latest_by_kind": {},
                "counts_by_kind": {},
                "counts_by_run": {},
            },
        )
        self._sequence = int(meta.get("sequence", 0))
        self._current_run_id = meta.get("current_run_id")
        self._latest_by_kind: dict[str, dict[str, Any]] = dict(meta.get("latest_by_kind", {}))
        self._counts_by_kind: dict[str, int] = {
            str(kind): int(count)
            for kind, count in dict(meta.get("counts_by_kind", {})).items()
        }
        self._counts_by_run: dict[str, int] = {
            str(run_id): int(count)
            for run_id, count in dict(meta.get("counts_by_run", {})).items()
        }
        self._repair_from_disk()

    def ingest(self, envelope: TelemetryEnvelopeIn) -> TelemetryEnvelopeStored:
        with self._lock:
            self._sequence += 1
            stored = TelemetryEnvelopeStored(
                **envelope.model_dump(),
                sequence=self._sequence,
                received_ns=time.time_ns(),
            )

            session = self._load_session_payload(
                stored.run_id,
                default={
                    "run_id": stored.run_id,
                    "session_id": stored.session_id,
                    "source": stored.source,
                    "started_at_ns": stored.stamp_ns,
                    "updated_at_ns": stored.stamp_ns,
                    "event_count": 0,
                    "metrics_count": 0,
                    "last_kind": stored.kind,
                    "last_stamp_ns": stored.stamp_ns,
                },
            )
            session["session_id"] = stored.session_id or session.get("session_id")
            session["source"] = stored.source
            session["updated_at_ns"] = stored.stamp_ns
            session["event_count"] = int(session.get("event_count", 0)) + 1
            session["last_kind"] = stored.kind
            session["last_stamp_ns"] = stored.stamp_ns

            snapshot_payload = self._load_snapshot_payload(
                stored.run_id,
                default={
                    "run_id": stored.run_id,
                    "session_id": stored.session_id,
                    "updated_at_ns": stored.stamp_ns,
                    "vehicle_state": {},
                    "vehicle_command_status": {},
                    "mission_status": {},
                    "safety_status": {},
                    "tracked_object": {},
                    "perception_heartbeat": {},
                    "perception_event": {},
                },
            )
            snapshot_payload["run_id"] = stored.run_id
            snapshot_payload["session_id"] = stored.session_id or snapshot_payload.get("session_id")
            snapshot_payload["updated_at_ns"] = stored.stamp_ns
            snapshot_payload[stored.kind] = stored.payload

            _append_jsonl(self._events_path(stored.run_id), stored.model_dump())

            metric = self._build_metric_record(
                run_id=stored.run_id,
                session_id=stored.session_id,
                seq=int(session.get("metrics_count", 0)) + 1,
                stamp_ns=stored.stamp_ns,
                snapshot_payload=snapshot_payload,
            )
            session["metrics_count"] = metric.seq
            _append_jsonl(self._metrics_path(stored.run_id), metric.model_dump())

            self._current_run_id = stored.run_id
            self._latest_by_kind[stored.kind] = stored.model_dump()
            self._counts_by_kind[stored.kind] = self._counts_by_kind.get(stored.kind, 0) + 1
            self._counts_by_run[stored.run_id] = self._counts_by_run.get(stored.run_id, 0) + 1

            self._save_session_payload(stored.run_id, session)
            self._save_snapshot_payload(stored.run_id, snapshot_payload)
            _write_json(self._current_session_path, {"run_id": stored.run_id})
            self._persist_global_state()
            return stored

    def list_runs(self) -> list[SessionSummary]:
        with self._lock:
            runs: list[SessionSummary] = []
            for session_path in self._runs_root.glob("*/session.json"):
                payload = _load_json(session_path, {})
                if payload:
                    runs.append(SessionSummary.model_validate(payload))
            return sorted(runs, key=lambda item: item.updated_at_ns, reverse=True)

    def current_session(self) -> SessionSummary:
        with self._lock:
            run_id = self._current_run_id or _load_json(self._current_session_path, {}).get("run_id")
            if not run_id:
                runs = self.list_runs()
                if not runs:
                    raise SessionNotFoundError("no telemetry sessions available")
                return runs[0]
            return self.get_session(str(run_id))

    def get_session(self, run_id: str) -> SessionSummary:
        payload = self._load_session_payload(run_id)
        if not payload:
            raise SessionNotFoundError(f"telemetry session not found: {run_id}")
        return SessionSummary.model_validate(payload)

    def snapshot(self) -> TelemetrySnapshot:
        with self._lock:
            if not self._current_run_id:
                return TelemetrySnapshot(current_run_id=None, latest_by_kind=dict(self._latest_by_kind))
            return self.session_snapshot(self._current_run_id, include_global_latest=True)

    def session_snapshot(self, run_id: str, *, include_global_latest: bool = False) -> TelemetrySnapshot:
        payload = self._load_snapshot_payload(run_id)
        if not payload:
            raise SessionNotFoundError(f"telemetry snapshot not found: {run_id}")
        payload["current_run_id"] = self._current_run_id
        payload["latest_by_kind"] = (
            dict(self._latest_by_kind)
            if include_global_latest
            else self._latest_by_kind_for_run(run_id)
        )
        return TelemetrySnapshot.model_validate(payload)

    def metrics(self) -> MetricsSnapshot:
        with self._lock:
            return MetricsSnapshot(
                total_events=sum(self._counts_by_kind.values()),
                counts_by_kind=dict(self._counts_by_kind),
                counts_by_run=dict(self._counts_by_run),
            )

    def session_metrics(self, run_id: str, *, limit: int = 200) -> list[MetricRecord]:
        self.get_session(run_id)
        metrics = [MetricRecord.model_validate(item) for item in _read_jsonl(self._metrics_path(run_id))]
        if limit <= 0:
            return metrics
        return metrics[-limit:]

    def recent_events(
        self,
        *,
        limit: int = 100,
        run_id: str | None = None,
        kind: str | None = None,
    ) -> list[TelemetryEnvelopeStored]:
        effective_run_id = run_id or self._current_run_id
        if not effective_run_id:
            return []
        self.get_session(effective_run_id)
        records = [
            TelemetryEnvelopeStored.model_validate(item)
            for item in _read_jsonl(self._events_path(effective_run_id))
        ]
        if kind is not None:
            records = [item for item in records if item.kind == kind]
        if limit <= 0:
            return records
        return records[-limit:]

    def replay(self, run_id: str, *, limit: int = 500) -> list[TelemetryEnvelopeStored]:
        return self.recent_events(limit=limit, run_id=run_id)

    def session_replay(self, run_id: str, *, limit: int = 5000) -> TelemetryReplayResponse:
        session = self.get_session(run_id)
        return TelemetryReplayResponse(
            run_id=run_id,
            session_id=session.session_id,
            snapshot=self.session_snapshot(run_id),
            events=self.recent_events(limit=limit, run_id=run_id),
            metrics=self.session_metrics(run_id, limit=limit),
        )

    def _repair_from_disk(self) -> None:
        runs = self.list_runs()
        if runs:
            if not self._current_run_id:
                self._current_run_id = runs[0].run_id
            for session in runs:
                if session.run_id not in self._counts_by_run:
                    self._counts_by_run[session.run_id] = session.event_count
            if not self._latest_by_kind and self._current_run_id:
                try:
                    current_snapshot = self.session_snapshot(self._current_run_id)
                    self._latest_by_kind = dict(current_snapshot.latest_by_kind)
                except SessionNotFoundError:
                    self._latest_by_kind = {}
            self._persist_global_state()

    def _persist_global_state(self) -> None:
        snapshot = self.snapshot().model_dump()
        metrics = self.metrics().model_dump()
        _write_json(self._global_snapshot_path, snapshot)
        _write_json(self._global_metrics_path, metrics)
        _write_json(
            self._meta_path,
            {
                "sequence": self._sequence,
                "current_run_id": self._current_run_id,
                "latest_by_kind": self._latest_by_kind,
                "counts_by_kind": self._counts_by_kind,
                "counts_by_run": self._counts_by_run,
            },
        )

    def _run_dir(self, run_id: str) -> Path:
        return self._runs_root / run_id

    def _session_path(self, run_id: str) -> Path:
        return self._run_dir(run_id) / "session.json"

    def _snapshot_path(self, run_id: str) -> Path:
        return self._run_dir(run_id) / "snapshot.json"

    def _events_path(self, run_id: str) -> Path:
        return self._run_dir(run_id) / "events.jsonl"

    def _metrics_path(self, run_id: str) -> Path:
        return self._run_dir(run_id) / "metrics.jsonl"

    def _load_session_payload(self, run_id: str, default: dict[str, Any] | None = None) -> dict[str, Any]:
        return _load_json(self._session_path(run_id), default or {})

    def _load_snapshot_payload(self, run_id: str, default: dict[str, Any] | None = None) -> dict[str, Any]:
        return _load_json(self._snapshot_path(run_id), default or {})

    def _save_session_payload(self, run_id: str, payload: dict[str, Any]) -> None:
        _write_json(self._session_path(run_id), payload)

    def _save_snapshot_payload(self, run_id: str, payload: dict[str, Any]) -> None:
        _write_json(self._snapshot_path(run_id), payload)

    def _latest_by_kind_for_run(self, run_id: str) -> dict[str, dict[str, Any]]:
        latest: dict[str, dict[str, Any]] = {}
        for envelope in self.recent_events(limit=5000, run_id=run_id):
            latest[envelope.kind] = envelope.model_dump()
        return latest

    @staticmethod
    def _build_metric_record(
        *,
        run_id: str,
        session_id: str | None,
        seq: int,
        stamp_ns: int,
        snapshot_payload: dict[str, Any],
    ) -> MetricRecord:
        vehicle_state = snapshot_payload.get("vehicle_state", {})
        mission_status = snapshot_payload.get("mission_status", {})
        safety_status = snapshot_payload.get("safety_status", {})
        tracked_object = snapshot_payload.get("tracked_object", {})
        perception_heartbeat = snapshot_payload.get("perception_heartbeat", {})
        return MetricRecord(
            seq=seq,
            run_id=run_id,
            session_id=session_id,
            stamp_ns=stamp_ns,
            mission_phase=str(mission_status.get("phase", "")),
            mission_active=bool(mission_status.get("active", False)),
            altitude_m=_optional_float(vehicle_state.get("altitude_m")),
            relative_altitude_m=_optional_float(vehicle_state.get("relative_altitude_m")),
            failsafe=_optional_bool(vehicle_state.get("failsafe")),
            tracked=_optional_bool(tracked_object.get("tracked")),
            perception_latency_s=_optional_float(perception_heartbeat.get("pipeline_latency_s")),
            safety_rule=str(safety_status.get("rule", "")),
            safety_action=str(safety_status.get("action", "")),
        )


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)
