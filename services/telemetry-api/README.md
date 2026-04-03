# Telemetry API

Backend da Fase 7 para telemetria, replay e observabilidade operacional.

## Papel

- receber envelopes do `telemetry_bridge_node`
- persistir eventos em JSONL por `run_id`
- materializar snapshot e metricas do runtime atual
- expor replay e stream websocket para o dashboard

## Conceitos

- `run_id`: execucao auditavel da simulacao
- `snapshot`: ultimo envelope observado por `kind`
- `metrics`: agregacao simples por tipo e por `run_id`
- `replay`: sequencia persistida de envelopes de um `run_id`

## Endpoints

- `GET /api/v1/health`
- `POST /api/v1/ingest`
- `GET /api/v1/snapshot`
- `GET /api/v1/metrics`
- `GET /api/v1/events`
- `GET /api/v1/runs`
- `GET /api/v1/replay/{run_id}`
- `WS /ws/telemetry`

## Websocket

- o websocket principal envia um `snapshot` inicial
- cada ingestao posterior gera um `telemetry_event`
- o dashboard usa esse stream apenas para refletir estado operacional

## Persistencia

- `data/runs/<run_id>/events.jsonl`
- `data/runs/<run_id>/snapshot.json`
- `data/runs/<run_id>/metrics.json`
- `data/snapshot.json`
- `data/metrics.json`

## Teste

```bash
python3 -m pytest services/telemetry-api/tests -q
```
