from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator, Callable
from typing import Any, Protocol

from .contracts import PositionSample
from .errors import MissionCommandFailed, MissionConnectionFailure, MissionTimeout
from .geodesy import horizontal_distance_m


class MissionGateway(Protocol):
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


class MavsdkMissionGateway:
    def __init__(self) -> None:
        self._system = None

    async def connect(self, system_address: str, timeout_s: float) -> None:
        try:
            from mavsdk import System
        except ImportError as exc:
            raise MissionConnectionFailure(
                "mavsdk is not installed; install the phase-2 mission dependency set before running phase 4"
            ) from exc

        self._system = System()
        await self._system.connect(system_address=system_address)

        try:
            await asyncio.wait_for(self._wait_connection_state(), timeout_s)
        except asyncio.TimeoutError as exc:
            raise MissionConnectionFailure(f"timed out while connecting to {system_address}") from exc

    async def wait_until_ready_position(self, timeout_s: float) -> PositionSample:
        if self._system is None:
            raise MissionConnectionFailure("system is not connected")

        try:
            await asyncio.wait_for(self._wait_health_ready(), timeout_s)
            return await asyncio.wait_for(self._next_position(), timeout_s)
        except asyncio.TimeoutError as exc:
            raise MissionTimeout("timed out while waiting for global and home position") from exc

    async def arm(self, timeout_s: float) -> None:
        await self._run_action(self._system.action.arm(), "arm", timeout_s)

    async def wait_until_armed(self, timeout_s: float) -> None:
        try:
            await asyncio.wait_for(self._wait_boolean_stream(self._system.telemetry.armed(), True), timeout_s)
        except asyncio.TimeoutError as exc:
            raise MissionTimeout("timed out while waiting for armed state") from exc

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
            raise MissionTimeout("timed out while waiting for takeoff altitude") from exc

    async def current_position(self, timeout_s: float) -> PositionSample:
        try:
            return await asyncio.wait_for(self._next_position(), timeout_s)
        except asyncio.TimeoutError as exc:
            raise MissionTimeout("timed out while reading current position") from exc

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
                    lambda sample: horizontal_distance_m(
                        sample.latitude_deg,
                        sample.longitude_deg,
                        target.latitude_deg,
                        target.longitude_deg,
                    )
                    <= tolerance_m
                    and abs(sample.absolute_altitude_m - target.absolute_altitude_m) <= tolerance_m
                ),
                timeout_s,
            )
        except asyncio.TimeoutError as exc:
            raise MissionTimeout("timed out while waiting for waypoint arrival") from exc

    async def land(self, timeout_s: float) -> None:
        await self._run_action(self._system.action.land(), "land", timeout_s)

    async def wait_until_landed(self, timeout_s: float) -> PositionSample:
        try:
            await asyncio.wait_for(self._wait_boolean_stream(self._system.telemetry.in_air(), False), timeout_s)
            return await asyncio.wait_for(self._next_position(), timeout_s)
        except asyncio.TimeoutError as exc:
            raise MissionTimeout("timed out while waiting for landed state") from exc

    async def _run_action(self, coroutine: Any, action_name: str, timeout_s: float) -> None:
        if self._system is None:
            raise MissionConnectionFailure("system is not connected")

        try:
            await asyncio.wait_for(coroutine, timeout_s)
        except asyncio.TimeoutError as exc:
            raise MissionTimeout(f"{action_name} timed out") from exc
        except Exception as exc:  # pragma: no cover
            raise MissionCommandFailed(f"{action_name} failed: {exc}") from exc

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
        raise MissionTimeout("position stream ended unexpectedly")

    async def _next_position(self) -> PositionSample:
        async for sample in self._position_stream():
            return sample
        raise MissionTimeout("position stream ended unexpectedly")

    async def _position_stream(self) -> AsyncIterator[PositionSample]:
        async for position in self._system.telemetry.position():
            yield PositionSample(
                latitude_deg=position.latitude_deg,
                longitude_deg=position.longitude_deg,
                absolute_altitude_m=position.absolute_altitude_m,
                relative_altitude_m=position.relative_altitude_m,
            )


