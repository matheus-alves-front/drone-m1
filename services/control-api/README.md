# Control API

Backend do control plane do Mark 1.

## Papel atual

- o serviço agora sustenta a superfície operacional usada pela UI do Mark 1 até `R15`
- implementa `simulation.start`, `simulation.stop`, `simulation.restart`, `simulation.status.get`, `scenario.list`, `scenario.run`, `scenario.cancel`, `scenario.status.get`, `mission.start`, `mission.abort`, `mission.reset`, `mission.status.get`, `vehicle.*`, `safety.*`, `perception.status.get`, `perception.stream.status.get` e os proxies reais do read model (`snapshot`, `metrics`, `events`, `runs`, `replay`)
- o lifecycle real da simulação passa pelo adapter shell oficial sobre `scripts/sim/start.sh` e `scripts/sim/stop.sh`
- `takeoff_land` roda pela Control API usando o runner MAVSDK existente via `scripts/scenarios/run_scenario.sh`
- `patrol_basic` roda pela Control API através da mission surface e do adapter ROS 2 sobre `/drone/mission_command`
- `mission.start:patrol_basic` e `scenario.run:patrol_basic` convergem para o mesmo runtime de missão, preservando `scenario.status.get` como surface única de acompanhamento
- a leitura consolidada de missão usa o `mission_status` do read model para traduzir estado ROS 2 em estado de produto
- `vehicle.arm`, `vehicle.disarm`, `vehicle.takeoff`, `vehicle.land`, `vehicle.return_to_home` e `vehicle.goto` passam pela mesma Control API e são despachados ao runtime ROS 2 sem expor tópico cru
- `safety.inject_fault`, `safety.clear_fault` e `safety.status.get` entram pela mesma surface, com faults ativos mantidos no boundary do control plane e estado consolidado vindo do read model
- `perception.status.get` traduz `tracked_object`, `perception_heartbeat` e `perception_event` do read model para contrato de produto
- `perception.stream.status.get` expõe disponibilidade de stream/proxy por environment contract, sem empurrar lógica de câmera para a UI
- os cenários `geofence_breach`, `failsafe_*` e `perception_target_tracking` entram no registry unificado; `perception_target_tracking` continua formalizado no catálogo, mesmo que seu executor específico continue sujeito ao runtime disponível
- `session_id` e `runs` ficam persistidos em disco sob o state root do serviço
- o preflight de runtime é executado antes de `simulation.start` e falhas são normalizadas em erros de control plane
- o endpoint `GET /api/v1/health` expõe readiness do runtime já agregada pela sessão atual
- `scenario.list` não expõe `executor_type` para a UI; a decisão de executor continua interna ao control plane
- `GET /api/v1/read/*` agora consome a Telemetry API consolidada e reforça a correlação de `run_id` e `session_id`
- a superfície pública do Mark 1 fica completa com simulação, cenários, missão, veículo, safety, percepção e read model, sem depender de fases adicionais para a experiência central de produto

## Endpoints principais

- `GET /api/v1/health`
- `GET /api/v1/control/status`
- `GET /api/v1/control/actions`
- `GET /api/v1/control/capabilities`
- `GET /api/v1/control/scenarios`
- `GET /api/v1/control/scenarios/{scenario_name}/status`
- `GET /api/v1/control/missions/status`
- `GET /api/v1/control/safety/status`
- `GET /api/v1/control/perception/status`
- `GET /api/v1/control/perception/stream/status`
- `GET /api/v1/control/simulation/status`
- `GET /api/v1/read/snapshot`
- `GET /api/v1/read/metrics`
- `GET /api/v1/read/events`
- `GET /api/v1/read/runs`
- `GET /api/v1/read/replay`
- `POST /api/v1/control/simulation/start`
- `POST /api/v1/control/simulation/stop`
- `POST /api/v1/control/simulation/restart`
- `POST /api/v1/control/scenarios/{scenario_name}/run`
- `POST /api/v1/control/scenarios/{scenario_name}/cancel`
- `POST /api/v1/control/missions/start`
- `POST /api/v1/control/missions/abort`
- `POST /api/v1/control/missions/reset`
- `POST /api/v1/control/vehicles/{command}`
- `POST /api/v1/control/safety/faults/inject`
- `POST /api/v1/control/safety/faults/clear`

