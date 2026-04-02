from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


class Phase0StructureTest(unittest.TestCase):
    def test_required_paths_exist(self) -> None:
        required_paths = [
            ROOT / "docs/PROJECT-EXECUTION-CHECKLIST.md",
            ROOT / "docs/PHASE-0-OPEN-DECISIONS.md",
            ROOT / "robotics/ros2_ws/scripts/validate-workspace.sh",
            ROOT / "simulation/scenarios/README.md",
            ROOT / "services/telemetry-api/README.md",
            ROOT / "apps/dashboard/README.md",
            ROOT / "packages/shared-py/README.md",
            ROOT / "packages/shared-ts/README.md",
            ROOT / "third_party/README.md",
        ]

        missing = [str(path.relative_to(ROOT)) for path in required_paths if not path.exists()]
        self.assertEqual(missing, [], f"Missing required bootstrap artifacts: {missing}")

    def test_bootstrap_validator_passes(self) -> None:
        result = subprocess.run(
            ["bash", "scripts/bootstrap/validate-phase-0.sh"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)


if __name__ == "__main__":
    unittest.main()
