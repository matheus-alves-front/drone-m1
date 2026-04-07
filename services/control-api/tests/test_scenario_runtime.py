from __future__ import annotations

from pathlib import Path
import time

from control_plane.domain import ControlPlaneErrorCode, RunStatus
from control_api.scenario_runtime import ScenarioRuntimeError, ShellScenarioRuntimeAdapter


def test_shell_scenario_runtime_runs_takeoff_land_with_fake_backend(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    adapter = ShellScenarioRuntimeAdapter(
        repo_root,
        state_root=tmp_path / "scenario-runtime",
    )

    launch = adapter.start(
        scenario_name="takeoff_land",
        run_id="run_takeoff_land_fake",
        scenario_contract_path=str(repo_root / "simulation" / "scenarios" / "takeoff_land.json"),
        parameters={"backend": "fake-success"},
    )

    deadline = time.time() + 8.0
    inspection = adapter.inspect(scenario_name="takeoff_land", run_id="run_takeoff_land_fake")
    while inspection.status == RunStatus.RUNNING and time.time() < deadline:
        time.sleep(0.05)
        inspection = adapter.inspect(scenario_name="takeoff_land", run_id="run_takeoff_land_fake")

    assert launch.process_id is not None
    assert inspection.status == RunStatus.COMPLETED
    assert inspection.result_payload is not None
    assert inspection.result_payload["scenario_name"] == "takeoff_land"


def test_shell_scenario_runtime_rejects_patrol_basic_in_r4(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    adapter = ShellScenarioRuntimeAdapter(
        repo_root,
        state_root=tmp_path / "scenario-runtime",
    )

    try:
        adapter.start(
            scenario_name="patrol_basic",
            run_id="run_patrol_basic_fake",
            scenario_contract_path=str(repo_root / "simulation" / "scenarios" / "patrol_basic.json"),
            parameters={},
        )
    except ScenarioRuntimeError as exc:
        assert exc.code == ControlPlaneErrorCode.NOT_SUPPORTED
    else:
        raise AssertionError("expected patrol_basic to stay unsupported in the R4 shell scenario runtime")
