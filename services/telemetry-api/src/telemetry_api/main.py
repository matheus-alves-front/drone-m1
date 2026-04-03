from __future__ import annotations

import asyncio
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect

from .models import ReplayModel, SessionSummaryModel, SnapshotModel, TelemetryEnvelopeModel
from .store import SessionNotFoundError, TelemetryStore


def create_app(*, storage_root: str | Path | None = None) -> FastAPI:
    resolved_storage_root = Path(
        storage_root
        if storage_root is not None
        else os.environ.get("TELEMETRY_API_STORAGE_ROOT", "services/telemetry-api/data")
    ).resolve()
    store = TelemetryStore(resolved_storage_root)

    app = FastAPI(title="Telemetry API", version="0.1.0")
    app.state.telemetry_store = store

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/ingest", status_code=202)
    def ingest(envelope: TelemetryEnvelopeModel) -> dict[str, str]:
        store.ingest(envelope)
        return {"status": "accepted"}

    @app.get("/api/v1/sessions", response_model=list[SessionSummaryModel])
    def list_sessions() -> list[SessionSummaryModel]:
        return store.list_sessions()

    @app.get("/api/v1/sessions/current", response_model=SessionSummaryModel)
    def current_session() -> SessionSummaryModel:
        try:
            return store.current_session()
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/sessions/{run_id}", response_model=SessionSummaryModel)
    def get_session(run_id: str) -> SessionSummaryModel:
        try:
            return store.get_session(run_id)
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/sessions/{run_id}/snapshot", response_model=SnapshotModel)
    def get_snapshot(run_id: str) -> SnapshotModel:
        try:
            return store.get_snapshot(run_id)
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/sessions/{run_id}/events")
    def get_events(run_id: str, limit: int = Query(default=200, ge=1, le=2000)) -> list[dict]:
        try:
            return [item.model_dump() for item in store.get_events(run_id, limit=limit)]
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/sessions/{run_id}/metrics")
    def get_metrics(run_id: str, limit: int = Query(default=200, ge=1, le=2000)) -> list[dict]:
        try:
            return [item.model_dump() for item in store.get_metrics(run_id, limit=limit)]
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/sessions/{run_id}/replay", response_model=ReplayModel)
    def get_replay(run_id: str) -> ReplayModel:
        try:
            return store.get_replay(run_id)
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.websocket("/ws/telemetry/{requested_run_id}")
    async def telemetry_stream(websocket: WebSocket, requested_run_id: str) -> None:
        await websocket.accept()
        last_signature: tuple[int, int, int] | None = None
        try:
            while True:
                try:
                    session = (
                        store.current_session()
                        if requested_run_id == "current"
                        else store.get_session(requested_run_id)
                    )
                    snapshot = store.get_snapshot(session.run_id)
                    recent_events = [item.model_dump() for item in store.get_events(session.run_id, limit=25)]
                    latest_metrics = store.get_metrics(session.run_id, limit=1)
                    signature = (session.updated_at_ns, session.event_count, session.metrics_count)
                    if signature != last_signature:
                        await websocket.send_json(
                            {
                                "type": "telemetry_update",
                                "session": session.model_dump(),
                                "snapshot": snapshot.model_dump(),
                                "recent_events": recent_events,
                                "latest_metric": latest_metrics[-1].model_dump() if latest_metrics else None,
                            }
                        )
                        last_signature = signature
                except SessionNotFoundError:
                    await websocket.send_json({"type": "telemetry_update", "session": None})
                await asyncio.sleep(0.5)
        except WebSocketDisconnect:
            return

    return app


app = create_app()
