from __future__ import annotations

import json
from pathlib import Path

from .contracts import ConnectionContract, FlightContract, MissionContract, PatrolContract


class MissionValidationError(ValueError):
    """Raised when the mission contract is malformed."""


def load_mission_contract(path: str | Path) -> MissionContract:
    scenario_path = Path(path)
    try:
        payload = json.loads(scenario_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise MissionValidationError(f"mission contract not found: {scenario_path}") from exc
    except json.JSONDecodeError as exc:
        raise MissionValidationError(f"invalid JSON in mission contract: {scenario_path}") from exc

    required_fields = ("name", "objective", "flight", "patrol")
    missing_fields = [field for field in required_fields if field not in payload]
    if missing_fields:
        missing = ", ".join(missing_fields)
        raise MissionValidationError(f"mission contract missing required fields: {missing}")

    try:
        connection = ConnectionContract(**payload.get("connection", {}))
        flight = FlightContract(**payload["flight"])
        patrol = PatrolContract(**payload["patrol"])
    except TypeError as exc:
        raise MissionValidationError(f"invalid mission contract payload: {exc}") from exc

    if len(patrol.waypoint_offsets_north_m) != len(patrol.waypoint_offsets_east_m):
        raise MissionValidationError("patrol waypoint offset lists must have the same size")
    if not patrol.waypoint_offsets_north_m:
        raise MissionValidationError("patrol contract must define at least one waypoint")
    if flight.takeoff_altitude_m <= 0.0:
        raise MissionValidationError("takeoff altitude must be positive")

    return MissionContract(
        name=payload["name"],
        scenario_path=str(scenario_path),
        objective=payload["objective"],
        connection=connection,
        flight=flight,
        patrol=patrol,
    )
