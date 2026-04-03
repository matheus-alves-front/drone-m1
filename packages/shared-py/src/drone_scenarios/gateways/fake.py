from __future__ import annotations

import asyncio
from dataclasses import replace

from ..contracts import PositionSample
from ..errors import ConnectionFailure, ScenarioTimeout


class FakeVehicleGateway:
    def __init__(self, failure_mode: str | None = None) -> None:
        self.failure_mode = failure_mode
        self.connected = False
        self.armed = False
        self.in_air = False
        self.position = PositionSample(
            latitude_deg=-22.9985032,
            longitude_deg=-43.3658758,
            absolute_altitude_m=100.0,
            relative_altitude_m=0.0,
        )

    async def connect(self, system_address: str, timeout_s: float) -> None:
        await asyncio.sleep(0)
        if self.failure_mode == "connection":
            raise ConnectionFailure(f"fake backend could not connect to {system_address}")
        self.connected = True

    async def wait_until_ready_position(self, timeout_s: float) -> PositionSample:
        await asyncio.sleep(0)
        if not self.connected:
            raise ConnectionFailure("fake backend is not connected")
        return self.position

    async def arm(self, timeout_s: float) -> None:
        await asyncio.sleep(0)
        self.armed = True

    async def wait_until_armed(self, timeout_s: float) -> None:
        await asyncio.sleep(0)
        if self.failure_mode == "armed_timeout":
            raise ScenarioTimeout("fake backend timed out waiting for armed state")
        if not self.armed:
            raise ScenarioTimeout("fake backend never armed")

    async def set_takeoff_altitude(self, altitude_m: float, timeout_s: float) -> None:
        await asyncio.sleep(0)

    async def takeoff(self, timeout_s: float) -> None:
        await asyncio.sleep(0)
        self.in_air = True
        self.position = replace(
            self.position,
            absolute_altitude_m=self.position.absolute_altitude_m + 3.0,
            relative_altitude_m=3.0,
        )

    async def wait_until_altitude(self, minimum_relative_altitude_m: float, timeout_s: float) -> PositionSample:
        await asyncio.sleep(0)
        if self.failure_mode == "takeoff_timeout":
            raise ScenarioTimeout("fake backend timed out during takeoff")
        return self.position

    async def current_position(self, timeout_s: float) -> PositionSample:
        await asyncio.sleep(0)
        return self.position

    async def goto_location(
        self,
        latitude_deg: float,
        longitude_deg: float,
        absolute_altitude_m: float,
        yaw_deg: float,
        timeout_s: float,
    ) -> None:
        await asyncio.sleep(0)
        self.position = replace(
            self.position,
            latitude_deg=latitude_deg,
            longitude_deg=longitude_deg,
            absolute_altitude_m=absolute_altitude_m,
        )

    async def wait_until_near(
        self,
        target: PositionSample,
        tolerance_m: float,
        timeout_s: float,
    ) -> PositionSample:
        await asyncio.sleep(0)
        if self.failure_mode == "waypoint_timeout":
            raise ScenarioTimeout("fake backend timed out while approaching waypoint")
        return self.position

    async def land(self, timeout_s: float) -> None:
        await asyncio.sleep(0)
        self.in_air = False
        self.armed = False
        self.position = replace(
            self.position,
            absolute_altitude_m=self.position.absolute_altitude_m - self.position.relative_altitude_m,
            relative_altitude_m=0.0,
        )

    async def wait_until_landed(self, timeout_s: float) -> PositionSample:
        await asyncio.sleep(0)
        if self.failure_mode == "land_timeout":
            raise ScenarioTimeout("fake backend timed out while landing")
        return self.position
