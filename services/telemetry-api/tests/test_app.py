from pathlib import Path

from fastapi.testclient import TestClient

from telemetry_api.app import create_app


def test_ingest_updates_snapshot_metrics_and_replay(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))

    response = client.post(
        "/api/v1/ingest",
        json={
            "run_id": "run-a",
            "source": "telemetry_bridge",
            "kind": "vehicle_state",
            "topic": "/drone/vehicle_state",
            "stamp_ns": 123,
            "payload": {"connected": True, "armed": False},
        },
    )

    assert response.status_code == 202
    assert response.json()["status"] == "accepted"

    snapshot = client.get("/api/v1/snapshot")
    assert snapshot.status_code == 200
    assert snapshot.json()["current_run_id"] == "run-a"
    assert snapshot.json()["latest_by_kind"]["vehicle_state"]["payload"]["connected"] is True

    metrics = client.get("/api/v1/metrics")
    assert metrics.status_code == 200
    assert metrics.json()["total_events"] == 1
    assert metrics.json()["counts_by_kind"]["vehicle_state"] == 1

    replay = client.get("/api/v1/replay/run-a")
    assert replay.status_code == 200
    assert len(replay.json()) == 1
    assert (tmp_path / "runs" / "run-a" / "events.jsonl").exists()


def test_runs_endpoint_returns_summary(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    payloads = [
        {
            "run_id": "run-a",
            "source": "telemetry_bridge",
            "kind": "mission_status",
            "topic": "/drone/mission_status",
            "stamp_ns": 100,
            "payload": {"phase": "hover"},
        },
        {
            "run_id": "run-b",
            "source": "telemetry_bridge",
            "kind": "safety_status",
            "topic": "/drone/safety_status",
            "stamp_ns": 200,
            "payload": {"rule": "perception_timeout"},
        },
    ]
    for payload in payloads:
        assert client.post("/api/v1/ingest", json=payload).status_code == 202

    response = client.get("/api/v1/runs")
    assert response.status_code == 200
    runs = {item["run_id"]: item for item in response.json()}
    assert runs["run-a"]["event_count"] == 1
    assert runs["run-b"]["last_kind"] == "safety_status"
