from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ConnectionContract:
    system_address: str = "udp://:14540"
    connection_timeout_s: float = 20.0
    ready_timeout_s: float = 20.0
    action_timeout_s: float = 20.0


@dataclass(frozen=True)
class FlightContract:
    takeoff_altitude_m: float
    hover_duration_s: float
    arrival_tolerance_m: float
    takeoff_timeout_s: float
    waypoint_timeout_s: float
    land_timeout_s: float
    abort_land_timeout_s: float = 60.0


@dataclass(frozen=True)
class PatrolContract:
    waypoint_offsets_north_m: list[float] = field(default_factory=list)
    waypoint_offsets_east_m: list[float] = field(default_factory=list)
    return_to_home: bool = True


@dataclass(frozen=True)
class MissionContract:
    name: str
    scenario_path: str
    objective: str
    connection: ConnectionContract
    flight: FlightContract
    patrol: PatrolContract


@dataclass(frozen=True)
class PositionSample:
    latitude_deg: float
    longitude_deg: float
    absolute_altitude_m: float
    relative_altitude_m: float
