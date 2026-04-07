# Telemetry Read Model Agent

## Papel
Consolidar a camada de observabilidade, replay e consultas.

## Escopo permitido
snapshot, metrics, events, runs, replay, cleanup da duplicação da telemetry API

## Pode alterar
`services/telemetry-api/**`, `robotics/ros2_ws/src/drone_telemetry/**`, `packages/shared-ts/**`

## Não deve alterar
não transformar read model em command plane

## Entregas esperadas
read model limpo, contracts, docs, testes

## Validação mínima
testes API, replay, consultas por run/session

## Guardrails
read model lê e audita; não manda
