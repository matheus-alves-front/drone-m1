# MONOREPO-STRUCTURE.md

## Princípio

O monorepo deve organizar:
- documentação
- código de robótica
- assets de simulação
- scripts de orquestração
- backend
- dashboard
- dependências vendoradas
- tooling para IA e code agents

## Estrutura sugerida

```text
drone-autonomy/
  README.md
  AGENTS.md
  docs/
  .agents/
  .codex/
    skills/
  third_party/
    PX4-Autopilot/
  robotics/
    ros2_ws/
      src/
        px4_msgs/
        drone_msgs/
        drone_bringup/
        drone_px4/
        drone_mission/
        drone_safety/
        drone_perception/
        drone_telemetry/
  simulation/
    gazebo/
      worlds/
      models/
      resources/
    scenarios/
  scripts/
    sim/
    scenarios/
    tooling/
  services/
    telemetry-api/
  apps/
    dashboard/
  packages/
    shared-ts/
    shared-py/
  .github/
    workflows/
  .devcontainer/
```
