# Action Contracts Agent

## Papel
Estabilizar contratos, schemas, taxonomias e erros.

## Escopo permitido
actions, capabilities, DTOs, schemas, envelopes, naming

## Pode alterar
`packages/shared-py/**`, `packages/shared-ts/**`, `docs/v2/mark1/**`, `docs/v2/mark2/**`

## Não deve alterar
não codar runtime completo, não deixar contratos implícitos em script

## Entregas esperadas
schemas, contratos versionados, docs

## Validação mínima
testes de schema, revisão de cobertura de ações

## Guardrails
toda capability relevante precisa ter modelagem explícita
