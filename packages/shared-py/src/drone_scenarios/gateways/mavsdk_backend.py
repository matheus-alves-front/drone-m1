from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from typing import Any

from ..contracts import PositionSample
from ..errors import ConnectionFailure, ScenarioCommandFailed, ScenarioTimeout
from ..geodesy import horizontal_distance_m


class MavsdkVehicleGateway:
    def __init__(self) -> None:
        self._system = None

    async def connect(self, system_address: str, timeout_s: float) -> None:
        try:
            from mavsdk import System
        except ImportError as exc:
            raise ConnectionFailure(
                "mavsdk is not installed; install the optional dependency or use the phase-2 validation scripts"
            ) from exc

        self._system = System()
        await self._system.connect(system_address=system_address)

        try:
            await asyncio.wait_for(self._wait_connection_state(), timeout_s)
        except asyncio.TimeoutError as exc:
            raise ConnectionFailure(f"timed out while connecting to {system_address}") from exc

    async def wait_until_ready_position(self, timeout_s: float) -> PositionSample:
        if self._system is None:
            raise ConnectionFailure("system is not connected")

        try:
            await asyncio.wait_for(self._wait_health_ready(), timeout_s)
            return await asyncio.wait_for(self._next_position(), timeout_s)
        except asyncio.TimeoutError as exc:
            raise ScenarioTimeout("timed out while waiting for global and home position") from exc

    async def arm(self, timeout_s: float) -> None:
        await self._run_action(self._system.action.arm(), "arm", timeout_s)

    async def wait_until_armed(self, timeout_s: float) -> None:
        try:
            await asyncio.wait_for(self._wait_boolean_stream(self._system.telemetry.armed(), True), timeout_s)
        except asyncio.TimeoutError as exc:
            raise ScenarioTimeout("timed out while waiting for armed state") from exc

    async def set_takeoff_altitude(self, altitude_m: float, timeout_s: float) -> None:
        await self._run_action(self._system.action.set_takeoff_altitude(altitude_m), "set_takeoff_altitude", timeout_s)

    async def takeoff(self, timeout_s: float) -> None:
        await self._run_action(self._system.action.takeoff(), "takeoff", timeout_s)

    async def wait_until_altitude(self, minimum_relative_altitude_m: float, timeout_s: float) -> PositionSample:
        try:
            return await asyncio.wait_for(
                self._wait_until_position(lambda sample: sample.relative_altitude_m >= minimum_relative_altitude_m),
                timeout_s,
            )
        except asyncio.TimeoutError as exc:
            raise ScenarioTimeout("timed out while waiting for takeoff altitude") from exc

    async def current_position(self, timeout_s: float) -> PositionSample:
        try:
            return await asyncio.wait_for(self._next_position(), timeout_s)
        except asyncio.TimeoutError as exc:
            raise ScenarioTimeout("timed out while reading current position") from exc

    async def goto_location(
        self,
        latitude_deg: float,
        longitude_deg: float,
        absolute_altitude_m: float,
        yaw_deg: float,
        timeout_s: float,
    ) -> None:
        await self._run_action(
            self._system.action.goto_location(latitude_deg, longitude_deg, absolute_altitude_m, yaw_deg),
            "goto_location",
            timeout_s,
        )

    async def wait_until_near(
        self,
        target: PositionSample,
        tolerance_m: float,
        timeout_s: float,
    ) -> PositionSample:
        try:
            return await asyncio.wait_for(
                self._wait_until_position(
                    lambda sample: horizontal_distance_m(sample, target) <= tolerance_m
                    and abs(sample.absolute_altitude_m - target.absolute_altitude_m) <= tolerance_m
                ),
                timeout_s,
            )
        except asyncio.TimeoutError as exc:
            raise ScenarioTimeout("timed out while waiting for waypoint arrival") from exc

    async def land(self, timeout_s: float) -> None:
        await self._run_action(self._system.action.land(), "land", timeout_s)

    async def wait_until_landed(self, timeout_s: float) -> PositionSample:
        try:
            await asyncio.wait_for(self._wait_boolean_stream(self._system.telemetry.in_air(), False), timeout_s)
            return await asyncio.wait_for(self._next_position(), timeout_s)
        except asyncio.TimeoutError as exc:
            raise ScenarioTimeout("timed out while waiting for landed state") from exc

    async def _run_action(self, coroutine: Any, action_name: str, timeout_s: float) -> None:
        if self._system is None:
            raise ConnectionFailure("system is not connected")

        try:
            await asyncio.wait_for(coroutine, timeout_s)
        except asyncio.TimeoutError as exc:
            raise ScenarioTimeout(f"{action_name} timed out") from exc
        except Exception as exc:  # pragma: no cover
            raise ScenarioCommandFailed(f"{action_name} failed: {exc}") from exc

    async def _wait_connection_state(self) -> None:
        async for state in self._system.core.connection_state():
            if state.is_connected:
                return

    async def _wait_health_ready(self) -> None:
        async for health in self._system.telemetry.health():
            if health.is_global_position_ok and health.is_home_position_ok:
                return

    async def _wait_boolean_stream(self, stream: AsyncIterator[bool], expected: bool) -> None:
        async for value in stream:
            if value is expected:
                return

    async def _wait_until_position(self, predicate: Callable[[PositionSample], bool]) -> PositionSample:
        async for sample in self._position_stream():
            if predicate(sample):
                return sample
        raise ScenarioTimeout("position stream ended unexpectedly")

    async def _next_position(self) -> PositionSample:
        async for sample in self._position_stream():
            return sample
        raise ScenarioTimeout("position stream ended unexpectedly")

    async def _position_stream(self) -> AsyncIterator[PositionSample]:
        async for position in self._system.telemetry.position():
            yield PositionSample(
                latitude_deg=position.latitude_deg,
                longitude_deg=position.longitude_deg,
                absolute_altitude_m=position.absolute_altitude_m,
                relative_altitude_m=position.relative_altitude_m,
            )
