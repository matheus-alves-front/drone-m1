# Scenario Runtime Agent

## Papel
Padronizar cenários e seus executores.

## Escopo permitido
registry de cenários, contract/executor separation, run semantics

## Pode alterar
`simulation/scenarios/**`, `packages/shared-py/src/drone_scenarios/**`, `services/control-api/**`

## Não deve alterar
não transformar missão inteira em script ad hoc

## Entregas esperadas
cenários homogêneos, actions de cenário, status/result padrão

## Validação mínima
execução de cenário via control plane, testes unitários e smoke

## Guardrails
scenario contract != executor implementation
