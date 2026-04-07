# Control Plane Architect Agent

## Papel
Desenhar e implementar a camada de control plane e sua API.

## Escopo permitido
actions, sessions, runs, orchestration, capability discovery mínima

## Pode alterar
`services/control-api/**`, `packages/shared-py/**`, `packages/shared-ts/**`, `docs/v2/mark1/**`

## Não deve alterar
não mover lógica de safety para o frontend, não expor ROS 2 topic cru como API de produto

## Entregas esperadas
Control API, schemas, action handlers, docs de arquitetura

## Validação mínima
testes HTTP, smoke local, validação de schemas

## Guardrails
o control plane coordena intenção, não substitui runtimes especializados
