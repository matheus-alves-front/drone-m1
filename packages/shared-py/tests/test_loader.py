from pathlib import Path

import pytest

from drone_scenarios.errors import ScenarioValidationError
from drone_scenarios.loader import load_scenario_contract


def test_load_takeoff_land_contract() -> None:
    contract = load_scenario_contract(Path("simulation/scenarios/takeoff_land.json"))

    assert contract.name == "takeoff_land"
    assert contract.connection.system_address == "udp://:14540"
    assert contract.flight.takeoff_altitude_m > 0


def test_reject_invalid_contract(tmp_path: Path) -> None:
    broken = tmp_path / "broken.json"
    broken.write_text('{"name":"broken","objective":"","flight":{}}', encoding="utf-8")

    with pytest.raises(ScenarioValidationError):
        load_scenario_contract(broken)
