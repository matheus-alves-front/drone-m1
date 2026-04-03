from __future__ import annotations

import json
from pathlib import Path
import threading
import time

from .models import MetricsSnapshot, RunSummary, SnapshotResponse, TelemetryEnvelopeIn, TelemetryEnvelopeStored


class TelemetryStore:
    def __init__(self, data_root: Path) -> None:
        self._data_root = data_root
        self._runs_root = data_root / "runs"
        self._runs_root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._sequence = 0
        self._current_run_id: str | None = None
        self._latest_by_kind: dict[str, dict] = {}
        self._counts_by_kind: dict[str, int] = {}
        self._counts_by_run: dict[str, int] = {}
        self._last_by_run: dict[str, TelemetryEnvelopeStored] = {}

    def ingest(self, envelope: TelemetryEnvelopeIn) -> TelemetryEnvelopeStored:
        with self._lock:
            self._sequence += 1
            stored = TelemetryEnvelopeStored(
                **envelope.model_dump(),
                sequence=self._sequence,
                received_ns=time.time_ns(),
            )
            self._current_run_id = stored.run_id
            self._latest_by_kind[stored.kind] = stored.model_dump()
            self._counts_by_kind[stored.kind] = self._counts_by_kind.get(stored.kind, 0) + 1
            self._counts_by_run[stored.run_id] = self._counts_by_run.get(stored.run_id, 0) + 1
            self._last_by_run[stored.run_id] = stored
            self._append_event(stored)
            self._persist_run_snapshot(stored.run_id)
            self._persist_global_snapshot()
            self._persist_metrics(stored.run_id)
            return stored

    def list_runs(self) -> list[RunSummary]:
        with self._lock:
            summaries: list[RunSummary] = []
            for run_id in sorted(self._counts_by_run):
                last = self._last_by_run.get(run_id)
                summaries.append(
                    RunSummary(
                        run_id=run_id,
                        event_count=self._counts_by_run[run_id],
                        last_kind=last.kind if last else None,
                        last_stamp_ns=last.stamp_ns if last else None,
                    )
                )
            return summaries

    def recent_events(self, *, limit: int = 100, run_id: str | None = None) -> list[TelemetryEnvelopeStored]:
        path = self._events_file(run_id or self._current_run_id)
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        result = []
        for line in lines[-limit:]:
            if not line.strip():
                continue
            result.append(TelemetryEnvelopeStored.model_validate_json(line))
        return result

    def replay(self, run_id: str, *, limit: int = 500) -> list[TelemetryEnvelopeStored]:
        return self.recent_events(limit=limit, run_id=run_id)

    def snapshot(self) -> SnapshotResponse:
        with self._lock:
            return SnapshotResponse(
                current_run_id=self._current_run_id,
                latest_by_kind=self._latest_by_kind,
            )

    def metrics(self) -> MetricsSnapshot:
        with self._lock:
            return MetricsSnapshot(
                total_events=sum(self._counts_by_kind.values()),
                counts_by_kind=dict(self._counts_by_kind),
                counts_by_run=dict(self._counts_by_run),
            )

    def _events_file(self, run_id: str | None) -> Path:
        if not run_id:
            return self._runs_root / "unknown" / "events.jsonl"
        run_dir = self._runs_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir / "events.jsonl"

    def _append_event(self, stored: TelemetryEnvelopeStored) -> None:
        events_file = self._events_file(stored.run_id)
        with events_file.open("a", encoding="utf-8") as handle:
            handle.write(stored.model_dump_json())
            handle.write("\n")

    def _persist_run_snapshot(self, run_id: str) -> None:
        snapshot = {
            "run_id": run_id,
            "latest_by_kind": {
                kind: envelope
                for kind, envelope in self._latest_by_kind.items()
                if envelope["run_id"] == run_id
            },
        }
        run_dir = self._runs_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "snapshot.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    def _persist_global_snapshot(self) -> None:
        payload = self.snapshot().model_dump()
        (self._data_root / "snapshot.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _persist_metrics(self, run_id: str) -> None:
        global_metrics = self.metrics().model_dump()
        (self._data_root / "metrics.json").write_text(json.dumps(global_metrics, indent=2), encoding="utf-8")
        run_metrics = {
            "run_id": run_id,
            "event_count": self._counts_by_run.get(run_id, 0),
        }
        run_dir = self._runs_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "metrics.json").write_text(json.dumps(run_metrics, indent=2), encoding="utf-8")
