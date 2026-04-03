from __future__ import annotations

from typing import Protocol

from ..contracts import PositionSample


class VehicleGateway(Protocol):
    async def connect(self, system_address: str, timeout_s: float) -> None:
        ...

    async def wait_until_ready_position(self, timeout_s: float) -> PositionSample:
        ...

    async def arm(self, timeout_s: float) -> None:
        ...

    async def wait_until_armed(self, timeout_s: float) -> None:
        ...

    async def set_takeoff_altitude(self, altitude_m: float, timeout_s: float) -> None:
        ...

    async def takeoff(self, timeout_s: float) -> None:
        ...

    async def wait_until_altitude(self, minimum_relative_altitude_m: float, timeout_s: float) -> PositionSample:
        ...

    async def current_position(self, timeout_s: float) -> PositionSample:
        ...

    async def goto_location(
        self,
        latitude_deg: float,
        longitude_deg: float,
        absolute_altitude_m: float,
        yaw_deg: float,
        timeout_s: float,
    ) -> None:
        ...

    async def wait_until_near(
        self,
        target: PositionSample,
        tolerance_m: float,
        timeout_s: float,
    ) -> PositionSample:
        ...

    async def land(self, timeout_s: float) -> None:
        ...

    async def wait_until_landed(self, timeout_s: float) -> PositionSample:
        ...