## Instalação local

```bash
python3 -m pip install -e packages/shared-py
python3 -m pip install -e 'services/control-api[test]'
```

## Rodar o serviço

```bash
control-api
```

Ou:

```bash
python3 -m control_api.main
```

Variáveis úteis:

- `CONTROL_API_PORT`
- `TELEMETRY_API_BASE_URL`
- `CONTROL_API_STATE_DIR`
- `CONTROL_API_PERCEPTION_STREAM_URL`
- `CONTROL_API_PERCEPTION_STREAM_MODE`
- `CONTROL_API_PERCEPTION_STREAM_SOURCE`

O shell adapter também respeita o contrato existente de:

- `PHASE1_RUNTIME_DIR`
- `PHASE1_LOG_DIR`
- `PHASE1_HEADLESS`
- `PHASE1_GZ_PARTITION`

## Teste

```bash
.venv-r3/bin/python -m pytest services/control-api/tests -q
```

Validação integrada do read model consolidado:

```bash
PYTHONPATH=services/telemetry-api .venv-r3/bin/python -m pytest services/telemetry-api/tests -q
```

Checks diretos do contrato shell:

```bash
bash scripts/sim/start.sh --check
bash scripts/sim/stop.sh --check
```

Validação do seam real de cenário:

```bash
PYTHONPATH=packages/shared-py/src \
  bash scripts/scenarios/run_scenario.sh \
  simulation/scenarios/takeoff_land.json \
  --backend fake-success \
  --output json
```

Validação contratual dos pacotes compartilhados:

```bash
PYTHONPATH=packages/shared-py/src .venv-r3/bin/python -m pytest packages/shared-py/tests -q
node --experimental-strip-types --test packages/shared-ts/tests/control-plane.test.ts
```

Smoke de import do serviço:

```bash
source /home/matheusalves/Dev/random/drone-sim-complete/.venv-r3/bin/activate
python - <<'PY'
from control_api.app import create_app
app = create_app()
print(app.title, app.version)
PY
```

## Smoke manual headless

```bash
curl -X POST http://127.0.0.1:8090/api/v1/control/simulation/start \
  -H 'content-type: application/json' \
  -d '{"input":{"mode":"headless"}}'

curl http://127.0.0.1:8090/api/v1/control/simulation/status

curl http://127.0.0.1:8090/api/v1/health

curl -X POST http://127.0.0.1:8090/api/v1/control/simulation/stop \
  -H 'content-type: application/json' \
  -d '{}'
```

## Smoke manual visual

```bash
curl -X POST http://127.0.0.1:8090/api/v1/control/simulation/start \
  -H 'content-type: application/json' \
  -d '{"input":{"mode":"visual"}}'
```

O modo visual usa `PHASE1_HEADLESS=0` no shell adapter e delega a subida real ao contrato existente de `scripts/sim/start.sh`.

## Smoke manual de cenário

```bash
curl -X POST http://127.0.0.1:8090/api/v1/control/scenarios/takeoff_land/run \
  -H 'content-type: application/json' \
  -d '{"input":{"backend":"fake-success"}}'

curl http://127.0.0.1:8090/api/v1/control/scenarios/takeoff_land/status

curl -X POST http://127.0.0.1:8090/api/v1/control/scenarios/takeoff_land/cancel \
  -H 'content-type: application/json' \
  -d '{}'
```

## Smoke manual de missão via superfície de cenário

```bash
curl -X POST http://127.0.0.1:8090/api/v1/control/scenarios/patrol_basic/run \
  -H 'content-type: application/json' \
  -d '{}'

curl http://127.0.0.1:8090/api/v1/control/scenarios/patrol_basic/status

curl -X POST http://127.0.0.1:8090/api/v1/control/scenarios/patrol_basic/cancel \
  -H 'content-type: application/json' \
  -d '{}'
```

## Smoke manual de missão

