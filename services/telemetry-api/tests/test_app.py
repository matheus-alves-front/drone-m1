from pathlib import Path

from fastapi.testclient import TestClient

from telemetry_api.app import create_app


def test_ingest_updates_current_snapshot_metrics_events_and_replay(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))

    response = client.post(
        "/api/v1/ingest",
        json={
            "run_id": "run-a",
            "session_id": "session-a",
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
    assert snapshot.json()["run_id"] == "run-a"
    assert snapshot.json()["session_id"] == "session-a"
    assert snapshot.json()["vehicle_state"]["connected"] is True

    metrics = client.get("/api/v1/metrics")
    assert metrics.status_code == 200
    assert metrics.json()["total_events"] == 1
    assert metrics.json()["counts_by_kind"]["vehicle_state"] == 1
    assert metrics.json()["counts_by_run"]["run-a"] == 1

    events = client.get("/api/v1/events")
    assert events.status_code == 200
    assert len(events.json()) == 1
    assert events.json()[0]["kind"] == "vehicle_state"

    replay = client.get("/api/v1/replay/run-a")
    assert replay.status_code == 200
    assert len(replay.json()) == 1
    assert replay.json()[0]["run_id"] == "run-a"
    assert (tmp_path / "runs" / "run-a" / "events.jsonl").exists()


def test_runs_endpoint_returns_session_summary_and_filters_events(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    payloads = [
        {
            "run_id": "run-a",
            "session_id": "session-a",
            "source": "telemetry_bridge",
            "kind": "mission_status",
            "topic": "/drone/mission_status",
            "stamp_ns": 100,
            "payload": {"phase": "hover", "active": True},
        },
        {
            "run_id": "run-a",
            "session_id": "session-a",
            "source": "telemetry_bridge",
            "kind": "safety_status",
            "topic": "/drone/safety_status",
            "stamp_ns": 110,
            "payload": {"rule": "perception_timeout", "action": "abort"},
        },
        {
            "run_id": "run-b",
            "session_id": "session-b",
            "source": "telemetry_bridge",
            "kind": "vehicle_state",
            "topic": "/drone/vehicle_state",
            "stamp_ns": 200,
            "payload": {"connected": True},
        },
    ]
    for payload in payloads:
        assert client.post("/api/v1/ingest", json=payload).status_code == 202

    response = client.get("/api/v1/runs")
    assert response.status_code == 200
    runs = {item["run_id"]: item for item in response.json()}
    assert runs["run-a"]["event_count"] == 2
    assert runs["run-a"]["session_id"] == "session-a"
    assert runs["run-b"]["last_kind"] == "vehicle_state"

    filtered_events = client.get("/api/v1/events", params={"run_id": "run-a", "kind": "safety_status"})
    assert filtered_events.status_code == 200
    assert len(filtered_events.json()) == 1
    assert filtered_events.json()[0]["kind"] == "safety_status"
