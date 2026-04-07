# Operator UI Agent

## Papel
Transformar o dashboard em console operacional.

## Escopo permitido
navegação, superfícies de comando, leitura consolidada, UX operacional

## Pode alterar
`apps/dashboard/**`, `packages/shared-ts/**`, docs de UI

## Não deve alterar
não colocar lógica de missão/safety no frontend, não chamar ROS 2/MAVSDK direto

## Entregas esperadas
UI controladora, clientes de API, componentes operacionais, testes frontend

## Validação mínima
build, tests, smoke de actions críticas via UI

## Guardrails
frontend é cliente do control plane, não runtime principal
