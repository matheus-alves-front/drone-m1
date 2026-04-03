# PHASE-5-SAFETY-CONTRACT.md

## Objetivo

Registrar o contrato tecnico da Fase 5 apos a validacao real do safety manager contra o stack oficial de simulacao.

## Componentes da fase

- `robotics/ros2_ws/src/drone_safety/drone_safety/safety_manager_node.py`
- `robotics/ros2_ws/src/drone_safety/drone_safety/rules.py`
- `robotics/ros2_ws/src/drone_safety/drone_safety/contracts.py`
- `robotics/ros2_ws/src/drone_bringup/config/drone_safety.yaml`
- `robotics/ros2_ws/src/drone_bringup/drone_bringup/launch/bringup.launch.py`
- `robotics/ros2_ws/src/drone_msgs/msg/SafetyFault.msg`
- `robotics/ros2_ws/src/drone_msgs/msg/SafetyStatus.msg`
- `robotics/ros2_ws/src/drone_msgs/msg/PerceptionHeartbeat.msg`
- `simulation/scenarios/geofence_breach.json`
- `simulation/scenarios/failsafe_gps_loss.json`
- `simulation/scenarios/failsafe_rc_loss.json`

## Topicos de dominio materializados

- `/drone/vehicle_state`
- `/drone/mission_status`
- `/drone/safety_fault`
- `/drone/perception_heartbeat`
- `/drone/safety_status`
- `/drone/mission_command`
- `/drone/vehicle_command`

## Regras validadas

- `geofence_breach`
- `gps_loss`
- `rc_loss`
- `data_link_loss`
- `perception_timeout`
- `perception_latency`
- `px4_failsafe_active`

## Fontes de verdade da fase

- Telemetria real do veiculo:
  - `drone_msgs/msg/VehicleState`
  - origem real: `px4_msgs` via `/fmu/out/*` e uXRCE-DDS
- Progresso de missao:
  - `drone_msgs/msg/MissionStatus`
- Eventos de fault injection e watchdog:
  - `drone_msgs/msg/SafetyFault`
  - `drone_msgs/msg/PerceptionHeartbeat`
- Decisao consolidada de safety:
  - `drone_msgs/msg/SafetyStatus`

## Janela de monitoramento validada

- O safety manager nao toma decisoes durante o bootstrap da missao ainda no solo.
- A politica de safety passa a monitorar o runtime quando:
  - o veiculo esta armado
  - ou a missao esta ativa e o veiculo ja nao esta mais pousado

Essa decisao evita aborts falsos por ruído de bootstrap sem misturar safety com a state machine de missao.

## Sequencia validada no ambiente oficial

### `geofence_breach`

1. Subir `PX4 SITL + Gazebo Harmonic + Micro XRCE-DDS Agent`
2. Subir `drone_bringup` com `mission_manager_node` e `safety_manager_node`
3. Iniciar `patrol_basic`
4. Confirmar `arm` aceito por `VehicleCommandStatus`
5. Confirmar `VehicleState.armed=true`
6. Detectar violacao de geofence por telemetria real
7. Publicar `/drone/safety_status` com `rule=geofence_breach` e `action=return_to_home`
8. Publicar `abort` para a missao
9. Publicar `return_to_home` e depois `land` no dominio de veiculo
10. Confirmar `/drone/mission_status` em `aborted`
11. Confirmar pouso por `/drone/vehicle_state`

### `failsafe_gps_loss`

1. Subir stack minimo isolado
2. Iniciar `patrol_basic`
3. Esperar fase `patrol`
4. Injetar `SafetyFault` com `fault_type=gps_loss`
5. Publicar `/drone/safety_status` com `rule=gps_loss` e `action=land`
6. Abortar a missao
7. Enviar `land`
8. Confirmar missao abortada e pouso observado

### `failsafe_rc_loss`

1. Subir stack minimo isolado
2. Iniciar `patrol_basic`
3. Esperar fase `patrol`
4. Injetar `SafetyFault` com `fault_type=rc_loss`
5. Publicar `/drone/safety_status` com `rule=rc_loss` e `action=return_to_home`
6. Abortar a missao
7. Enviar `return_to_home` e concluir com `land`
8. Confirmar missao abortada e pouso observado

## Isolamento oficial do validador

O validador oficial da Fase 5 reinicia o stack de simulacao por caso.

- Cada um dos cenarios `geofence_breach`, `failsafe_gps_loss` e `failsafe_rc_loss` sobe seu proprio runtime `PX4 + Gazebo + XRCE`.
- O bringup ROS 2 tambem sobe do zero por caso.
- Logs e artefatos ficam separados por caso em `.sim-logs/phase-5-container/<cenario>/`.

Esse isolamento evita contaminacao entre cenarios e faz parte do contrato de qualidade da fase.

## Separacao de responsabilidades

- `drone_mission` nao implementa politica de safety
- `drone_safety` nao implementa state machine de patrulha
- `drone_px4` continua sendo a fronteira com o runtime real do PX4
- `drone_bringup` apenas compoe nodes e parametros

## Criterio terminal da fase

A Fase 5 so conta como concluida quando o comando abaixo passa no ambiente oficial:

```bash
bash robotics/ros2_ws/scripts/validate-phase-5-container.sh
```

Esse fluxo precisa provar, em runtime real:

- `geofence_breach` com resposta `return_to_home`
- `gps_loss` com resposta `land`
- `rc_loss` com resposta `return_to_home`
- `mission abort` observado no dominio
- pouso observado por `VehicleState`
