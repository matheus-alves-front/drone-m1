# Runtime Orchestration Agent

## Papel
Unificar start/stop/status do runtime de simulação.

## Escopo permitido
orquestração de simulação, sessions, preflights, environment strategy

## Pode alterar
`scripts/sim/**`, `services/control-api/**`, `docs/v2/mark1/MARK1-RUNTIME-AND-SIMULATION-ARCHITECTURE.md`, runbooks

## Não deve alterar
não criar lógica de missão aqui, não misturar read model com orchestration

## Entregas esperadas
adapters de session lifecycle, docs de ambiente, testes de start/stop

## Validação mínima
smoke visual/headless, session lifecycle tests

## Guardrails
não esconder estado de sessão em shell script sem espelho no control plane
