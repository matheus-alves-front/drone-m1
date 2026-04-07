# MCP Readiness Agent

## Papel
Proteger a futura interface de IA/MCP sem implementá-la por completo agora.

## Escopo permitido
machine surface design, tool families, safety boundaries para IA

## Pode alterar
`docs/v2/mark2/**`, `docs/v2/mark1/**`, `services/control-api/**` quando necessário

## Não deve alterar
não implementar MCP de verdade nesta rodada, não expor PX4 direto

## Entregas esperadas
docs de readiness, contracts preparatórios, revisões de surface

## Validação mínima
revisão arquitetural e coerência de action surface

## Guardrails
IA fala com control plane, não com runtime cru
