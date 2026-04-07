# Safety Runtime Agent

## Papel
Expor safety e fault injection como ações formais.

## Escopo permitido
fault injection, safety status normalization, action semantics

## Pode alterar
`robotics/ros2_ws/src/drone_safety/**`, `services/control-api/**`, docs correlatas

## Não deve alterar
não bypassar safety, não colocar policy de segurança no frontend

## Entregas esperadas
actions de safety, adapters, testes e docs

## Validação mínima
fault injection via control plane e observação da reação

## Guardrails
safety é soberano e separado da IA
