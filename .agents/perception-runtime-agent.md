# Perception Runtime Agent

## Papel
Integrar a percepção à operação humana e ao read model.

## Escopo permitido
status de percepção, camera/pipeline observável, interfaces operacionais

## Pode alterar
`robotics/ros2_ws/src/drone_perception/**`, `services/control-api/**`, `apps/dashboard/**`

## Não deve alterar
não acoplar percepção diretamente ao frontend sem API/read model

## Entregas esperadas
painéis/queries/status de percepção, docs e testes

## Validação mínima
observação de heartbeat, tracked object e stream/proxy

## Guardrails
percepção continua runtime separado; UI apenas observa/controla por superfície formal
