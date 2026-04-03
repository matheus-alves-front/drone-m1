from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .models import TelemetryEnvelopeIn
from .store import TelemetryStore


class WebsocketHub:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._clients.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._clients.discard(websocket)

    async def broadcast(self, payload: dict) -> None:
        stale: list[WebSocket] = []
        for client in self._clients:
            try:
                await client.send_json(payload)
            except Exception:
                stale.append(client)
        for client in stale:
            self.disconnect(client)


def create_app(data_root: Path | None = None, *, storage_root: Path | None = None) -> FastAPI:
    root = Path(storage_root or data_root or Path(__file__).resolve().parents[1] / "data")
    root.mkdir(parents=True, exist_ok=True)
    store = TelemetryStore(root)
    hub = WebsocketHub()
    legacy_hub = WebsocketHub()

    app = FastAPI(title="drone-sim telemetry api", version="0.1.0")
    app.state.store = store
    app.state.hub = hub
    app.state.legacy_hub = legacy_hub

    def session_snapshot(run_id: str) -> dict:
        snapshot = store.snapshot().model_dump()["latest_by_kind"]
        return {
            kind: envelope["payload"]
            for kind, envelope in snapshot.items()
            if envelope["run_id"] == run_id
        }

    def session_metrics(run_id: str) -> list[dict]:
        counts: dict[str, int] = {}
        for event in store.replay(run_id, limit=5000):
            counts[event.kind] = counts.get(event.kind, 0) + 1
        return [{"kind": kind, "count": count} for kind, count in sorted(counts.items())]

    @app.get("/api/v1/health")
    async def health() -> dict:
        return {"status": "ok"}

    @app.post("/api/v1/ingest", status_code=202)
    async def ingest(envelope: TelemetryEnvelopeIn) -> dict:
        stored = store.ingest(envelope)
        await hub.broadcast({"type": "telemetry_event", "event": stored.model_dump()})
        await legacy_hub.broadcast(
            {
                "type": "telemetry_update",
                "session": {"run_id": stored.run_id},
                "snapshot": session_snapshot(stored.run_id),
            }
        )
        return {"status": "accepted", "sequence": stored.sequence}

    @app.get("/api/v1/snapshot")
    async def snapshot() -> dict:
        return store.snapshot().model_dump()

    @app.get("/api/v1/metrics")
    async def metrics() -> dict:
        return store.metrics().model_dump()

    @app.get("/api/v1/events")
    async def events(limit: int = 100, run_id: str | None = None) -> list[dict]:
        return [event.model_dump() for event in store.recent_events(limit=max(1, min(limit, 1000)), run_id=run_id)]

    @app.get("/api/v1/runs")
    async def runs() -> list[dict]:
        return [item.model_dump() for item in store.list_runs()]

    @app.get("/api/v1/replay/{run_id}")
    async def replay(run_id: str, limit: int = 500) -> list[dict]:
        return [event.model_dump() for event in store.replay(run_id, limit=max(1, min(limit, 5000)))]

    @app.get("/api/v1/sessions/current")
    async def current_session() -> dict:
        return {"run_id": store.snapshot().current_run_id}

    @app.get("/api/v1/sessions/{run_id}/snapshot")
    async def session_snapshot_endpoint(run_id: str) -> dict:
        return session_snapshot(run_id)

    @app.get("/api/v1/sessions/{run_id}/replay")
    async def session_replay(run_id: str) -> dict:
        return {
            "events": [event.model_dump() for event in store.replay(run_id, limit=5000)],
            "metrics": session_metrics(run_id),
        }

    @app.websocket("/ws/telemetry")
    async def telemetry_socket(websocket: WebSocket) -> None:
        await hub.connect(websocket)
        await websocket.send_json({"type": "snapshot", "snapshot": store.snapshot().model_dump()})
        try:
            while True:
                await asyncio.sleep(30.0)
        except WebSocketDisconnect:
            hub.disconnect(websocket)
        except Exception:
            hub.disconnect(websocket)

    @app.websocket("/ws/telemetry/current")
    async def telemetry_current_socket(websocket: WebSocket) -> None:
        await legacy_hub.connect(websocket)
        try:
            while True:
                await asyncio.sleep(30.0)
        except WebSocketDisconnect:
            legacy_hub.disconnect(websocket)
        except Exception:
            legacy_hub.disconnect(websocket)

    return app
