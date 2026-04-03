import json
import os
import subprocess
import sys
from pathlib import Path


def test_cli_fake_backend_json_output() -> None:
    root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{root / 'src'}{os.pathsep}{env['PYTHONPATH']}" if env.get("PYTHONPATH") else str(root / "src")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "drone_scenarios",
            "takeoff_land",
            "--backend",
            "fake-success",
            "--scenario-file",
            "simulation/scenarios/takeoff_land.json",
            "--output",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=root.parent,
        env=env,
    )

    payload = json.loads(result.stdout)
    assert payload["status"] == "completed"
    assert payload["scenario_name"] == "takeoff_land"
    assert [item["name"] for item in payload["assertions"]] == [
        "connection_ready",
        "arm",
        "takeoff",
        "hover",
        "waypoint",
        "land",
    ]
