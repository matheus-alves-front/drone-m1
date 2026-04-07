from __future__ import annotations

from fastapi.testclient import TestClient

from telemetry_api.main import create_app


def build_envelope(**overrides):
    payload = {
        "run_id": "run-123",
        "session_id": "session-123",
        "source": "telemetry_bridge_node",
        "kind": "mission_status",
        "topic": "/drone/mission_status",
        "stamp_ns": 123456789,
        "payload": {
            "mission_id": "patrol_basic",
            "phase": "patrol",
            "active": True,
            "completed": False,
            "aborted": False,
            "failed": False,
            "terminal": False,
            "succeeded": False,
            "detail": "waypoint 1",
            "current_waypoint_index": 1,
            "total_waypoints": 3,
            "last_command": "goto",
        },
    }
    payload.update(overrides)
    return payload


def test_ingest_creates_current_session_snapshot_and_replay(tmp_path):
    app = create_app(storage_root=tmp_path)
    client = TestClient(app)

    response = client.post("/api/v1/ingest", json=build_envelope())
    assert response.status_code == 202

    current = client.get("/api/v1/sessions/current")
    assert current.status_code == 200
    assert current.json()["run_id"] == "run-123"
    assert current.json()["session_id"] == "session-123"

    sessions = client.get("/api/v1/sessions")
    assert sessions.status_code == 200
    assert sessions.json()[0]["run_id"] == "run-123"

    snapshot = client.get("/api/v1/sessions/run-123/snapshot")
    assert snapshot.status_code == 200
    assert snapshot.json()["mission_status"]["phase"] == "patrol"

    events = client.get("/api/v1/sessions/run-123/events")
    assert events.status_code == 200
    assert events.json()[0]["kind"] == "mission_status"

    metrics = client.get("/api/v1/sessions/run-123/metrics")
    assert metrics.status_code == 200
    assert metrics.json()[0]["mission_phase"] == "patrol"

    replay = client.get("/api/v1/sessions/run-123/replay")
    assert replay.status_code == 200
    assert replay.json()["run_id"] == "run-123"
    assert len(replay.json()["events"]) == 1
    assert len(replay.json()["metrics"]) == 1


def test_websocket_emits_updates_for_current_session(tmp_path):
    app = create_app(storage_root=tmp_path)
    client = TestClient(app)

    with client.websocket_connect("/ws/telemetry/current") as websocket:
        client.post("/api/v1/ingest", json=build_envelope())
        message = websocket.receive_json()

    assert message["type"] == "telemetry_update"
    assert message["session"]["run_id"] == "run-123"
    assert message["snapshot"]["mission_status"]["phase"] == "patrol"
