# PHASE-6-PERCEPTION-CONTRACT.md

## Objetivo

Registrar o contrato tecnico da Fase 6 apos a validacao real do pipeline de percepcao no stack oficial de simulacao.

## Componentes da fase

- `robotics/ros2_ws/src/drone_perception/drone_perception/camera_input_node.py`
- `robotics/ros2_ws/src/drone_perception/drone_perception/object_detector_node.py`
- `robotics/ros2_ws/src/drone_perception/drone_perception/tracker_node.py`
- `robotics/ros2_ws/src/drone_mission/drone_mission/mission_manager_node.py`
- `robotics/ros2_ws/src/drone_bringup/config/drone_perception.yaml`
- `robotics/ros2_ws/src/drone_bringup/config/drone_mission.yaml`
- `robotics/ros2_ws/src/drone_msgs/msg/VisionDetection.msg`
- `robotics/ros2_ws/src/drone_msgs/msg/TrackedObject.msg`
- `robotics/ros2_ws/src/drone_msgs/msg/PerceptionEvent.msg`
- `robotics/ros2_ws/src/drone_msgs/msg/PerceptionHeartbeat.msg`
- `robotics/ros2_ws/scripts/publish_sim_camera_stream.py`
- `robotics/ros2_ws/scripts/validate-phase-6-container.sh`
- `simulation/scenarios/perception_target_tracking.json`

## Topicos de dominio materializados

- `/simulation/camera/image_raw`
- `/drone/perception/preprocessed_image`
- `/drone/perception/detection`
- `/drone/perception/tracked_object`
- `/drone/perception/event`
- `/drone/perception_heartbeat`
- `/drone/mission_status`
- `/drone/safety_status`

## Fontes de verdade da fase

- Estado persistente de lock visual:
  - `drone_msgs/msg/TrackedObject`
  - origem: `tracker_node`
- Notificacao de transicoes visuais:
  - `drone_msgs/msg/PerceptionEvent`
  - origem: `object_detector_node` e `tracker_node`
- Watchdog de saude do pipeline:
  - `drone_msgs/msg/PerceptionHeartbeat`
  - origem: `tracker_node`
- Progresso de missao e degradacao:
  - `drone_msgs/msg/MissionStatus`
  - `drone_msgs/msg/SafetyStatus`

## Decisoes operacionais validadas

- O gate de missao para `visual lock` usa estado persistente de tracking em `TrackedObject`, nao um evento transitorio.
- `PerceptionEvent` continua sendo o contrato de notificacao para observabilidade e integracoes leves do dominio.
- Mission e safety continuam desacoplados de frame bruto e de detalhes de OpenCV.
- O timeout de percepcao continua responsabilidade do `drone_safety`, a partir de `PerceptionHeartbeat`.

## Sequencia validada no ambiente oficial

### `visual_lock_gate`

1. Subir `PX4 SITL + Gazebo Harmonic + Micro XRCE-DDS Agent`
2. Subir `drone_bringup` com mission, perception e safety
3. Confirmar conectividade e `arm`
4. Confirmar `hover` com detalhe `waiting for visual lock before patrol`
5. Iniciar o feed sintetico em `/simulation/camera/image_raw`
6. Confirmar `PerceptionHeartbeat.healthy=true`
7. Confirmar `VisionDetection.detected=true`
8. Confirmar `TrackedObject.tracked=true`
9. Confirmar transicao posterior para `MissionStatus.phase=patrol`

### `perception_timeout`

1. Subir stack minimo isolado
2. Iniciar o feed sintetico e confirmar heartbeat saudavel
3. Confirmar `TrackedObject.tracked=true`
4. Iniciar `patrol_basic`
5. Confirmar `MissionStatus.phase=patrol`
6. Parar o feed sintetico
7. Confirmar `SafetyStatus.rule=perception_timeout` e `action=land`
8. Confirmar `mission_abort_requested=true` e `vehicle_command_sent=true`
9. Confirmar `MissionStatus.aborted=true`
10. Confirmar pouso observado por `VehicleState`

## Isolamento oficial do validador

- O validador oficial da Fase 6 reinicia o stack minimo por caso.
- `visual_lock_gate` e `perception_timeout` usam runtimes isolados de `PX4 + Gazebo + XRCE`.
- Logs e artefatos ficam segregados em `.sim-logs/phase-6-container/<caso>/`.

## Criterio terminal da fase

A Fase 6 so conta como concluida quando o comando abaixo passa no ambiente oficial:

```bash
bash robotics/ros2_ws/scripts/validate-phase-6-container.sh
```

Esse fluxo precisa provar, em runtime real:

- gate de missao em `hover` aguardando visual lock
- lock visual real via `TrackedObject`
- avanço posterior para `patrol`
- `perception_timeout` disparando `SafetyStatus`
- `mission abort` e pouso observados no dominio
