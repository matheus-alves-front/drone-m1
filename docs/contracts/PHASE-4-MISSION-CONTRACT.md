# PHASE-4-MISSION-CONTRACT.md

## Objetivo

Registrar o contrato tecnico da Fase 4 apos a validacao real da missao `patrol_basic`.

## Componentes da fase

- `robotics/ros2_ws/src/drone_mission/drone_mission/mission_manager_node.py`
- `robotics/ros2_ws/src/drone_mission/drone_mission/mission_executor.py`
- `robotics/ros2_ws/src/drone_mission/drone_mission/mission_state_machine.py`
- `robotics/ros2_ws/src/drone_mission/drone_mission/gateway.py`
- `robotics/ros2_ws/src/drone_bringup/config/drone_mission.yaml`
- `simulation/scenarios/patrol_basic.json`

## Sequencia validada

1. Esperar conectividade e posicao valida via `/drone/vehicle_state`
2. Enviar `arm` pelo dominio ROS 2 em `/drone/vehicle_command`
3. Confirmar aceitacao do arm por `VehicleCommandStatus`
4. Confirmar `VehicleState.armed=true` no mesmo fluxo de arm
5. Configurar altitude de decolagem e enviar `takeoff`
6. Confirmar subida real por `VehicleState.relative_altitude_m`
7. Executar `hover`
8. Publicar waypoints de patrulha com `goto`
9. Retornar para home quando `return_to_home=true`
10. Enviar `land`
11. Confirmar pouso real por `VehicleState`

## Fontes de verdade da fase

- Progresso de comando:
  - `drone_msgs/msg/VehicleCommandStatus`
  - origem real: `px4_msgs/msg/VehicleCommandAck`
- Progresso de voo:
  - `drone_msgs/msg/VehicleState`
  - origem real: topicos `/fmu/out/*` do PX4 via uXRCE-DDS
- Progresso de missao:
  - `drone_msgs/msg/MissionStatus`

## Decisoes operacionais validadas

- A aceitacao do arm continua vindo do ACK real do PX4 publicado em `VehicleCommandStatus`.
- O gateway ROS 2 da missao so libera `takeoff` depois de observar `VehicleState.armed=true`.
- As etapas de takeoff, patrulha, retorno e pouso continuam dependendo de telemetria real publicada em `VehicleState`.
- O baseline simulation-first da patrulha configura `NAV_DLL_ACT=0` e `COM_DISARM_PRFLT=60` no runtime do PX4 para evitar interferencia de data-link loss e auto-disarm prematuro durante a validacao oficial.

## Hardening arquitetural implementado

O hardening explicitado depois da conclusao funcional da fase foi implementado e validado:

- `VehicleCommandStatus` permanece como contrato transacional de comando
- `VehicleState` voltou a ser o gate canonico para confirmar `armed=true` antes do `takeoff`
- a validacao oficial da fase agora prova a sequencia:
  - baseline pre-arm desarmado
  - `VehicleCommandStatus.accepted=true`
  - seguido de `VehicleState.armed=true`

## Backlog tecnico associado

O registro historico do hardening fica em `docs/contracts/PHASE-4-ARCHITECTURE-HARDENING.md`.

## Criterio terminal da fase

A Fase 4 so conta como concluida quando o comando abaixo passa no ambiente oficial:

```bash
bash robotics/ros2_ws/scripts/validate-phase-4-container.sh
```

Esse fluxo precisa provar, no mesmo runtime:

- stack minimo da Fase 1 em execucao
- bringup ROS 2 com missao habilitada
- `arm` aceito por `VehicleCommandStatus`
- `VehicleState.armed=true` observado depois do ACK de `arm` no mesmo fluxo
- fase `patrol` observada em `/drone/mission_status`
- missao `completed` observada em `/drone/mission_status`
- voo e pouso observados em `/drone/vehicle_state`
