# PHASE-7-OPERATIONS-CONTRACT.md

## Objetivo

Registrar o contrato tecnico da Fase 7 apos a validacao da camada de operacao e observabilidade do projeto.

## Componentes da fase

- `robotics/ros2_ws/src/drone_telemetry/drone_telemetry/telemetry_bridge_node.py`
- `robotics/ros2_ws/src/drone_telemetry/drone_telemetry/serializers.py`
- `robotics/ros2_ws/src/drone_telemetry/drone_telemetry/transport.py`
- `robotics/ros2_ws/src/drone_bringup/config/drone_telemetry.yaml`
- `services/telemetry-api/telemetry_api/app.py`
- `services/telemetry-api/telemetry_api/store.py`
- `apps/dashboard/src/App.tsx`
- `apps/dashboard/src/lib/api.ts`
- `robotics/ros2_ws/scripts/validate-phase-7.sh`

## Topicos de dominio observados pelo bridge

- `/drone/vehicle_state`
- `/drone/vehicle_command_status`
- `/drone/mission_status`
- `/drone/safety_status`
- `/drone/perception/tracked_object`
- `/drone/perception_heartbeat`
- `/drone/perception/event`

## Envelope operacional materializado

Cada mensagem observada pelo bridge e serializada como:

- `run_id`
- `source`
- `kind`
- `topic`
- `stamp_ns`
- `payload`

O `payload` preserva somente o estado operacional relevante para auditoria, replay e dashboard.

## API materializada

### Endpoints HTTP

- `GET /api/v1/health`
- `POST /api/v1/ingest`
- `GET /api/v1/snapshot`
- `GET /api/v1/metrics`
- `GET /api/v1/events`
- `GET /api/v1/runs`
- `GET /api/v1/replay/{run_id}`

### Endpoint websocket

- `WS /ws/telemetry`

O websocket envia um `snapshot` inicial e depois um `telemetry_event` para cada envelope ingerido.

## Persistencia validada

- `services/telemetry-api/data/snapshot.json`
- `services/telemetry-api/data/metrics.json`
- `services/telemetry-api/data/runs/<run_id>/events.jsonl`
- `services/telemetry-api/data/runs/<run_id>/snapshot.json`
- `services/telemetry-api/data/runs/<run_id>/metrics.json`

## Fonte de verdade da fase

- Estado de runtime do dominio:
  - `drone_msgs/*`
  - origem: bridge ROS 2, mission, safety e perception
- Persistencia operacional:
  - Telemetry API + arquivos estruturados por `run_id`
- Visualizacao:
  - dashboard React consumindo apenas HTTP + websocket da API

## Limites arquiteturais

- `drone_telemetry` nao toma decisoes de missao
- `drone_telemetry` nao implementa politica de safety
- a Telemetry API nao controla o voo nem injeta logica no dominio
- o dashboard nao implementa state machine nem regras de safety

## Sequencia validada da fase

1. Validar serializacao e transporte do `telemetry_bridge_node`
2. Validar ingest, persistencia e consultas da Telemetry API
3. Validar renderizacao do dashboard com snapshot, metrics, events, runs e replay
4. Validar stream websocket do dashboard para refletir eventos operacionais
5. Validar `build` de producao do frontend

## Criterio terminal da fase

A Fase 7 so conta como concluida quando o comando abaixo passa:

```bash
bash robotics/ros2_ws/scripts/validate-phase-7.sh
```

Esse fluxo precisa provar:

- bridge ROS 2 serializando envelopes auditaveis
- API persistindo e consultando `snapshot`, `metrics`, `events`, `runs` e `replay`
- dashboard renderizando o estado operacional sem logica de missao
- `test` e `build` do frontend aprovados no mesmo validador oficial
