# ROBOTICS-ROS2-WORKSPACE-PX4-MSGS.md

## Objetivo

Registrar a trilha de alinhamento inicial de `px4_msgs` no workspace ROS 2, sem avançar para a Fase 3 completa.

## Baseline oficial

- PX4-Autopilot: `v1.16.1`
- Linha de mensagens: `release/1.16`
- ROS 2: `Humble`
- Sistema de referencia: `Ubuntu 22.04`

## Contrato

- `px4_msgs` deve permanecer alinhado com a linha `release/1.16`.
- O workspace ainda nao deve ser tratado como funcional completo nesta fase.
- O manifesto em `robotics/ros2_ws/src/px4_msgs/PINNING.md` serve como contrato estrutural e documental.

## Validação

- `bash robotics/ros2_ws/scripts/validate-workspace.sh`
- `rg -n "release/1.16|v1.16.1" robotics/ros2_ws docs`

## Limite

Este documento nao substitui a Fase 3. Ele apenas prepara a trilha de sincronizacao para o pacote `px4_msgs`.
