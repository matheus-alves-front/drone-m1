# Scenario Scripts

Diretorio reservado para wrappers de execucao de cenarios e smoke runs.

## Escopo real dos wrappers

- Os wrappers chamam a CLI Python em `packages/shared-py/src/drone_scenarios/`.
- A CLI MAVSDK materializa hoje apenas o cenário `takeoff_land`.
- `run_takeoff_land.sh` aponta explicitamente para `simulation/scenarios/takeoff_land.json`.
- `run_scenario.sh` aceita somente contratos compatíveis com a CLI MAVSDK e falha de forma explícita para cenários de domínio ROS 2.

## Mapeamento oficial por fase

- `takeoff_land`
  - execução direta: `bash scripts/scenarios/run_takeoff_land.sh`
  - prova oficial: `bash scripts/scenarios/validate-phase-2-container.sh`
- `patrol_basic`
  - prova oficial: `bash robotics/ros2_ws/scripts/validate-phase-4-container.sh`
- `geofence_breach`, `failsafe_gps_loss`, `failsafe_rc_loss`
  - prova oficial: `bash robotics/ros2_ws/scripts/validate-phase-5-container.sh`
- `perception_target_tracking`, `perception_timeout`
  - prova oficial: `bash robotics/ros2_ws/scripts/validate-phase-6-container.sh`
- suíte final de maturidade
  - prova oficial: `bash scripts/ci/validate-phase-8.sh`

## Contrato da Fase 2

- `validate-phase-2.sh` executa a validacao estrutural da Fase 2.
- `validate-phase-2-container.sh` executa o smoke test E2E da Fase 2 contra PX4 SITL + Gazebo Harmonic.
- O smoke test oficial precisa terminar com `status: completed` para a Fase 2 ser considerada concluida.
