# Mark 1 Action and Capability Contracts

## Objetivo
Dar uma semântica única ao que hoje está espalhado entre shell, MAVSDK, ROS 2 e validators.

## Action Contract

### Shape
```json
{
  "action_name": "mission.start",
  "target": "default",
  "request_id": "req_123",
  "session_id": "sess_123",
  "input": {
    "mission_name": "patrol_basic"
  },
  "requested_by": {
    "type": "operator_ui",
    "id": "local-user"
  }
}
```

## Action Result Contract

```json
{
  "request_id": "req_123",
  "accepted": true,
  "status": "running",
  "message": "Mission start requested",
  "run_id": "run_456",
  "artifacts": [],
  "errors": []
}
```

## Capability Contract

```json
{
  "capability_name": "scenario.takeoff_land.run",
  "version": "1.0.0",
  "description": "Runs the takeoff_land scenario using the current runtime",
  "action_names": ["scenario.run", "scenario.cancel", "scenario.status.get"],
  "required_runtime_components": ["simulation", "px4", "gazebo", "mavsdk"],
  "constraints": {
    "visual_supported": true,
    "headless_supported": true
  }
}
```

## Initial capability list for Mark 1

- `simulation.lifecycle`
- `scenario.takeoff_land.run`
- `scenario.patrol_basic.run`
- `mission.control`
- `vehicle.basic_control`
- `safety.fault_injection`
- `telemetry.read_model`
- `replay.read`
- `perception.observe`

## Initial action list for Mark 1

- `simulation.start`
- `simulation.stop`
- `simulation.restart`
- `simulation.status.get`
- `capabilities.list`
- `scenario.list`
- `scenario.run`
- `scenario.cancel`
- `scenario.status.get`
- `mission.start`
- `mission.abort`
- `mission.reset`
- `mission.status.get`
- `vehicle.arm`
- `vehicle.disarm`
- `vehicle.takeoff`
- `vehicle.land`
- `vehicle.return_to_home`
- `safety.inject_fault`
- `safety.clear_fault`
- `safety.status.get`
- `telemetry.snapshot.get`
- `telemetry.metrics.get`
- `telemetry.events.get`
- `telemetry.runs.list`
- `telemetry.replay.get`

## Mapping from current repo

### Shell-backed
- `simulation.start`
- `simulation.stop`

### MAVSDK-backed
- `scenario.takeoff_land.run`
- portions of vehicle control when used in scenario context

### ROS 2-backed
- `mission.start`
- `mission.abort`
- `mission.reset`
- `vehicle.*`
- `safety.inject_fault`
- `safety.clear_fault`

### Read model-backed
- `telemetry.*`

## R5/R6 execution note

- `scenario.takeoff_land.run` continua materializada pela superfície unificada
- `scenario.patrol_basic.run` deixa de ser apenas formalizada e passa a ser `available` via `mission.control`
- `mission.start`, `mission.abort`, `mission.reset` e `mission.status.get` passam a ser operáveis pela Control API
- `mission.start:patrol_basic` e `scenario.run:patrol_basic` compartilham o mesmo runtime ROS 2, sem expor `MissionCommand` bruto para a UI
- `vehicle.basic_control` fica `available` em `R6`, cobrindo `arm`, `disarm`, `takeoff`, `land`, `return_to_home` e `goto`
- `safety.fault_injection` fica `available` em `R6`, cobrindo inject/clear fault e `safety.status.get`
- `scenario.list` e `scenario.status.get` não precisam expor `executor_type` para a UI; essa decisão continua interna ao control plane

## R7 execution note

- `telemetry.read_model` passa a ser `available` em `R7`
- `telemetry.snapshot.get`, `telemetry.metrics.get`, `telemetry.events.get`, `telemetry.runs.list` e `telemetry.replay.get` deixam de ser apenas formais e passam a responder pela surface unificada do control plane
- `telemetry.runs.list` continua distinto de `RunRecord` de controle; a agregação acontece no boundary da Control API, sem misturar command model com read model na origem

## Anti-pattern
Não deixar actions "existirem" apenas como:
- um comando shell
- um tópico bruto
- uma chamada escondida em componente frontend
