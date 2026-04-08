from __future__ import annotations

from typing import Any, Protocol

import httpx


class ReadModelAdapter(Protocol):
    async def get_snapshot(self, run_id: str | None = None) -> dict[str, Any]:
        raise NotImplementedError

    async def get_metrics(self, run_id: str | None = None, *, limit: int = 100) -> dict[str, Any]:
        raise NotImplementedError

    async def get_events(
        self,
        run_id: str | None = None,
        *,
        kind: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        raise NotImplementedError

    async def get_replay(self, run_id: str, *, limit: int = 500) -> dict[str, Any]:
        raise NotImplementedError

    async def list_runs(self) -> list[dict[str, Any]]:
        raise NotImplementedError


class HttpReadModelAdapter:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    async def get_snapshot(self, run_id: str | None = None) -> dict[str, Any]:
        if run_id is None:
            return await self._get_json("/api/v1/snapshot")
        return await self._get_json(f"/api/v1/sessions/{run_id}/snapshot")

    async def get_metrics(self, run_id: str | None = None, *, limit: int = 100) -> dict[str, Any]:
        effective_run_id = run_id or await self._current_run_id()
        if effective_run_id is None:
            return {"run_id": None, "metrics": [], "source": "telemetry_api"}
        metrics = await self._get_json_or_default(
            f"/api/v1/sessions/{effective_run_id}/metrics",
            default=[],
            params={"limit": max(1, min(limit, 5000))},
        )
        return {
            "run_id": effective_run_id,
            "metrics": metrics,
            "source": "telemetry_api",
        }

    async def get_events(
        self,
        run_id: str | None = None,
        *,
        kind: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": max(1, min(limit, 5000))}
        if run_id is not None:
            params["run_id"] = run_id
        if kind:
            params["kind"] = kind
        events = await self._get_json_or_default("/api/v1/events", default=[], params=params)
        return {
            "run_id": run_id,
            "events": events,
            "source": "telemetry_api",
        }

    async def get_replay(self, run_id: str, *, limit: int = 500) -> dict[str, Any]:
        replay = await self._get_json_or_default(
            f"/api/v1/sessions/{run_id}/replay",
            default={"run_id": run_id, "snapshot": {}, "events": [], "metrics": []},
            params={"limit": max(1, min(limit, 5000))},
        )
        if "run_id" not in replay:
            replay["run_id"] = run_id
        return replay

    async def list_runs(self) -> list[dict[str, Any]]:
        response = await self._get_json("/api/v1/runs")
        if isinstance(response, list):
            return response
        raise TypeError("telemetry api returned a non-list payload for /api/v1/runs")

    async def _get_json(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{self._base_url}{path}", params=params)
            response.raise_for_status()
            return response.json()

    async def _get_json_or_default(
        self,
        path: str,
        *,
        default: Any,
        params: dict[str, Any] | None = None,
    ) -> Any:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{self._base_url}{path}", params=params)
            if response.status_code == 404:
                return default
            response.raise_for_status()
            return response.json()

    async def _current_run_id(self) -> str | None:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{self._base_url}/api/v1/sessions/current")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            payload = response.json()
            return payload.get("run_id")
