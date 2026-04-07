# Mark 1 Control Plane Architecture

## Objetivo
Unificar a superfície de controle do produto.

## O que é o Control Plane
A camada que transforma o sistema de:
- shell scripts
- validators
- ROS topics
- runner MAVSDK

em uma superfície única de:
- actions
- capabilities
- runs
- sessions
- stateful orchestration

## Entidades centrais

### SimulationSession
Representa o lifecycle do runtime simulado.

Campos mínimos:
- `session_id`
- `status`
- `mode` (`headless`, `visual`)
- `started_at`
- `stopped_at`
- `environment`
- `runtime_components`

### Run
Representa uma execução rastreável.

Campos mínimos:
- `run_id`
- `run_type`
- `target`
- `status`
- `started_at`
- `ended_at`
- `session_id`
- `result_summary`

### ActionRequest
Pedido formal de ação.

Campos mínimos:
- `action_name`
- `target`
- `input`
- `requested_by`
- `request_id`
- `session_id`
- `run_id` opcional

### ActionResult
Resultado formal de ação.

Campos mínimos:
- `accepted`
- `status`
- `message`
- `run_id`
- `artifacts`
- `errors`

## Initial action families

### Simulation
- `simulation.start`
- `simulation.stop`
- `simulation.restart`
- `simulation.status.get`

### Scenario
- `scenario.list`
- `scenario.run`
- `scenario.cancel`
- `scenario.status.get`

Regra de surface em `R4`:
- a seleção de executor é interna ao control plane
- a UI vê nome, kind, disponibilidade e status do cenário
- `takeoff_land` fica materializado em `R4`
- cenários ROS 2 ficam formalizados, mas continuam `experimental` até suas fases runtime

### Mission
- `mission.start`
- `mission.abort`
- `mission.reset`
- `mission.status.get`

Regra de surface em `R5`:
- `patrol_basic` é operado pela mission surface, não por `ros2 topic pub` direto na experiência de produto
- o adapter ROS 2 continua encapsulando `MissionCommand` e a leitura consolidada de `MissionStatus`
- `mission.start` e `scenario.run:patrol_basic` convergem para o mesmo runtime de missão, com `scenario.status.get` servindo como acompanhamento homogêneo do run
- o control plane não move a state machine de missão para a UI

### Vehicle
- `vehicle.arm`
- `vehicle.disarm`
- `vehicle.takeoff`
- `vehicle.land`
- `vehicle.return_to_home`
- `vehicle.goto`

Regra de surface em `R6`:
- `vehicle.*` entra pela Control API e é encapsulado pelo adapter ROS 2 de veículo
- a UI não fala com `VehicleCommand` cru
- o control plane mantém auditoria e correlação de run sem mover lógica de PX4 para o frontend

### Safety
- `safety.inject_fault`
- `safety.clear_fault`
- `safety.status.get`

Regra de surface em `R6`:
- `safety.inject_fault` e `safety.clear_fault` entram pela Control API e continuam passando pelo runtime soberano de safety
- `safety.status.get` traduz o estado consolidado do read model para contrato de produto
- safety continua podendo abortar missão e enviar comando de veículo sem depender de UI ou IA

### Perception
- `perception.status.get`
- `perception.stream.status.get`

### Telemetry
- `telemetry.snapshot.get`
- `telemetry.metrics.get`
- `telemetry.events.get`
- `telemetry.replay.get`
- `telemetry.runs.list`

### Discovery
- `capabilities.list`

## Adapters

### Shell adapter
Encapsula:
- `scripts/sim/start.sh`
- `scripts/sim/stop.sh`
- validators utilitários quando necessário

### MAVSDK adapter
Encapsula:
- `takeoff_land`
- futuros runners homogêneos de cenário

### ROS 2 adapter
Encapsula:
- `MissionCommand`
- `VehicleCommand`
- `SafetyFault`
- estados agregados de runtime

### Read model adapter
Encapsula:
- Telemetry API atual
- futuras queries consolidadas

## Suggested API shape

### HTTP/JSON example
- `POST /api/v1/control/simulation/start`
- `POST /api/v1/control/scenarios/{scenario_name}/run`
- `POST /api/v1/control/missions/start`
- `POST /api/v1/control/safety/faults`
- `GET /api/v1/control/capabilities`
- `GET /api/v1/control/status`
- `GET /api/v1/read/snapshot`
- `GET /api/v1/read/metrics`
- `GET /api/v1/read/events`
- `GET /api/v1/read/runs`
- `GET /api/v1/read/replay`

### Websocket/events
Opcionalmente:
- run status stream
- action status stream
- session status stream

## Critical design rule
O control plane deve orquestrar intenção e lifecycle, mas não substituir a lógica dos runtimes especializados.

## R7 note
- a Control API continua dona da surface unificada de leitura, mas não passa a armazenar ou recalcular telemetria bruta
- a Telemetry API consolidada fica responsável por `snapshot`, `metrics`, `events`, `runs` e `replay`
- `read/runs` pode agregar `RunRecord` do control plane com `telemetry_session` do read model, preservando a separação entre controle e observabilidade
