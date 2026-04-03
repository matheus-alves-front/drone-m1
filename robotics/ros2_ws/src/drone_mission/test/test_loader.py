import os
from pathlib import Path
import tempfile
import unittest

from drone_mission.loader import MissionValidationError, load_mission_contract


def resolve_patrol_basic_contract() -> Path:
    seed_paths = [Path.cwd(), Path(__file__).resolve()]
    explicit_root = os.environ.get("DRONE_SIM_REPO_ROOT")
    if explicit_root:
        seed_paths.append(Path(explicit_root))
    seed_paths.append(Path("/workspace"))

    visited: set[Path] = set()
    for seed in seed_paths:
        for parent in (seed, *seed.parents):
            if parent in visited:
                continue
            visited.add(parent)
            candidate = parent / "simulation" / "scenarios" / "patrol_basic.json"
            if candidate.is_file():
                return candidate
    raise FileNotFoundError("could not locate simulation/scenarios/patrol_basic.json from test path")


class TestMissionLoader(unittest.TestCase):
    def test_load_patrol_basic_contract(self) -> None:
        contract = load_mission_contract(resolve_patrol_basic_contract())

        self.assertEqual(contract.name, "patrol_basic")
        self.assertEqual(contract.connection.system_address, "udp://:14540")
        self.assertEqual(
            len(contract.patrol.waypoint_offsets_north_m),
            len(contract.patrol.waypoint_offsets_east_m),
        )
        self.assertGreater(contract.flight.takeoff_altitude_m, 0.0)

    def test_reject_invalid_patrol_contract(self) -> None:
        with tempfile.TemporaryDirectory(prefix="drone-loader-test-") as tmp_root:
            broken = Path(tmp_root) / "broken.json"
            with self.assertRaises(MissionValidationError):
                broken.write_text(
                    '{"name":"broken","objective":"","flight":{"takeoff_altitude_m":3.0,"hover_duration_s":1.0,"arrival_tolerance_m":2.0,"takeoff_timeout_s":20.0,"waypoint_timeout_s":20.0,"land_timeout_s":20.0},"patrol":{"waypoint_offsets_north_m":[0.0],"waypoint_offsets_east_m":[]}}',
                    encoding="utf-8",
                )
                load_mission_contract(broken)


if __name__ == "__main__":
    unittest.main()