class Ros2MissionGateway:
    """Mission gateway that talks to PX4 only through the ROS 2 domain boundary."""

    def __init__(
        self,
        *,
        publish_command: Callable[..., None],
        get_vehicle_state: Callable[[], Any | None],
        get_command_status: Callable[[], tuple[int, Any | None]],
        command_retry_interval_s: float = 3.0,
        max_command_retries: int = 5,
        takeoff_altitude_tolerance_m: float = 0.4,
    ) -> None:
        self._publish_command = publish_command
        self._get_vehicle_state = get_vehicle_state
        self._get_command_status = get_command_status
        self._command_retry_interval_s = max(command_retry_interval_s, 0.1)
        self._max_command_retries = max(max_command_retries, 1)
        self._takeoff_altitude_tolerance_m = max(takeoff_altitude_tolerance_m, 0.0)
        self._configured_takeoff_altitude_m = 0.0
        self._last_command_name = ""

    @property
    def last_command_name(self) -> str:
        return self._last_command_name

    async def connect(self, system_address: str, timeout_s: float) -> None:
        del system_address
        await self._wait_for_vehicle_state(
            timeout_s,
            predicate=lambda msg: bool(msg.connected),
            timeout_message="timed out while waiting for ROS 2 vehicle connectivity",
        )

    async def wait_until_ready_position(self, timeout_s: float) -> PositionSample:
        return await self._wait_for_position(
            timeout_s,
            predicate=lambda msg: bool(msg.connected) and bool(msg.position_valid),
            timeout_message="timed out while waiting for connected vehicle with valid position",
        )

    async def arm(self, timeout_s: float) -> None:
        await self._publish_and_wait_ack("arm", timeout_s)

    async def wait_until_armed(self, timeout_s: float) -> None:
        await self._wait_for_vehicle_state(
            timeout_s,
            predicate=lambda msg: bool(msg.connected) and bool(msg.armed),
            timeout_message="timed out while waiting for armed state",
        )

    async def set_takeoff_altitude(self, altitude_m: float, timeout_s: float) -> None:
        await asyncio.sleep(0)
        self._configured_takeoff_altitude_m = max(altitude_m, 0.5)

    async def takeoff(self, timeout_s: float) -> None:
        await self._publish_and_wait_ack(
            "takeoff",
            timeout_s,
            target_altitude_m=max(self._configured_takeoff_altitude_m, 0.0),
        )

    async def wait_until_altitude(self, minimum_relative_altitude_m: float, timeout_s: float) -> PositionSample:
        minimum_observed_altitude_m = max(
            minimum_relative_altitude_m - self._takeoff_altitude_tolerance_m,
            0.0,
        )
        return await self._wait_for_position(
            timeout_s,
            predicate=lambda msg: bool(msg.connected)
            and bool(msg.position_valid)
            and float(msg.relative_altitude_m) >= minimum_observed_altitude_m,
            timeout_message="timed out while waiting for takeoff altitude",
        )

    async def current_position(self, timeout_s: float) -> PositionSample:
        return await self._wait_for_position(
            timeout_s,
            predicate=lambda msg: bool(msg.connected) and bool(msg.position_valid),
            timeout_message="timed out while reading current position",
        )

    async def goto_location(
        self,
        latitude_deg: float,
        longitude_deg: float,
        absolute_altitude_m: float,
        yaw_deg: float,
        timeout_s: float,
    ) -> None:
        del timeout_s
        self._last_command_name = "goto"
        self._publish_command(
            "goto",
            target_latitude_deg=latitude_deg,
            target_longitude_deg=longitude_deg,
            target_absolute_altitude_m=absolute_altitude_m,
            target_yaw_deg=yaw_deg,
        )
        await asyncio.sleep(0)

    async def wait_until_near(
        self,
        target: PositionSample,
        tolerance_m: float,
        timeout_s: float,
    ) -> PositionSample:
        return await self._wait_for_position(
            timeout_s,
            predicate=lambda msg: bool(msg.connected)
            and bool(msg.position_valid)
            and horizontal_distance_m(
                float(msg.latitude_deg),
                float(msg.longitude_deg),
                target.latitude_deg,
                target.longitude_deg,
            )
            <= tolerance_m
            and abs(float(msg.absolute_altitude_m) - target.absolute_altitude_m) <= tolerance_m,
            timeout_message="timed out while waiting for waypoint arrival",
        )

    async def land(self, timeout_s: float) -> None:
        await self._publish_and_wait_ack("land", timeout_s)

    async def wait_until_landed(self, timeout_s: float) -> PositionSample:
        return await self._wait_for_position(
            timeout_s,
            predicate=lambda msg: bool(msg.connected)
            and bool(msg.position_valid)
            and bool(msg.landed)
            and abs(float(msg.relative_altitude_m)) <= 0.3,
            timeout_message="timed out while waiting for landed state",
        )

    async def _publish_and_wait_ack(self, command_name: str, timeout_s: float, **payload: float) -> None:
        deadline = time.monotonic() + timeout_s
        attempt = 0
        last_error = f"{command_name} timed out while waiting for PX4 acknowledgement"

        while attempt < self._max_command_retries and time.monotonic() < deadline:
            attempt += 1
            start_serial, _ = self._get_command_status()
            self._last_command_name = command_name
            self._publish_command(command_name, **payload)

            attempt_deadline = min(deadline, time.monotonic() + self._command_retry_interval_s)
            while time.monotonic() < attempt_deadline:
                state = self._get_vehicle_state()
                if state is not None and bool(getattr(state, "failsafe", False)):
                    raise MissionCommandFailed(f"{command_name} interrupted by PX4 failsafe")

                serial, status = self._get_command_status()
                if status is not None and serial > start_serial:
                    if str(getattr(status, "command", "")).strip().lower() != command_name:
                        await asyncio.sleep(0.1)
                        continue
                    if bool(getattr(status, "accepted", False)):
                        return
                    result_label = str(getattr(status, "result_label", "UNKNOWN"))
                    if result_label == "TEMPORARILY_REJECTED":
                        last_error = f"{command_name} temporarily rejected by PX4"
                        await asyncio.sleep(self._command_retry_interval_s)
                        break
                    raise MissionCommandFailed(f"{command_name} rejected by PX4: {result_label}")

                await asyncio.sleep(0.05)

        raise MissionTimeout(last_error)

    async def _wait_for_vehicle_state(
        self,
        timeout_s: float,
        *,
        predicate: Callable[[Any], bool],
        timeout_message: str,
    ) -> Any:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            state = self._get_vehicle_state()
            if state is not None:
                if bool(getattr(state, "failsafe", False)):
                    raise MissionCommandFailed("vehicle entered failsafe during mission")
                if predicate(state):
                    return state
            await asyncio.sleep(0.1)
        raise MissionTimeout(timeout_message)

    async def _wait_for_position(
        self,
        timeout_s: float,
        *,
        predicate: Callable[[Any], bool],
        timeout_message: str,
    ) -> PositionSample:
        state = await self._wait_for_vehicle_state(
            timeout_s,
            predicate=predicate,
            timeout_message=timeout_message,
        )
        return PositionSample(
            latitude_deg=float(state.latitude_deg),
            longitude_deg=float(state.longitude_deg),
            absolute_altitude_m=float(state.absolute_altitude_m),
            relative_altitude_m=float(state.relative_altitude_m),
        )


def create_gateway(name: str, **kwargs: Any) -> MissionGateway:
    from .fake_gateway import FakeMissionGateway

    if name in {"ros2", "ros2_domain"}:
        return Ros2MissionGateway(**kwargs)
    if name == "mavsdk":
        return MavsdkMissionGateway()
    if name == "fake-success":
        return FakeMissionGateway()
    if name.startswith("fake-"):
        return FakeMissionGateway(failure_mode=name.removeprefix("fake-"))
    raise ValueError(f"unsupported mission backend: {name}")
