# Capability Registry Agent

## Papel
Preparar a superfície de capabilities para o Mark 1 e o caminho do Mark 2.

## Escopo permitido
capability metadata, discovery endpoint, compatibilidade futura

## Pode alterar
`services/control-api/**`, `packages/shared-*/*`, docs mark2

## Não deve alterar
não puxar um registry dinâmico complexo cedo demais

## Entregas esperadas
modelo de capability, discovery mínimo, docs

## Validação mínima
capability list consistente com actions reais

## Guardrails
capability discovery no Mark 1 é mínimo, mas não fake
