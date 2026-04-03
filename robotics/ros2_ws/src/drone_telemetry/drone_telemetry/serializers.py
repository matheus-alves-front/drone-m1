from __future__ import annotations

from typing import Any

from .contracts import TelemetryEnvelope


def stamp_to_ns(stamp: Any) -> int:
    return (int(getattr(stamp, "sec", 0)) * 1_000_000_000) + int(getattr(stamp, "nanosec", 0))


def build_envelope(
    *,
    run_id: str,
    source: str,
    kind: str,
    topic: str,
    stamp: Any,
    payload: dict[str, Any],
) -> TelemetryEnvelope:
    return TelemetryEnvelope(
        run_id=run_id,
        source=source,
        kind=kind,
        topic=topic,
        stamp_ns=stamp_to_ns(stamp),
        payload=payload,
    )


def serialize_vehicle_state(msg: Any) -> dict[str, Any]:
    return {
        "connected": bool(msg.connected),
        "armed": bool(msg.armed),
        "landed": bool(msg.landed),
        "failsafe": bool(msg.failsafe),
        "preflight_checks_pass": bool(msg.preflight_checks_pass),
        "position_valid": bool(msg.position_valid),
        "nav_state": str(msg.nav_state),
        "altitude_m": float(msg.altitude_m),
        "relative_altitude_m": float(msg.relative_altitude_m),
        "absolute_altitude_m": float(msg.absolute_altitude_m),
        "latitude_deg": float(msg.latitude_deg),
        "longitude_deg": float(msg.longitude_deg),
    }


def serialize_command_status(msg: Any) -> dict[str, Any]:
    return {
        "command": str(msg.command),
        "px4_command": int(msg.px4_command),
        "result": int(msg.result),
        "accepted": bool(msg.accepted),
        "result_label": str(msg.result_label),
    }


def serialize_mission_status(msg: Any) -> dict[str, Any]:
    return {
        "mission_id": str(msg.mission_id),
        "phase": str(msg.phase),
        "active": bool(msg.active),
        "completed": bool(msg.completed),
        "aborted": bool(msg.aborted),
        "failed": bool(msg.failed),
        "terminal": bool(msg.terminal),
        "succeeded": bool(msg.succeeded),
        "detail": str(msg.detail),
        "current_waypoint_index": int(msg.current_waypoint_index),
        "total_waypoints": int(msg.total_waypoints),
        "last_command": str(msg.last_command),
    }


def serialize_safety_status(msg: Any) -> dict[str, Any]:
    return {
        "active": bool(msg.active),
        "mission_abort_requested": bool(msg.mission_abort_requested),
        "vehicle_command_sent": bool(msg.vehicle_command_sent),
        "rule": str(msg.rule),
        "action": str(msg.action),
        "source": str(msg.source),
        "detail": str(msg.detail),
        "trigger_count": int(msg.trigger_count),
    }


def serialize_tracked_object(msg: Any) -> dict[str, Any]:
    return {
        "tracked": bool(msg.tracked),
        "track_id": int(msg.track_id),
        "label": str(msg.label),
        "confidence": float(msg.confidence),
        "center_x": float(msg.center_x),
        "center_y": float(msg.center_y),
        "width": float(msg.width),
        "height": float(msg.height),
        "age": int(msg.age),
        "state": str(msg.state),
    }


def serialize_perception_heartbeat(msg: Any) -> dict[str, Any]:
    return {
        "healthy": bool(msg.healthy),
        "pipeline_latency_s": float(msg.pipeline_latency_s),
    }


def serialize_perception_event(msg: Any) -> dict[str, Any]:
    return {
        "event_type": str(msg.event_type),
        "track_id": int(msg.track_id),
        "label": str(msg.label),
        "confidence": float(msg.confidence),
        "detail": str(msg.detail),
    }
