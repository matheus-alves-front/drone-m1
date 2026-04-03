# drone_telemetry

Bridge de telemetria da Fase 7 para o workspace ROS 2 do projeto.

## Papel

- consumir contratos de dominio ja estabilizados no ROS 2
- normalizar eventos operacionais em envelopes pequenos e auditaveis
- encaminhar telemetria para a API de observabilidade
- manter replay, dashboard e metricas desacoplados de `px4_msgs`

## Envelope operacional

Cada mensagem observada pelo bridge e convertida no envelope:

- `run_id`
- `source`
- `kind`
- `topic`
- `stamp_ns`
- `payload`

O bridge nao replica mensagens ROS 2 inteiras nem frame bruto. Ele extrai somente o payload operacional necessario para auditoria e replay.

## Topicos observados

- `/drone/vehicle_state`
- `/drone/vehicle_command_status`
- `/drone/mission_status`
- `/drone/safety_status`
- `/drone/perception_heartbeat`
- `/drone/perception/event`
- `/drone/perception/tracked_object`

## Limites arquiteturais

- nao toma decisoes de missao
- nao implementa politica de safety
- nao fala direto com PX4
- so consome contratos de dominio e envia envelopes operacionais para o backend

## Validacao

```bash
PYTHONPATH=robotics/ros2_ws/src/drone_telemetry python3 -m unittest discover \
  -s robotics/ros2_ws/src/drone_telemetry/test \
  -p "test_*.py"
```
