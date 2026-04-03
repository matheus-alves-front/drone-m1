from __future__ import annotations

import asyncio
from dataclasses import replace

from .contracts import ScenarioAssertion, ScenarioContract, ScenarioResult, ScenarioStatus
from .errors import ConnectionFailure, ScenarioAssertionFailed, ScenarioCommandFailed, ScenarioTimeout
from .geodesy import horizontal_distance_m, offset_position
from .gateways.base import VehicleGateway


class TakeoffLandScenarioRunner:
    def __init__(self, gateway: VehicleGateway) -> None:
        self._gateway = gateway

    async def run(self, contract: ScenarioContract) -> ScenarioResult:
        assertions: list[ScenarioAssertion] = []
        result = ScenarioResult(
            scenario_name=contract.name,
            scenario_path=contract.scenario_path,
            status=ScenarioStatus.FAILED,
            system_address=contract.connection.system_address,
            assertions=assertions,
        )

        try:
            await self._gateway.connect(
                system_address=contract.connection.system_address,
                timeout_s=contract.connection.connection_timeout_s,
            )

            ready_position = await self._gateway.wait_until_ready_position(contract.connection.ready_timeout_s)
            assertions.append(
                ScenarioAssertion(
                    name="connection_ready",
                    success=True,
                    detail=f"vehicle discovered at {ready_position.latitude_deg:.6f},{ready_position.longitude_deg:.6f}",
                )
            )

            await self._gateway.arm(contract.connection.action_timeout_s)
            await self._gateway.wait_until_armed(contract.connection.action_timeout_s)
            assertions.append(ScenarioAssertion(name="arm", success=True, detail="vehicle armed successfully"))

            await self._gateway.set_takeoff_altitude(
                contract.flight.takeoff_altitude_m,
                contract.connection.action_timeout_s,
            )
            await self._gateway.takeoff(contract.connection.action_timeout_s)
            airborne = await self._gateway.wait_until_altitude(
                minimum_relative_altitude_m=contract.flight.takeoff_altitude_m - contract.flight.altitude_tolerance_m,
                timeout_s=contract.flight.takeoff_timeout_s,
            )
            assertions.append(
                ScenarioAssertion(
                    name="takeoff",
                    success=True,
                    detail=f"relative altitude reached {airborne.relative_altitude_m:.2f} m",
                )
            )

            await asyncio.sleep(contract.flight.hover_duration_s)
            hover_position = await self._gateway.current_position(contract.connection.action_timeout_s)
            if hover_position.relative_altitude_m < contract.flight.takeoff_altitude_m - contract.flight.altitude_tolerance_m:
                raise ScenarioAssertionFailed("hover altitude dropped below the expected threshold")

            assertions.append(
                ScenarioAssertion(
                    name="hover",
                    success=True,
                    detail=(
                        f"hover maintained at {hover_position.relative_altitude_m:.2f} m "
                        f"for {contract.flight.hover_duration_s:.1f} s"
                    ),
                )
            )

            target_position = offset_position(
                hover_position,
                north_m=contract.flight.waypoint_offset_north_m,
                east_m=contract.flight.waypoint_offset_east_m,
            )
            target_position = replace(
                target_position,
                absolute_altitude_m=hover_position.absolute_altitude_m,
                relative_altitude_m=hover_position.relative_altitude_m,
            )

            await self._gateway.goto_location(
                latitude_deg=target_position.latitude_deg,
                longitude_deg=target_position.longitude_deg,
                absolute_altitude_m=target_position.absolute_altitude_m,
                yaw_deg=0.0,
                timeout_s=contract.connection.action_timeout_s,
            )
            at_waypoint = await self._gateway.wait_until_near(
                target=target_position,
                tolerance_m=contract.flight.arrival_tolerance_m,
                timeout_s=contract.flight.waypoint_timeout_s,
            )
            assertions.append(
                ScenarioAssertion(
                    name="waypoint",
                    success=True,
                    detail=f"waypoint reached within {horizontal_distance_m(at_waypoint, target_position):.2f} m of target",
                )
            )
            result.target_position = target_position

            await self._gateway.land(contract.connection.action_timeout_s)
            landed = await self._gateway.wait_until_landed(contract.flight.land_timeout_s)
            assertions.append(ScenarioAssertion(name="land", success=True, detail="vehicle landed and left in-air state"))

            result.status = ScenarioStatus.COMPLETED
            result.final_position = landed
            result.detail = "scenario completed successfully"
            return result

        except ConnectionFailure as exc:
            assertions.append(ScenarioAssertion(name="connection_ready", success=False, detail=str(exc)))
            result.status = ScenarioStatus.CONNECTION_FAILED
            result.detail = str(exc)
            return result
        except ScenarioTimeout as exc:
            assertions.append(ScenarioAssertion(name="timeout", success=False, detail=str(exc)))
            result.status = ScenarioStatus.TIMEOUT
            result.detail = str(exc)
            return result
        except (ScenarioAssertionFailed, ScenarioCommandFailed) as exc:
            assertions.append(ScenarioAssertion(name="scenario_assertion", success=False, detail=str(exc)))
            result.status = ScenarioStatus.ASSERTION_FAILED
            result.detail = str(exc)
            return result
        except Exception as exc:  # pragma: no cover
            assertions.append(ScenarioAssertion(name="unexpected_failure", success=False, detail=str(exc)))
            result.status = ScenarioStatus.FAILED
            result.detail = str(exc)
            return result
