# Dashboard

Frontend da Operator Console do Mark 1 concluído em `R15`.

## Papel

- expor a shell operacional humana do control plane
- controlar simulação, cenários, missão, veículo e safety por actions formais
- observar percepção, heartbeat, tracked object, runs, events, metrics e replay
- consolidar `session`, `run`, `actions` e `state` sem mover lógica central para o frontend
- consumir `Control API` para comando e `Read API` para observabilidade

## Páginas principais

- `Overview` com service/session/vehicle/mission/safety/perception
- `Control` com simulação, cenários e veículo
- `Mission` com start/abort/reset e estado consolidado
- `Safety` com inject/clear de fault e auditoria recente
- `Perception` com heartbeat, tracked object e stream/proxy status
- `Runs / Replay` com inventário, eventos, métricas e replay
- `Settings / Environment` com boundary de APIs e ambiente atual

## Fluxo de dados

- `GET /api/v1/control/status`
- `GET /api/v1/control/capabilities`
- `GET /api/v1/control/scenarios`
- `GET /api/v1/control/scenarios/{scenario_name}/status`
- `GET /api/v1/control/missions/status`
- `GET /api/v1/control/safety/status`
- `GET /api/v1/control/perception/status`
- `GET /api/v1/control/perception/stream/status`
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
- `GET /api/v1/read/snapshot`
- `GET /api/v1/read/metrics`
- `GET /api/v1/read/events`
- `GET /api/v1/read/runs`
- `GET /api/v1/read/replay`

## Comandos

```bash
npm install --prefix apps/dashboard
npm run --prefix apps/dashboard dev
npm test --prefix apps/dashboard
npm run --prefix apps/dashboard build
```

## Regra arquitetural

O dashboard continua sendo apenas camada de apresentacao. Ele nao implementa state machine de missao, politica de safety, escolha de executor nem integra direto com PX4, MAVSDK ou ROS 2 topic cru.

## Evidência atual

- `npm --prefix apps/dashboard test`
- `npm --prefix apps/dashboard run build`

Os testes da UI cobrem os fluxos principais de `R9-R11` já aceitos em `R15`: start de simulação, run de `takeoff_land`, start/abort de missão, inject/clear de fault e correlação `action -> run`.
