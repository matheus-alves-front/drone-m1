# Telemetry API

Read model canônico da `R7` do Mark 1.

## Papel

- receber envelopes do `telemetry_bridge_node`
- persistir sessões de telemetria por `run_id`
- materializar `snapshot`, `metrics`, `events` e `replay` sem virar command plane
- expor consultas estáveis para Control API e Operator UI
- preservar correlação opcional de `session_id` quando o runtime a informar

## Trilha canônica

- a implementação operacional fica em `services/telemetry-api/telemetry_api/`
- `services/telemetry-api/src/telemetry_api/` fica isolada como trilha legada de auditoria e não deve receber novas features
- o pacote instalável do serviço é `drone-telemetry-api`

## Conceitos

- `run_id`: execução auditável do read model
- `session_id`: correlação opcional com a sessão do control plane
- `snapshot`: estado operacional consolidado da run atual
- `metrics`: série derivada do snapshot por run
- `events`: timeline estruturada por run
- `replay`: agregação ordenada de `snapshot + events + metrics`

## Endpoints

- `GET /api/v1/health`
- `POST /api/v1/ingest`
- `GET /api/v1/snapshot`
- `GET /api/v1/metrics?run_id=&limit=`
- `GET /api/v1/events?run_id=&kind=&limit=`
- `GET /api/v1/runs`
- `GET /api/v1/replay/{run_id}?limit=`
- `GET /api/v1/sessions`
- `GET /api/v1/sessions/current`
- `GET /api/v1/sessions/{run_id}`
- `GET /api/v1/sessions/{run_id}/snapshot`
- `GET /api/v1/sessions/{run_id}/events`
- `GET /api/v1/sessions/{run_id}/metrics`
- `GET /api/v1/sessions/{run_id}/replay`
- `WS /ws/telemetry`
- `WS /ws/telemetry/current`
- `WS /ws/telemetry/{run_id}`

## Persistência

- `data/current_session.json`
- `data/snapshot.json`
- `data/runs/<run_id>/session.json`
- `data/runs/<run_id>/snapshot.json`
- `data/runs/<run_id>/events.jsonl`
- `data/runs/<run_id>/metrics.jsonl`

## Instalação local

```bash
python3 -m pip install -e 'services/telemetry-api[test]'
```

## Teste

```bash
PYTHONPATH=services/telemetry-api .venv-r3/bin/python -m pytest services/telemetry-api/tests -q
```

## Smoke rápido

```bash
curl -X POST http://127.0.0.1:8080/api/v1/ingest \
  -H 'content-type: application/json' \
  -d '{
    "run_id":"run-demo",
    "session_id":"session-demo",
    "source":"telemetry_bridge_node",
    "kind":"vehicle_state",
    "topic":"/drone/vehicle_state",
    "stamp_ns":123,
    "payload":{"connected":true,"armed":false}
  }'

curl http://127.0.0.1:8080/api/v1/snapshot
curl http://127.0.0.1:8080/api/v1/events?run_id=run-demo
curl http://127.0.0.1:8080/api/v1/replay/run-demo
```
