from control_plane.domain import (
    INITIAL_ACTION_CATALOG,
    INITIAL_CAPABILITY_CATALOG,
    ActionAvailabilityScope,
    ActionCategory,
    ActionExecutionStatus,
    ActionRequest,
    ActionResult,
    ArtifactRef,
    CapabilityStatus,
    ControlPlaneError,
    ControlPlaneErrorCode,
    RequestedBy,
    SafetyLevel,
)


def test_action_request_serialization_matches_mark1_contract() -> None:
    request = ActionRequest(
        action_name="mission.start",
        target="default",
        request_id="req_123",
        session_id="sess_123",
        input={"mission_name": "patrol_basic"},
        requested_by=RequestedBy(type="operator_ui", id="local-user"),
    )

    assert request.to_dict() == {
        "action_name": "mission.start",
        "target": "default",
        "request_id": "req_123",
        "session_id": "sess_123",
        "input": {"mission_name": "patrol_basic"},
        "requested_by": {"type": "operator_ui", "id": "local-user"},
    }


def test_action_result_serialization_matches_mark1_contract() -> None:
    result = ActionResult(
        request_id="req_123",
        accepted=True,
        status=ActionExecutionStatus.RUNNING,
        message="Mission start requested",
        run_id="run_456",
        artifacts=(ArtifactRef(artifact_type="log", uri="runs/run_456/events.jsonl"),),
        errors=(
            ControlPlaneError(
                code=ControlPlaneErrorCode.RUNTIME_FAILURE,
                message="warning only",
                detail="runtime accepted but reported degraded state",
            ),
        ),
    )

    assert result.to_dict() == {
        "request_id": "req_123",
        "accepted": True,
        "status": "running",
        "message": "Mission start requested",
        "run_id": "run_456",
        "artifacts": [
            {
                "artifact_type": "log",
                "uri": "runs/run_456/events.jsonl",
                "description": "",
            }
        ],
        "errors": [
            {
                "code": "runtime_failure",
                "message": "warning only",
                "detail": "runtime accepted but reported degraded state",
            }
        ],
    }


def test_initial_action_catalog_covers_mark1_required_actions() -> None:
    action_names = {definition.action_name for definition in INITIAL_ACTION_CATALOG}
    expected = {
        "simulation.start",
        "simulation.stop",
        "simulation.restart",
        "simulation.status.get",
        "capabilities.list",
        "scenario.list",
        "scenario.run",
        "scenario.cancel",
        "scenario.status.get",
        "mission.start",
        "mission.abort",
        "mission.reset",
        "mission.status.get",
        "vehicle.arm",
        "vehicle.disarm",
        "vehicle.takeoff",
        "vehicle.land",
        "vehicle.return_to_home",
        "vehicle.goto",
        "safety.inject_fault",
        "safety.clear_fault",
        "safety.status.get",
        "perception.status.get",
        "perception.stream.status.get",
        "telemetry.snapshot.get",
        "telemetry.metrics.get",
        "telemetry.events.get",
        "telemetry.runs.list",
        "telemetry.replay.get",
    }

    assert expected == action_names
    assert {definition.category for definition in INITIAL_ACTION_CATALOG} == {
        ActionCategory.SIMULATION,
        ActionCategory.DISCOVERY,
        ActionCategory.SCENARIO,
        ActionCategory.MISSION,
        ActionCategory.VEHICLE,
        ActionCategory.SAFETY,
        ActionCategory.PERCEPTION,
        ActionCategory.TELEMETRY,
    }


def test_action_availability_is_discriminated_by_domain_scope() -> None:
    by_name = {definition.action_name: definition for definition in INITIAL_ACTION_CATALOG}

    assert by_name["mission.start"].to_dict()["availability"] == [
        {"scope": "simulation_session", "allowed_statuses": ["active", "degraded"]},
        {"scope": "mission", "allowed_statuses": ["idle"]},
    ]
    assert by_name["mission.abort"].availability[0].scope == ActionAvailabilityScope.MISSION
    assert by_name["scenario.cancel"].availability[0].allowed_statuses == ("starting", "running")


def test_initial_capability_catalog_is_mark2_ready_without_executor_leakage() -> None:
    capability_names = {definition.capability_name for definition in INITIAL_CAPABILITY_CATALOG}

    assert capability_names == {
        "simulation.lifecycle",
        "scenario.takeoff_land.run",
        "scenario.patrol_basic.run",
        "mission.control",
        "vehicle.basic_control",
        "safety.fault_injection",
        "telemetry.read_model",
        "replay.read",
        "perception.observe",
    }

    patrol = next(
        definition
        for definition in INITIAL_CAPABILITY_CATALOG
        if definition.capability_name == "scenario.patrol_basic.run"
    )
    vehicle_control = next(
        definition
        for definition in INITIAL_CAPABILITY_CATALOG
        if definition.capability_name == "vehicle.basic_control"
    )
    replay = next(
        definition
        for definition in INITIAL_CAPABILITY_CATALOG
        if definition.capability_name == "replay.read"
    )

    assert patrol.action_names == ("scenario.run", "scenario.cancel", "scenario.status.get")
    assert vehicle_control.safety_level == SafetyLevel.CRITICAL
    assert vehicle_control.required_vehicle_type == "aerial_multirotor"
    assert replay.status == CapabilityStatus.AVAILABLE
    assert replay.to_dict()["required_environment"] == ["simulation"]


def test_action_execution_statuses_cover_terminal_cancellation_and_timeout() -> None:
    assert ActionExecutionStatus.CANCELLED.value == "cancelled"
    assert ActionExecutionStatus.TIMED_OUT.value == "timed_out"
