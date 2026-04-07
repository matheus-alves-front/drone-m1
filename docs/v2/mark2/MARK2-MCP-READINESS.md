# Mark 2 MCP Readiness

## Objetivo
Preparar a futura superfície programática para IA/MCP sem permitir acesso caótico ao runtime interno.

## Regra central
MCP/IA deve falar com **actions e capabilities do control plane**, não com:
- PX4 diretamente
- ROS 2 topics crus
- shell scripts
- callbacks da UI

## MCP-facing tool families futuras

### Discovery
- `list_capabilities`
- `get_runtime_status`
- `get_vehicle_status`
- `get_payload_inventory`

### Execution
- `run_scenario`
- `start_mission`
- `abort_mission`
- `vehicle_action`

### Safety-aware
- `inject_fault`
- `clear_fault`
- `validate_plan`

### Observation
- `get_snapshot`
- `get_metrics`
- `get_events`
- `get_replay`
- `get_perception_status`

## Requisitos para readiness
- actions formais
- run ids claros
- error model estável
- capability discovery
- response contracts claros
- policy boundaries explícitas
