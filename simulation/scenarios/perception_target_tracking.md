# perception_target_tracking

## Objetivo

Validar o pipeline real da Fase 6:

- feed de câmera simulada publicado em ROS 2
- ingestão por `camera_input_node`
- detecção em `object_detector_node`
- tracking e heartbeat em `tracker_node`
- reação de safety quando o feed some e o heartbeat entra em timeout

## Sequência validada

1. subir `PX4 SITL + Gazebo Harmonic + Micro XRCE-DDS Agent`
2. subir `drone_bringup` com mission, safety e perception habilitados
3. publicar feed sintético em `/simulation/camera/image_raw`
4. observar:
   - `/drone/perception/detection`
   - `/drone/perception/tracked_object`
   - `/drone/perception/event`
   - `/drone/perception_heartbeat`
5. iniciar `patrol_basic`
6. desligar o feed da câmera
7. observar `perception_timeout` em `/drone/safety_status`
8. confirmar `mission abort` e pouso final do veículo
