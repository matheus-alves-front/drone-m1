from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect

from .models import TelemetryEnvelopeIn
from .store import SessionNotFoundError, TelemetryStore


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
                "session": store.get_session(stored.run_id).model_dump(),
                "snapshot": store.session_snapshot(stored.run_id).model_dump(),
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
    async def events(
        limit: int = Query(default=100, ge=1, le=1000),
        run_id: str | None = None,
        kind: str | None = None,
    ) -> list[dict]:
        try:
            return [
                event.model_dump()
                for event in store.recent_events(limit=limit, run_id=run_id, kind=kind)
            ]
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/runs")
    async def runs() -> list[dict]:
        return [item.model_dump() for item in store.list_runs()]

    @app.get("/api/v1/replay/{run_id}")
    async def replay(run_id: str, limit: int = 500) -> list[dict]:
        return [event.model_dump() for event in store.replay(run_id, limit=max(1, min(limit, 5000)))]

    @app.get("/api/v1/sessions")
    async def sessions() -> list[dict]:
        return [item.model_dump() for item in store.list_runs()]

    @app.get("/api/v1/sessions/current")
    async def current_session() -> dict:
        try:
            return store.current_session().model_dump()
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/sessions/{run_id}")
    async def session(run_id: str) -> dict:
        try:
            return store.get_session(run_id).model_dump()
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/sessions/{run_id}/snapshot")
    async def session_snapshot(run_id: str) -> dict:
        try:
            return store.session_snapshot(run_id).model_dump()
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/sessions/{run_id}/events")
    async def session_events(run_id: str, limit: int = Query(default=200, ge=1, le=5000)) -> list[dict]:
        try:
            return [item.model_dump() for item in store.recent_events(limit=limit, run_id=run_id)]
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/sessions/{run_id}/metrics")
    async def session_metrics(run_id: str, limit: int = Query(default=200, ge=1, le=5000)) -> list[dict]:
        try:
            return [item.model_dump() for item in store.session_metrics(run_id, limit=limit)]
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/sessions/{run_id}/replay")
    async def session_replay(run_id: str) -> dict:
        try:
            return store.session_replay(run_id).model_dump()
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

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
            session = store.current_session()
            await websocket.send_json(
                {
                    "type": "telemetry_update",
                    "session": session.model_dump(),
                    "snapshot": store.session_snapshot(session.run_id).model_dump(),
                }
            )
        except SessionNotFoundError:
            pass
        try:
            while True:
                await asyncio.sleep(30.0)
        except WebSocketDisconnect:
            legacy_hub.disconnect(websocket)
        except Exception:
            legacy_hub.disconnect(websocket)

    return app
