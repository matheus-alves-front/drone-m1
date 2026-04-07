# Telemetry Read Model

## When to use
Quando a tarefa envolver snapshot, metrics, events, replay, runs ou telemetry API.

## Goal
Consolidar leitura auditável e separada de comando.

## Inputs required
telemetry-api atual, drone_telemetry, docs de read model

## Output expectations
API consolidada, schemas, docs, limpeza de duplicações

## Rules
read model não manda comando

## Anti-patterns
misturar ingestão/leitura com actions de controle

## Validation
testes API, replay e consistência de run/session
