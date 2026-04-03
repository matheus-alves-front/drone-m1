# ROS 2 Workspace

Workspace base do projeto simulation-first de autonomia de drone.

## Objetivo desta etapa do workspace

Materializar a fronteira ROS 2 do projeto com mensagens de dominio, bringup executavel, bridge real com PX4, orquestracao de missao, safety manager e pipeline de percepcao validaveis em ambiente Humble/Jammy.

## Estrutura atual

- `src/drone_bringup/` para entrada de launch e params externalizados
- `src/drone_msgs/` para mensagens e contratos do dominio
- `src/drone_mission/` para orquestracao de missao e state machine de patrulha
- `src/drone_safety/` para politica de safety, fault injection e watchdogs
- `src/drone_perception/` para camera simulada, deteccao, tracking e heartbeat
- `src/drone_telemetry/` para bridge ROS 2 -> API de telemetria, envelopes e replay
- `src/drone_px4/` para a fronteira entre o dominio ROS 2 e o runtime real do PX4
- `src/px4_msgs/` para a trilha oficial de alinhamento com `release/1.16`
- `scripts/validate-workspace.sh` para validação estrutural e lógica local
- `scripts/validate-phase-3-container.sh` para build, test e launch reais em Humble/Jammy
- `scripts/validate-phase-4-container.sh` para provar a missao `patrol_basic` com stack real
- `scripts/validate-phase-5-container.sh` para provar safety real com tres cenarios oficiais
- `scripts/validate-phase-6-container.sh` para provar gate de visual lock e degradacao por `perception_timeout`
- `scripts/validate-phase-7.sh` para provar a camada de telemetria, persistencia e dashboard
- `scripts/ci/validate-phase-8.sh` para consolidar a maturidade final da simulacao no repositório

## Alinhamento de mensagens PX4

- `px4_msgs` segue a linha `release/1.16`
- o consumo runtime de PX4 continua encapsulado em `drone_px4`
- `drone_msgs` e o contrato estável consumido pelas camadas de dominio
- `VehicleCommandStatus` e o contrato de ACK do autopilot no dominio ROS 2

## Validação local

```bash
bash robotics/ros2_ws/scripts/validate-workspace.sh
```

## Validação real da Fase 3

```bash
bash robotics/ros2_ws/scripts/validate-phase-3-container.sh
```

## Validação real da Fase 4

```bash
bash robotics/ros2_ws/scripts/validate-phase-4-container.sh
```

## Validação real da Fase 5

```bash
bash robotics/ros2_ws/scripts/validate-phase-5-container.sh
```

## Validação real da Fase 6

```bash
bash robotics/ros2_ws/scripts/validate-phase-6-container.sh
```

## Validação oficial da Fase 7

```bash
bash robotics/ros2_ws/scripts/validate-phase-7.sh
```

## Validação terminal da Fase 8

```bash
bash scripts/ci/validate-phase-8.sh
```

## Observações

- O bringup atual sobe `px4_bridge_node` com integração real via `/fmu/out/*` e `/fmu/in/vehicle_command`.
- A validacao oficial da Fase 3 sobe `PX4 SITL`, `Gazebo Harmonic`, `Micro XRCE-DDS Agent` e o workspace ROS 2 no mesmo fluxo.
- O bridge publica `VehicleState` e `VehicleCommandStatus` a partir do runtime real do PX4.
- A validacao oficial da Fase 4 sobe o mesmo stack real e executa `patrol_basic` via `mission_manager_node`.
- A progressao de comandos da missao usa `VehicleCommandStatus` como contrato transacional, e `VehicleState` como gate canonico de estado para `armed`, voo e pouso.
- A validacao oficial da Fase 5 executa `geofence_breach`, `failsafe_gps_loss` e `failsafe_rc_loss` com `safety_manager_node`.
- O validador da Fase 5 reinicia o stack minimo por caso para evitar contaminacao entre cenarios.
- A validacao oficial da Fase 6 sobe o mesmo stack real e materializa `VisionDetection`, `TrackedObject`, `PerceptionEvent` e `PerceptionHeartbeat`.
- O gate de visual lock da missao usa estado persistente de `/drone/perception/tracked_object`, enquanto `/drone/perception/event` permanece como contrato de notificacao e observabilidade.
- A Fase 7 adiciona `telemetry_bridge_node` como consumidor de contratos de dominio ROS 2 e produtor de envelopes operacionais para a API de telemetria.
- O bridge de telemetria nao implementa missao nem safety; ele apenas normaliza e encaminha estado operacional para observabilidade.
- A Fase 8 consolida os validadores anteriores em uma suite final e nao muda a fronteira arquitetural do workspace.
