# PX4-Autopilot Submodule

## Objetivo

Registrar a forma oficial de vendorizar o PX4 no monorepo.

## Fonte oficial

- Repositorio: `https://github.com/PX4/PX4-Autopilot.git`
- Tipo: git submodule
- Path alvo: `third_party/PX4-Autopilot/`
- Tag oficial: `v1.16.1`

## Compatibilidade exigida

- `px4_msgs` deve seguir a linha `release/1.16`.
- ROS 2 baseline: Humble.
- Devcontainer baseline: Ubuntu 22.04.
- Simulador baseline: Gazebo Harmonic.

## Observacao

Este manifesto existe para abrir a Fase 1 com clareza. A vendorizaçao real depende de o repositório atual estar em um estado Git compativel com submodules.
