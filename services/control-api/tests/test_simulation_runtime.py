from __future__ import annotations

from pathlib import Path

from control_plane.domain import SessionMode, SimulationSessionStatus
from control_api.simulation_runtime import ShellSimulationRuntimeAdapter


def test_shell_runtime_adapter_respects_phase1_check_contract(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    adapter = ShellSimulationRuntimeAdapter(
        repo_root,
        runtime_root=tmp_path / "runtime",
        log_root=tmp_path / "logs",
        preflight_timeout_s=30.0,
    )

    adapter.check("session_check_only", SessionMode.HEADLESS)


def test_shell_runtime_inspection_reports_idle_when_no_runtime_artifacts_exist(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    adapter = ShellSimulationRuntimeAdapter(
        repo_root,
        runtime_root=tmp_path / "runtime",
        log_root=tmp_path / "logs",
    )

    inspection = adapter.inspect("session_idle", SessionMode.HEADLESS, SimulationSessionStatus.IDLE)

    assert inspection.status == SimulationSessionStatus.IDLE
    assert inspection.runtime_ready is False
