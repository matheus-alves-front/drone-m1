from __future__ import annotations

import json
from queue import Empty, Full, Queue
import threading
from urllib import error, request

from .contracts import TelemetryEnvelope


class TelemetryApiClient:
    def __init__(self, base_url: str, timeout_s: float = 1.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_s = max(float(timeout_s), 0.1)

    def emit(self, envelope: TelemetryEnvelope) -> None:
        payload = json.dumps(envelope.to_dict()).encode("utf-8")
        req = request.Request(
            f"{self._base_url}/api/v1/ingest",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self._timeout_s) as response:
                if response.status >= 300:
                    raise RuntimeError(f"telemetry api returned status={response.status}")
        except error.URLError as exc:  # pragma: no cover
            raise RuntimeError(f"failed to reach telemetry api: {exc}") from exc


class AsyncTelemetryPublisher:
    def __init__(self, client: TelemetryApiClient, *, max_queue_size: int = 256) -> None:
        self._client = client
        self._queue: Queue[TelemetryEnvelope | None] = Queue(maxsize=max_queue_size)
        self._thread = threading.Thread(target=self._run, name="telemetry-api-publisher", daemon=True)
        self._stop_event = threading.Event()
        self._last_error: str = ""
        self._thread.start()

    @property
    def last_error(self) -> str:
        return self._last_error

    def submit(self, envelope: TelemetryEnvelope) -> None:
        try:
            self._queue.put_nowait(envelope)
        except Full as exc:
            self._last_error = f"telemetry queue full: {exc}"

    def close(self) -> None:
        self._stop_event.set()
        try:
            self._queue.put_nowait(None)
        except Full:
            pass
        self._thread.join(timeout=2.0)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                envelope = self._queue.get(timeout=0.2)
            except Empty:
                continue
            if envelope is None:
                break
            try:
                self._client.emit(envelope)
            except Exception as exc:  # pragma: no cover
                self._last_error = str(exc)