Prerequisito:

```bash
ros2 launch drone_bringup bringup.launch.py enable_mission:=true mission_auto_start:=false
```

Em outro terminal:

```bash
curl -X POST http://127.0.0.1:8090/api/v1/control/missions/start \
  -H 'content-type: application/json' \
  -d '{"input":{"mission_name":"patrol_basic"}}'

curl http://127.0.0.1:8090/api/v1/control/missions/status

curl -X POST http://127.0.0.1:8090/api/v1/control/missions/abort \
  -H 'content-type: application/json' \
  -d '{"input":{"mission_name":"patrol_basic","reason":"operator stop"}}'

curl -X POST http://127.0.0.1:8090/api/v1/control/missions/reset \
  -H 'content-type: application/json' \
  -d '{"input":{"mission_name":"patrol_basic"}}'
```

## Smoke manual de vehicle/safety

```bash
curl -X POST http://127.0.0.1:8090/api/v1/control/vehicles/arm \
  -H 'content-type: application/json' \
  -d '{}'

curl -X POST http://127.0.0.1:8090/api/v1/control/vehicles/return_to_home \
  -H 'content-type: application/json' \
  -d '{}'

curl -X POST http://127.0.0.1:8090/api/v1/control/safety/faults/inject \
  -H 'content-type: application/json' \
  -d '{"input":{"fault_type":"gps_loss","value":1.0,"detail":"operator test"}}'

curl http://127.0.0.1:8090/api/v1/control/safety/status

curl -X POST http://127.0.0.1:8090/api/v1/control/safety/faults/clear \
  -H 'content-type: application/json' \
  -d '{"input":{"fault_type":"gps_loss"}}'
```

## Evidência final do Mark 1

- `simulation.start`, `simulation.stop` e `simulation.restart` criam `RunRecord` rastreável
- o estado de `SimulationSession` é persistido em disco e recarregado em novo processo da API
- capability discovery marca `scenario.takeoff_land.run`, `scenario.patrol_basic.run`, `mission.control`, `vehicle.basic_control` e `safety.fault_injection` como `available`
- `scenario.run:takeoff_land` e `scenario.cancel:takeoff_land` ficam auditáveis em `GET /api/v1/read/runs`
- `mission.start:patrol_basic`, `mission.abort:patrol_basic` e `mission.reset:patrol_basic` ficam auditáveis em `GET /api/v1/read/runs`
- `vehicle.arm`, `vehicle.disarm`, `vehicle.takeoff`, `vehicle.land`, `vehicle.return_to_home` e `vehicle.goto` passam a gerar runs auditáveis na mesma surface
- `safety.inject_fault` e `safety.clear_fault` passam a gerar runs auditáveis e a manter faults ativos no boundary do control plane
- `scenario.run:patrol_basic` e `scenario.cancel:patrol_basic` passam pela mesma mission surface sem expor tópico bruto para a UI
- `mission.start` direto também reconcilia `scenario.status.get` para `patrol_basic`, evitando duas superfícies divergentes para o mesmo runtime
- `scenario.status.get` é reconciliado com o runner de cenário e mantém `last_run_id` consultável
- `mission.status.get` devolve `MissionDefinition` com phase consolidada para estado de produto
- `safety.status.get` devolve `SafetyStatus` consolidado sem fazer o cliente ler `SafetyStatus.msg` cru
- `perception.status.get` devolve heartbeat, tracked object e último tipo de evento sem exigir leitura direta de envelope cru
- `perception.stream.status.get` explicita se existe stream/proxy de câmera no ambiente atual
- `read/snapshot`, `read/metrics`, `read/events` e `read/replay` deixam de ser stubs e passam a proxy real da Telemetry API
- `read/runs` continua expondo os runs do control plane e agora também incorpora runs do read model como `telemetry_session`
- a correlação de `session_id` é preservada tanto no control plane quanto nos envelopes de telemetria quando o runtime a fornece
- o state root padrão do serviço fica em `.sim-runtime/control-api-state/` com `session.json`, `runs.json`, `scenarios.json` e caches de mission/vehicle/safety surface
