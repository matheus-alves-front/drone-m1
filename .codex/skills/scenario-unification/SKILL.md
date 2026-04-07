# Scenario Unification

## When to use
Quando a tarefa envolver contratos de cenário, execução de cenário ou runners.

## Goal
Separar contrato, executor, run e observabilidade de cenário.

## Inputs required
scenario jsons, MAVSDK runner, mission runtime

## Output expectations
modelo homogêneo de cenário, endpoints/actions e status

## Rules
scenario contract != executor; operator não deve conhecer a diferença

## Anti-patterns
um cenário por shell script sem modelagem comum

## Validation
scenario run via surface unificada
