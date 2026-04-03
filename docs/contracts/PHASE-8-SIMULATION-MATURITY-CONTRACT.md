# PHASE-8-SIMULATION-MATURITY-CONTRACT.md

## Objetivo

Registrar o contrato tecnico da Fase 8, que consolida o projeto como stack de simulacao madura, repetivel e auditavel.

## Entregas consolidadas pela fase

- `scripts/ci/validate-phase-8.sh`
- `.github/workflows/simulation-maturity.yml`
- `docs/runbooks/SIMULATION-OPERATIONS-TROUBLESHOOTING.md`
- `docs/decisions/HARDWARE-MIGRATION-CRITERIA.md`
- consolidacao da matriz de cenarios em `simulation/scenarios/README.md`

## Suite oficial consolidada

### Validacoes locais

- `bash scripts/bootstrap/validate-phase-0.sh`
- `python3 -m unittest scripts.tooling.tests.test_phase0_structure`
- `bash robotics/ros2_ws/scripts/validate-workspace.sh`
- `bash scripts/sim/validate-phase-1.sh`
- `bash scripts/scenarios/validate-phase-2.sh`
- `bash robotics/ros2_ws/scripts/validate-phase-4.sh`
- `bash robotics/ros2_ws/scripts/validate-phase-5.sh`
- `bash robotics/ros2_ws/scripts/validate-phase-6.sh`
- `bash robotics/ros2_ws/scripts/validate-phase-7.sh`

### Validacoes runtime

- `bash scripts/sim/validate-phase-1-container.sh`
- `bash scripts/scenarios/validate-phase-2-container.sh`
- `bash robotics/ros2_ws/scripts/validate-phase-4-container.sh`
- `bash robotics/ros2_ws/scripts/validate-phase-5-container.sh`
- `bash robotics/ros2_ws/scripts/validate-phase-6-container.sh`

## Cobertura consolidada dos cenarios obrigatorios

- `takeoff_land`
  - prova oficial: Fase 2
- `patrol_basic`
  - prova oficial: Fase 4
- `failsafe_gps_loss`
  - prova oficial: Fase 5
- `failsafe_rc_loss`
  - prova oficial: Fase 5
- `geofence_breach`
  - prova oficial: Fase 5

## Cobertura consolidada dos modos de falha

- `violacao de geofence`
  - prova oficial runtime: Fase 5
- `perda de GPS`
  - prova oficial runtime: Fase 5
- `perda de RC`
  - prova oficial runtime: Fase 5
- `perda de data link`
  - prova local de componente: `drone_safety/test/test_rules.py`
- `travamento do pipeline de percepcao`
  - materializado como perda de heartbeat e timeout de percepcao
  - prova runtime: Fase 6 via `perception_timeout`
- `atraso excessivo no pipeline`
  - prova local de componente: `drone_safety/test/test_rules.py`
- `perda de comunicacao com backend`
  - prova local de componente: `drone_telemetry/test/test_transport.py`

## CI da fase

O workflow `Simulation Maturity` roda em tres camadas:

1. `local-quality`
   - bootstrap, workspace, fases locais e frontend/backend
2. `runtime-smoke`
   - stack minimo e `takeoff_land`
3. `runtime-autonomy`
   - `patrol_basic`, safety e percepcao

## Limites arquiteturais mantidos

- PX4 continua dono do voo.
- ROS 2 continua middleware principal.
- dashboard continua somente apresentacao.
- nenhum artefato da Fase 8 declara prontidao para hardware.

## Criterio terminal da fase

A Fase 8 so conta como concluida quando:

```bash
bash scripts/ci/validate-phase-8.sh
```

passa com sucesso, e a workflow `Simulation Maturity` representa o mesmo contrato em CI.
