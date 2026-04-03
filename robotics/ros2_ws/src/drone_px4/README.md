# drone_px4

Pacote de fronteira entre o domínio ROS 2 do projeto e a integração real com PX4.

## Papel

- receber comandos de alto nível em `drone_msgs`
- publicar estado operacional simplificado em `drone_msgs`
- publicar status de comando em `drone_msgs`
- isolar a evolução interna da integração com `px4_msgs`

## Tópicos

- publica `VehicleState` em `/drone/vehicle_state`
- publica `VehicleCommandStatus` em `/drone/vehicle_command_status`
- consome `VehicleCommand` em `/drone/vehicle_command`
- assina `px4_msgs` reais em `/fmu/out/*`
- publica comandos reais de PX4 em `/fmu/in/vehicle_command`

## Runtime

O pacote da Fase 3 assume integração real com:

- PX4 SITL
- Micro XRCE-DDS Agent
- `px4_msgs` alinhado com `release/1.16`
