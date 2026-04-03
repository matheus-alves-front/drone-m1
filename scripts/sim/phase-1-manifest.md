# Phase 1 Manifest

## Objetivo

Consolidar a baseline da Fase 1 ate a subida real e repetivel da simulacao minima.

## Baseline oficial

- PX4-Autopilot: `v1.16.1`
- `px4_msgs`: linha `release/1.16`
- ROS 2: Humble
- Sistema de referencia: Ubuntu 22.04
- Simulador: Gazebo Harmonic
- Micro XRCE-DDS Agent: `v2.4.3`

## Entradas esperadas da Fase 1

- `third_party/PX4-Autopilot/` como git submodule real
- `simulation/gazebo/worlds/` com o primeiro world minimo
- `simulation/gazebo/models/` com o primeiro modelo base
- `simulation/gazebo/resources/` com recursos versionados para o world base
- `simulation/scenarios/` com o primeiro smoke test documentado

## Validação pretendida

- Verificar que os artefatos minimos da simulacao existem.
- Preparar o fluxo oficial de submodule para o PX4.
- Registrar a ordem oficial de subida do stack minimo.
- Executar `scripts/sim/start.sh --check` e `scripts/sim/stop.sh --check`.
- Executar `scripts/sim/validate-phase-1-container.sh` em Ubuntu 22.04 compatível com Gazebo Harmonic.
- Nao marcar a fase como concluida antes da subida real de PX4 SITL + Gazebo Harmonic.
