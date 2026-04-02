# ROS 2 Workspace

Workspace base do projeto simulation-first de autonomia de drone.

## Objetivo desta fase

Preparar o esqueleto mínimo para evoluir o middleware ROS 2 nas fases seguintes, sem assumir PX4, Gazebo ou bridges já operacionais.

## Estrutura inicial

- `src/drone_bringup/` para entrada de launch e composição futura do sistema
- `src/drone_msgs/` para mensagens e contratos do domínio
- `scripts/validate-workspace.sh` para smoke test estrutural do bootstrap

## Validação local

```bash
bash robotics/ros2_ws/scripts/validate-workspace.sh
```

## Observações

- Este workspace ainda não sobe nodes reais.
- `drone_msgs` está estruturado para virar o pacote de mensagens internas do domínio nas fases seguintes.
- `drone_bringup` existe apenas como ponto de entrada futuro para launch files.
