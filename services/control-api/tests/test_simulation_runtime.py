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


def test_shell_runtime_inspection_recovers_px4_pid_from_process_scan(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    adapter = ShellSimulationRuntimeAdapter(
        repo_root,
        runtime_root=tmp_path / "runtime",
        log_root=tmp_path / "logs",
    )

    paths = adapter.paths_for("session_recover_px4")
    paths.runtime_dir.mkdir(parents=True, exist_ok=True)
    paths.log_dir.mkdir(parents=True, exist_ok=True)
    paths.xrce_pid_file.write_text("4321\n", encoding="utf-8")

    adapter._find_process_pid = lambda command_fragment: 1234 if "px4_sitl_default/bin/px4" in command_fragment else 4321  # type: ignore[method-assign]
    adapter._pid_exists = lambda pid: pid in {1234, 4321}  # type: ignore[method-assign]

    inspection = adapter.inspect(
        "session_recover_px4",
        SessionMode.HEADLESS,
        SimulationSessionStatus.STARTING,
    )

    assert inspection.status == SimulationSessionStatus.ACTIVE
    assert inspection.runtime_ready is True
    assert paths.px4_pid_file.read_text(encoding="utf-8").strip() == "1234"


def test_shell_runtime_inspection_reports_degraded_when_only_xrce_can_be_found(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    adapter = ShellSimulationRuntimeAdapter(
        repo_root,
        runtime_root=tmp_path / "runtime",
        log_root=tmp_path / "logs",
    )

    paths = adapter.paths_for("session_xrce_only")
    paths.runtime_dir.mkdir(parents=True, exist_ok=True)
    paths.log_dir.mkdir(parents=True, exist_ok=True)

    adapter._find_process_pid = lambda command_fragment: 4321 if command_fragment == "MicroXRCEAgent" else None  # type: ignore[method-assign]
    adapter._pid_exists = lambda pid: pid == 4321  # type: ignore[method-assign]

    inspection = adapter.inspect(
        "session_xrce_only",
        SessionMode.HEADLESS,
        SimulationSessionStatus.STARTING,
    )

    assert inspection.status == SimulationSessionStatus.DEGRADED
    assert inspection.runtime_ready is False
    assert paths.xrce_pid_file.read_text(encoding="utf-8").strip() == "4321"
