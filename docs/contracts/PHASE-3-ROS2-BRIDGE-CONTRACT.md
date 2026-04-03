# PHASE-3-ROS2-BRIDGE-CONTRACT.md

## Objetivo

Registrar o corte oficial da Fase 3 para o workspace ROS 2, deixando clara a fronteira entre o domínio do projeto e a integração real em runtime com PX4 via uXRCE-DDS.

## Pacotes

- `drone_msgs`: contratos internos de domínio
- `drone_px4`: adaptador entre o domínio e o runtime real de PX4
- `drone_bringup`: ponto de entrada do grafo ROS 2
- `px4_msgs`: pacote oficial alinhado com `release/1.16`

## Fronteiras

- `drone_msgs` não depende de detalhes internos do PX4.
- `drone_px4` é o único pacote autorizado a consumir `px4_msgs` diretamente.
- `drone_bringup` sobe nodes e injeta parâmetros externos, sem conter lógica de missão ou safety.
- `px4_msgs` permanece pinado na família `release/1.16` para preservar compatibilidade com `PX4-Autopilot v1.16.1`.
- O runtime oficial da Fase 3 depende de `PX4 SITL`, `Gazebo Harmonic`, `Micro XRCE-DDS Agent v2.4.3` e do workspace ROS 2 Humble.

## Tópicos oficiais da Fase 3

- `/drone/vehicle_state`
  - tipo: `drone_msgs/msg/VehicleState`
  - direção: publish por `drone_px4`
  - QoS: `reliable`, `keep_last`, `depth=10`
- `/drone/vehicle_command`
  - tipo: `drone_msgs/msg/VehicleCommand`
  - direção: subscribe por `drone_px4`
  - QoS: `reliable`, `keep_last`, `depth=10`
- `/drone/vehicle_command_status`
  - tipo: `drone_msgs/msg/VehicleCommandStatus`
  - direção: publish por `drone_px4`
  - QoS: `reliable`, `transient_local`, `keep_last`, `depth=10`
- `/fmu/out/vehicle_status`
  - tipo: `px4_msgs/msg/VehicleStatus`
  - direção: subscribe por `drone_px4` quando disponível
  - QoS: `best_effort`, `transient_local`, `keep_last`, `depth=1`
- `/fmu/out/vehicle_local_position`
  - tipo: `px4_msgs/msg/VehicleLocalPosition`
  - direção: subscribe por `drone_px4`
  - QoS: `best_effort`, `transient_local`, `keep_last`, `depth=1`
- `/fmu/out/vehicle_global_position`
  - tipo: `px4_msgs/msg/VehicleGlobalPosition`
  - direção: subscribe por `drone_px4`
  - QoS: `best_effort`, `transient_local`, `keep_last`, `depth=1`
- `/fmu/out/vehicle_land_detected`
  - tipo: `px4_msgs/msg/VehicleLandDetected`
  - direção: subscribe por `drone_px4`
  - QoS: `best_effort`, `transient_local`, `keep_last`, `depth=1`
- `/fmu/out/vehicle_control_mode`
  - tipo: `px4_msgs/msg/VehicleControlMode`
  - direção: subscribe por `drone_px4`
  - QoS: `best_effort`, `transient_local`, `keep_last`, `depth=1`
- `/fmu/out/failsafe_flags`
  - tipo: `px4_msgs/msg/FailsafeFlags`
  - direção: subscribe por `drone_px4`
  - QoS: `best_effort`, `transient_local`, `keep_last`, `depth=1`
- `/fmu/out/vehicle_command_ack`
  - tipo: `px4_msgs/msg/VehicleCommandAck`
  - direção: subscribe por `drone_px4`
  - QoS: `best_effort`, `transient_local`, `keep_last`, `depth=1`
- `/fmu/in/vehicle_command`
  - tipo: `px4_msgs/msg/VehicleCommand`
  - direção: publish por `drone_px4`
  - QoS: `best_effort`, `transient_local`, `keep_last`, `depth=1`

## Mensagens de domínio

### `VehicleState`

- `stamp`
- `connected`
- `armed`
- `landed`
- `failsafe`
- `preflight_checks_pass`
- `nav_state`
- `altitude_m`

### `VehicleCommand`

- `stamp`
- `command`
- `target_altitude_m`

### `VehicleCommandStatus`

- `stamp`
- `command`
- `px4_command`
- `result`
- `accepted`
- `result_label`

## Ordem de subida do bringup

1. Carregar `config/drone_px4.yaml`
2. Declarar argumentos de launch para `params_file` e `use_sim_time`
3. Subir `px4_bridge_node`
4. Assinar tópicos reais `/fmu/out/*` expostos por PX4 via uXRCE-DDS
5. Publicar `VehicleState` e `VehicleCommandStatus` no domínio ROS 2
6. Encaminhar `VehicleCommand` para `/fmu/in/vehicle_command`

## Critério operacional da Fase 3

- A Fase 3 não usa `backend_mode=stub`.
- O bridge consome telemetria real de PX4 em runtime.
- O bridge expõe ACKs reais do PX4 no tópico `/drone/vehicle_command_status`.
- A validação oficial observa `VehicleState` durante o cenário MAVSDK `takeoff_land`.

## Comandos de validação

```bash
bash robotics/ros2_ws/scripts/validate-workspace.sh
bash robotics/ros2_ws/scripts/validate-phase-3-container.sh
```
