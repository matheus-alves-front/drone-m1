# drone_bringup

Pacote de entrada do grafo ROS 2 das Fases 3, 4, 5 e 6.

## Papel

- concentrar os launch files do sistema
- descrever a ordem de subida dos nodes
- manter parâmetros externos do stack ROS 2

## Conteúdo atual

- `drone_bringup/launch/bringup.launch.py`
- `config/drone_px4.yaml`
- `config/drone_mission.yaml`
- `config/drone_safety.yaml`
- `config/drone_perception.yaml`

## Ordem de subida atual

1. Carregar parâmetros externos do `drone_px4`
2. Subir `px4_bridge_node`
3. Assinar `px4_msgs` reais expostos por `/fmu/out/*`
4. Publicar `/drone/vehicle_state`
5. Aceitar `/drone/vehicle_command` e encaminhar para `/fmu/in/vehicle_command`
6. Opcionalmente subir `mission_manager_node`
7. Opcionalmente subir `camera_input_node`, `object_detector_node` e `tracker_node`
8. Opcionalmente subir `safety_manager_node`
9. Expor `MissionStatus`, `SafetyStatus`, `TrackedObject` e `PerceptionHeartbeat` no dominio

## Observação

O bringup estabelece a fronteira do middleware ROS 2 com integracao real em runtime com PX4 via `px4_msgs` e uXRCE-DDS, mantendo mission, safety e perception como nodes separados e configurados por parametros externos.
