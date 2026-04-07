# Mark 1 Observability and Read Model

## Objetivo
Preservar a força de telemetria/replay atual, mas separando claramente leitura e comando.

## Read model responsibilities
- snapshot operacional
- timeline de eventos
- métricas
- runs
- replay

## Command model responsibilities
- iniciar e parar simulação
- executar cenário
- iniciar/abortar missão
- injetar fault
- controlar veículo

## Current-state issue to address
A auditoria identificou duas trilhas para a Telemetry API.  
O Mark 1 deve consolidar uma implementação operacional única.

## R7 result
- implementação canônica: `services/telemetry-api/telemetry_api/*`
- trilha legada isolada para compatibilidade/auditoria: `services/telemetry-api/src/telemetry_api/*`
- surface explícita de leitura:
  - `snapshot`
  - `metrics`
  - `events`
  - `runs`
  - `replay`
- o control plane passa a consumir essa surface consolidada por `GET /api/v1/read/*`
- a correlação entre `run_id` e `session_id` fica preservada quando o runtime fornece `session_id`, com fallback do control plane para a sessão ativa do Mark 1

## Read model entities

### Snapshot
Visão compacta do estado atual do sistema:
- session
- vehicle
- mission
- safety
- perception
- run summary

### Metrics
Séries ou agregados relevantes:
- altitude
- posição
- heartbeat de percepção
- safety reactions
- action timing

### Events
Eventos estruturados, por exemplo:
- `simulation.started`
- `scenario.started`
- `mission.transitioned`
- `safety.fault.injected`
- `safety.response.triggered`
- `vehicle.armed`
- `vehicle.landed`

### Replay
Leitura agregada e ordenada da execução por `run_id`.

## Rules
1. Todo comando relevante gera evento
2. Toda run relevante gera replay
3. Toda UI action deve poder ser rastreada em run/event
4. O read model não decide a lógica do runtime
