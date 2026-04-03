from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ScenarioStatus(str, Enum):
    COMPLETED = "completed"
    CONNECTION_FAILED = "connection_failed"
    TIMEOUT = "timeout"
    ASSERTION_FAILED = "assertion_failed"
    FAILED = "failed"


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
    waypoint_offset_north_m: float
    waypoint_offset_east_m: float
    arrival_tolerance_m: float
    altitude_tolerance_m: float
    takeoff_timeout_s: float
    waypoint_timeout_s: float
    land_timeout_s: float


@dataclass(frozen=True)
class ScenarioContract:
    name: str
    scenario_path: str
    objective: str
    connection: ConnectionContract
    flight: FlightContract


@dataclass(frozen=True)
class PositionSample:
    latitude_deg: float
    longitude_deg: float
    absolute_altitude_m: float
    relative_altitude_m: float


@dataclass(frozen=True)
class ScenarioAssertion:
    name: str
    success: bool
    detail: str


@dataclass
class ScenarioResult:
    scenario_name: str
    scenario_path: str
    status: ScenarioStatus
    system_address: str
    assertions: list[ScenarioAssertion] = field(default_factory=list)
    detail: str = ""
    target_position: PositionSample | None = None
    final_position: PositionSample | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload
