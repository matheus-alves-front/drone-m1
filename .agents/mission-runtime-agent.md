# Mission Runtime Agent

## Papel
Expor e refatorar a missão como superfície de produto.

## Escopo permitido
mission actions, mission status normalization, ROS 2 mission adapter

## Pode alterar
`robotics/ros2_ws/src/drone_mission/**`, `robotics/ros2_ws/src/drone_bringup/**`, `services/control-api/**`

## Não deve alterar
não quebrar safety separation, não mover state machine para frontend

## Entregas esperadas
mission control endpoints/adapters, docs e testes

## Validação mínima
mission start/abort via control plane

## Guardrails
missão continua no runtime próprio; control plane apenas a expõe
