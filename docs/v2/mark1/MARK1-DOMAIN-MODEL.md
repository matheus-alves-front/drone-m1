# Mark 1 Domain Model

## Core entities

### Vehicle
Representa o veículo controlado.
Campos:
- `vehicle_id`
- `vehicle_type`
- `armed`
- `flight_mode`
- `position`
- `altitude`
- `connected`
- `health_summary`

### SimulationSession
Campos:
- `session_id`
- `status`
- `mode`
- `environment`
- `components`
- `started_at`
- `stopped_at`

### Run
Campos:
- `run_id`
- `run_kind`
- `name`
- `status`
- `session_id`
- `started_at`
- `ended_at`
- `artifacts`
- `summary`

### Mission
Campos:
- `mission_id`
- `mission_type`
- `status`
- `plan_ref`
- `constraints`
- `fallback_policy`
- `required_capabilities`

### Scenario
Campos:
- `scenario_name`
- `scenario_kind`
- `executor_type`
- `input_contract`
- `output_contract`
- `supports_visual`
- `supports_headless`

### SafetyFault
Campos:
- `fault_type`
- `active`
- `value`
- `detail`
- `source`
- `raised_at`
- `cleared_at`

### Action
Campos:
- `action_name`
- `category`
- `input_schema`
- `result_schema`
- `target`
- `sync_mode`
- `availability`

### ActionAvailability
Campos:
- `scope`
- `allowed_statuses`

### Capability
Campos:
- `capability_name`
- `version`
- `description`
- `action_names`
- `required_runtime_components`
- `constraints`

## Enumerations

### SimulationSessionStatus
- `idle`
- `starting`
- `active`
- `degraded`
- `stopping`
- `stopped`
- `failed`

### RunStatus
- `queued`
- `starting`
- `running`
- `completed`
- `failed`
- `cancelled`
- `timed_out`

### MissionStatus
- `idle`
- `arming`
- `takeoff`
- `hover`
- `patrol`
- `returning`
- `landing`
- `completed`
- `aborted`
- `failed`

### ActionCategory
- `simulation`
- `scenario`
- `mission`
- `vehicle`
- `safety`
- `perception`
- `telemetry`
- `discovery`

### ActionAvailabilityScope
- `none`
- `simulation_session`
- `run`
- `mission`

## Domain Rule
Toda mudança operacional relevante deve ser representável como:
- action
- run
- resulting state/event
