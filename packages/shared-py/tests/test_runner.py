from __future__ import annotations

import asyncio

from drone_scenarios.contracts import ConnectionContract, FlightContract, ScenarioContract, ScenarioStatus
from drone_scenarios.gateways.fake import FakeVehicleGateway
from drone_scenarios.runner import TakeoffLandScenarioRunner


def build_contract() -> ScenarioContract:
    return ScenarioContract(
        name="takeoff_land",
        scenario_path="simulation/scenarios/takeoff_land.json",
        objective="test contract",
        connection=ConnectionContract(
            system_address="udp://:14540",
            connection_timeout_s=20.0,
            ready_timeout_s=20.0,
            action_timeout_s=20.0,
        ),
        flight=FlightContract(
            takeoff_altitude_m=3.0,
            hover_duration_s=0.0,
            waypoint_offset_north_m=5.0,
            waypoint_offset_east_m=0.0,
            arrival_tolerance_m=2.0,
            altitude_tolerance_m=0.8,
            takeoff_timeout_s=20.0,
            waypoint_timeout_s=20.0,
            land_timeout_s=20.0,
        ),
    )


def test_runner_completes_takeoff_land_scenario() -> None:
    runner = TakeoffLandScenarioRunner(FakeVehicleGateway())
    result = asyncio.run(runner.run(build_contract()))

    assert result.status == ScenarioStatus.COMPLETED
    assert [assertion.name for assertion in result.assertions] == [
        "connection_ready",
        "arm",
        "takeoff",
        "hover",
        "waypoint",
        "land",
    ]


def test_runner_classifies_connection_failure() -> None:
    runner = TakeoffLandScenarioRunner(FakeVehicleGateway(failure_mode="connection"))
    result = asyncio.run(runner.run(build_contract()))

    assert result.status == ScenarioStatus.CONNECTION_FAILED
    assert "could not connect" in result.detail


def test_runner_classifies_timeout() -> None:
    runner = TakeoffLandScenarioRunner(FakeVehicleGateway(failure_mode="waypoint_timeout"))
    result = asyncio.run(runner.run(build_contract()))

    assert result.status == ScenarioStatus.TIMEOUT
    assert "waypoint" in result.detail
