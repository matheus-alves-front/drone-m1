# Dashboard

Frontend da Fase 7 para observabilidade operacional da simulação.

## Papel

- mostrar snapshot operacional do veículo, missão e safety
- exibir eventos recentes e métricas agregadas
- permitir inspeção de replay por `run_id`
- consumir somente a API de telemetria, sem carregar regra de missão

## Paineis principais

- cards operacionais de `vehicle`, `mission`, `safety` e `perception`
- feed de eventos recentes
- replay scrub por `run_id`
- painel de metricas agregadas
- inventario de runs persistidos

## Fluxo de dados

- `GET /api/v1/snapshot`
- `GET /api/v1/metrics`
- `GET /api/v1/events`
- `GET /api/v1/runs`
- `GET /api/v1/replay/{run_id}`
- `WS /ws/telemetry`

## Comandos

```bash
npm install --prefix apps/dashboard
npm run --prefix apps/dashboard dev
npm test --prefix apps/dashboard
npm run --prefix apps/dashboard build
```

## Regra arquitetural

O dashboard e apenas camada de apresentacao. Ele nao implementa state machine de missao, politica de safety nem integra direto com PX4.
