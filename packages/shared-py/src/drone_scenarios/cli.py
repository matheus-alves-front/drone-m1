from __future__ import annotations

import argparse
import asyncio
import json
import logging
from pathlib import Path

from .contracts import ConnectionContract, ScenarioStatus
from .gateways import create_gateway
from .loader import load_scenario_contract
from .runner import TakeoffLandScenarioRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run MAVSDK-backed simulation scenarios. The CLI currently materializes only takeoff_land.",
    )
    parser.add_argument("scenario", choices=["takeoff_land"], help="MAVSDK scenario name to execute.")
    parser.add_argument(
        "--scenario-file",
        default="simulation/scenarios/takeoff_land.json",
        help="Path to the machine-readable takeoff_land contract.",
    )
    parser.add_argument(
        "--system-address",
        default=None,
        help="Override the MAVSDK system address declared in the scenario contract.",
    )
    parser.add_argument(
        "--backend",
        default="mavsdk",
        choices=["mavsdk", "fake-success"],
        help="Execution backend.",
    )
    parser.add_argument(
        "--output",
        default="text",
        choices=["text", "json"],
        help="Output format for the final scenario result.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity.",
    )
    return parser


async def _run(args: argparse.Namespace):
    contract = load_scenario_contract(Path(args.scenario_file))
    if args.system_address:
        contract = contract.__class__(
            name=contract.name,
            scenario_path=contract.scenario_path,
            objective=contract.objective,
            connection=ConnectionContract(
                system_address=args.system_address,
                connection_timeout_s=contract.connection.connection_timeout_s,
                ready_timeout_s=contract.connection.ready_timeout_s,
                action_timeout_s=contract.connection.action_timeout_s,
            ),
            flight=contract.flight,
        )

    gateway = create_gateway(args.backend)
    runner = TakeoffLandScenarioRunner(gateway)
    return await runner.run(contract)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    result = asyncio.run(_run(args))

    if args.output == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"scenario: {result.scenario_name}")
        print(f"status: {result.status.value}")
        print(f"detail: {result.detail}")
        for assertion in result.assertions:
            marker = "ok" if assertion.success else "fail"
            print(f"- [{marker}] {assertion.name}: {assertion.detail}")

    if result.status == ScenarioStatus.COMPLETED:
        return 0
    if result.status == ScenarioStatus.CONNECTION_FAILED:
        return 2
    if result.status == ScenarioStatus.TIMEOUT:
        return 3
    if result.status == ScenarioStatus.ASSERTION_FAILED:
        return 4
    return 5
