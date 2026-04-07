from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from control_plane.domain import ScenarioExecutorType


_EXECUTOR_BY_NAME = {
    "takeoff_land": ScenarioExecutorType.MAVSDK.value,
    "patrol_basic": ScenarioExecutorType.ROS2_MISSION.value,
    "geofence_breach": ScenarioExecutorType.ROS2_SAFETY.value,
    "failsafe_gps_loss": ScenarioExecutorType.ROS2_SAFETY.value,
    "failsafe_rc_loss": ScenarioExecutorType.ROS2_SAFETY.value,
    "perception_target_tracking": ScenarioExecutorType.ROS2_PERCEPTION.value,
}

_KIND_BY_NAME = {
    "takeoff_land": "flight",
    "patrol_basic": "mission",
    "geofence_breach": "safety",
    "failsafe_gps_loss": "safety",
    "failsafe_rc_loss": "safety",
    "perception_target_tracking": "perception",
}

_CONTROL_PLANE_STATUS_BY_NAME = {
    "takeoff_land": "available",
    "patrol_basic": "available",
    "geofence_breach": "experimental",
    "failsafe_gps_loss": "experimental",
    "failsafe_rc_loss": "experimental",
    "perception_target_tracking": "experimental",
}

_PHASE_HINT_BY_NAME = {
    "takeoff_land": "available through the unified scenario surface in R4",
    "patrol_basic": "available through the mission control surface in R5",
    "geofence_breach": "formalized in R4, but its safety-backed executor lands in R6",
    "failsafe_gps_loss": "formalized in R4, but its safety-backed executor lands in R6",
    "failsafe_rc_loss": "formalized in R4, but its safety-backed executor lands in R6",
    "perception_target_tracking": "formalized in R4, but its perception-backed executor lands in R10",
}


def load_scenario_registry(scenarios_root: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in sorted(scenarios_root.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        scenario_name = str(payload["name"])
        entries.append(
            {
                "scenario_name": scenario_name,
                "scenario_kind": _KIND_BY_NAME.get(scenario_name, "scenario"),
                "executor_type": _EXECUTOR_BY_NAME.get(scenario_name, ScenarioExecutorType.SHELL.value),
                "input_contract": str(path.relative_to(scenarios_root.parents[1])),
                "output_contract": "ActionResult",
                "supports_visual": True,
                "supports_headless": True,
                "objective": payload.get("objective", ""),
                "control_plane_status": _CONTROL_PLANE_STATUS_BY_NAME.get(scenario_name, "experimental"),
                "phase_hint": _PHASE_HINT_BY_NAME.get(scenario_name, "future Mark 1 phase"),
            }
        )
    return entries


def public_scenario_definition(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "scenario_name": entry["scenario_name"],
        "scenario_kind": entry["scenario_kind"],
        "input_contract": entry["input_contract"],
        "output_contract": entry["output_contract"],
        "supports_visual": entry["supports_visual"],
        "supports_headless": entry["supports_headless"],
        "objective": entry.get("objective", ""),
        "control_plane_status": entry.get("control_plane_status", "experimental"),
        "phase_hint": entry.get("phase_hint", ""),
    }
