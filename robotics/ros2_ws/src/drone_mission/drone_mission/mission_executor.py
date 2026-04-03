from __future__ import annotations

import asyncio
from contextlib import suppress
from typing import Awaitable, Callable

from .contracts import MissionContract, PositionSample
from .errors import MissionAbortRequested, MissionConnectionFailure, MissionError
from .gateway import MissionGateway
from .geodesy import offset_position
from .mission_state_machine import MissionPhase, MissionStateMachine


class MissionExecutor:
    def __init__(
        self,
        gateway: MissionGateway,
        state_machine: MissionStateMachine,
        wait_for_visual_lock: Callable[[float], Awaitable[None]] | None = None,
        visual_lock_timeout_s: float = 20.0,
    ) -> None:
        self._gateway = gateway
        self._state_machine = state_machine
        self._wait_for_visual_lock = wait_for_visual_lock
        self._visual_lock_timeout_s = max(float(visual_lock_timeout_s), 1.0)

    async def run(
        self,
        contract: MissionContract,
        *,
        should_abort: Callable[[], bool],
    ) -> None:
        home_position: PositionSample | None = None
        cruise_position: PositionSample | None = None

        try:
            self._state_machine.transition(
                MissionPhase.WAITING_FOR_SYSTEM,
                detail="waiting for vehicle connection and home position",
            )
            await self._gateway.connect(
                system_address=contract.connection.system_address,
                timeout_s=contract.connection.connection_timeout_s,
            )
            home_position = await self._await_with_abort(
                self._gateway.wait_until_ready_position(contract.connection.ready_timeout_s),
                should_abort,
            )
            self._raise_if_abort_requested(should_abort)

            self._state_machine.transition(MissionPhase.ARMING, detail="arming vehicle")
            await self._gateway.arm(contract.connection.action_timeout_s)
            await self._await_with_abort(
                self._gateway.wait_until_armed(contract.connection.action_timeout_s),
                should_abort,
            )
            self._raise_if_abort_requested(should_abort)

            self._state_machine.transition(
                MissionPhase.TAKEOFF,
                detail=f"taking off to {contract.flight.takeoff_altitude_m:.1f} m",
            )
            await self._gateway.set_takeoff_altitude(
                contract.flight.takeoff_altitude_m,
                contract.connection.action_timeout_s,
            )
            await self._gateway.takeoff(contract.connection.action_timeout_s)
            cruise_position = await self._await_with_abort(
                self._gateway.wait_until_altitude(
                    minimum_relative_altitude_m=contract.flight.takeoff_altitude_m,
                    timeout_s=contract.flight.takeoff_timeout_s,
                ),
                should_abort,
            )
            self._raise_if_abort_requested(should_abort)

            self._state_machine.transition(
                MissionPhase.HOVER,
                detail=f"holding position for {contract.flight.hover_duration_s:.1f} s",
            )
            await self._sleep_with_abort(contract.flight.hover_duration_s, should_abort)
            cruise_position = await self._gateway.current_position(contract.connection.action_timeout_s)
            self._raise_if_abort_requested(should_abort)

            if self._wait_for_visual_lock is not None:
                self._state_machine.transition(
                    MissionPhase.HOVER,
                    detail="waiting for visual lock before patrol",
                )
                await self._await_with_abort(
                    self._wait_for_visual_lock(self._visual_lock_timeout_s),
                    should_abort,
                )
                self._raise_if_abort_requested(should_abort)

            waypoints = [
                offset_position(home_position, north_m=north_m, east_m=east_m)
                for north_m, east_m in zip(
                    contract.patrol.waypoint_offsets_north_m,
                    contract.patrol.waypoint_offsets_east_m,
                )
            ]
            waypoints = [
                PositionSample(
                    latitude_deg=waypoint.latitude_deg,
                    longitude_deg=waypoint.longitude_deg,
                    absolute_altitude_m=cruise_position.absolute_altitude_m,
                    relative_altitude_m=cruise_position.relative_altitude_m,
                )
                for waypoint in waypoints
            ]

            for index, waypoint in enumerate(waypoints, start=1):
                self._state_machine.transition(
                    MissionPhase.PATROL,
                    detail=f"flying to patrol waypoint {index}/{len(waypoints)}",
                    current_waypoint_index=index,
                )
                await self._gateway.goto_location(
                    latitude_deg=waypoint.latitude_deg,
                    longitude_deg=waypoint.longitude_deg,
                    absolute_altitude_m=waypoint.absolute_altitude_m,
                    yaw_deg=0.0,
                    timeout_s=contract.connection.action_timeout_s,
                )
                cruise_position = await self._await_with_abort(
                    self._gateway.wait_until_near(
                        target=waypoint,
                        tolerance_m=contract.flight.arrival_tolerance_m,
                        timeout_s=contract.flight.waypoint_timeout_s,
                    ),
                    should_abort,
                )
                self._raise_if_abort_requested(should_abort)

            if contract.patrol.return_to_home:
                self._state_machine.transition(
                    MissionPhase.RETURN_TO_HOME,
                    detail="returning to launch position",
                    current_waypoint_index=len(waypoints),
                )
                home_target = PositionSample(
                    latitude_deg=home_position.latitude_deg,
                    longitude_deg=home_position.longitude_deg,
                    absolute_altitude_m=cruise_position.absolute_altitude_m,
                    relative_altitude_m=cruise_position.relative_altitude_m,
                )
                await self._gateway.goto_location(
                    latitude_deg=home_target.latitude_deg,
                    longitude_deg=home_target.longitude_deg,
                    absolute_altitude_m=home_target.absolute_altitude_m,
                    yaw_deg=0.0,
                    timeout_s=contract.connection.action_timeout_s,
                )
                await self._await_with_abort(
                    self._gateway.wait_until_near(
                        target=home_target,
                        tolerance_m=contract.flight.arrival_tolerance_m,
                        timeout_s=contract.flight.waypoint_timeout_s,
                    ),
                    should_abort,
                )
                self._raise_if_abort_requested(should_abort)

            self._state_machine.transition(
                MissionPhase.LANDING,
                detail="landing at mission endpoint",
                current_waypoint_index=len(waypoints),
            )
            await self._gateway.land(contract.connection.action_timeout_s)
            await self._await_with_abort(
                self._gateway.wait_until_landed(contract.flight.land_timeout_s),
                should_abort,
            )
            self._state_machine.transition(
                MissionPhase.COMPLETED,
                detail="mission completed successfully",
                current_waypoint_index=len(waypoints),
            )
        except MissionAbortRequested:
            await self._run_abort_sequence(
                contract=contract,
                home_position=home_position,
                fallback_position=cruise_position,
                detail="mission abort requested",
            )
        except MissionConnectionFailure as exc:
            self._state_machine.transition(MissionPhase.FAILED, detail=str(exc))
            raise
        except MissionError as exc:
            await self._run_abort_sequence(
                contract=contract,
                home_position=home_position,
                fallback_position=cruise_position,
                detail=str(exc),
            )
            raise

    async def _run_abort_sequence(
        self,
        *,
        contract: MissionContract,
        home_position: PositionSample | None,
        fallback_position: PositionSample | None,
        detail: str,
    ) -> None:
        self._state_machine.transition(MissionPhase.ABORTING, detail=detail)

        try:
            if home_position is not None and fallback_position is not None:
                home_target = PositionSample(
                    latitude_deg=home_position.latitude_deg,
                    longitude_deg=home_position.longitude_deg,
                    absolute_altitude_m=fallback_position.absolute_altitude_m,
                    relative_altitude_m=fallback_position.relative_altitude_m,
                )
                await self._gateway.goto_location(
                    latitude_deg=home_target.latitude_deg,
                    longitude_deg=home_target.longitude_deg,
                    absolute_altitude_m=home_target.absolute_altitude_m,
                    yaw_deg=0.0,
                    timeout_s=contract.connection.action_timeout_s,
                )
                await self._gateway.wait_until_near(
                    target=home_target,
                    tolerance_m=contract.flight.arrival_tolerance_m,
                    timeout_s=contract.flight.waypoint_timeout_s,
                )

            await self._gateway.land(contract.connection.action_timeout_s)
            await self._await_with_abort(
                self._gateway.wait_until_landed(contract.flight.abort_land_timeout_s),
                lambda: False,
            )
            self._state_machine.transition(MissionPhase.ABORTED, detail=f"mission aborted: {detail}")
        except MissionError as exc:
            self._state_machine.transition(MissionPhase.FAILED, detail=f"abort sequence failed: {exc}")
            raise

    @staticmethod
    async def _sleep_with_abort(duration_s: float, should_abort: Callable[[], bool]) -> None:
        deadline = asyncio.get_running_loop().time() + duration_s
        while asyncio.get_running_loop().time() < deadline:
            if should_abort():
                raise MissionAbortRequested("mission abort requested")
            await asyncio.sleep(0.1)

    @staticmethod
    def _raise_if_abort_requested(should_abort: Callable[[], bool]) -> None:
        if should_abort():
            raise MissionAbortRequested("mission abort requested")

    @staticmethod
    async def _await_with_abort(awaitable, should_abort: Callable[[], bool]):
        task = asyncio.create_task(awaitable)
        try:
            while True:
                if should_abort():
                    raise MissionAbortRequested("mission abort requested")
                done, _pending = await asyncio.wait({task}, timeout=0.1)
                if task in done:
                    return task.result()
        except MissionAbortRequested:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
            raise
