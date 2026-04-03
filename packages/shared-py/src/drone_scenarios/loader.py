from __future__ import annotations

import json
from pathlib import Path

from .contracts import ConnectionContract, FlightContract, ScenarioContract
from .errors import ScenarioValidationError


def load_scenario_contract(path: str | Path) -> ScenarioContract:
    scenario_path = Path(path)
    try:
        payload = json.loads(scenario_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ScenarioValidationError(f"scenario contract not found: {scenario_path}") from exc
    except json.JSONDecodeError as exc:
        raise ScenarioValidationError(f"invalid JSON in scenario contract: {scenario_path}") from exc

    required_fields = ("name", "objective", "flight")
    missing_fields = [field for field in required_fields if field not in payload]
    if missing_fields:
        missing = ", ".join(missing_fields)
        raise ScenarioValidationError(f"scenario contract missing required fields: {missing}")

    try:
        connection = ConnectionContract(**payload.get("connection", {}))
        flight = FlightContract(**payload["flight"])
    except TypeError as exc:
        raise ScenarioValidationError(f"invalid scenario contract payload: {exc}") from exc

    return ScenarioContract(
        name=payload["name"],
        scenario_path=str(scenario_path),
        objective=payload["objective"],
        connection=connection,
        flight=flight,
    )
