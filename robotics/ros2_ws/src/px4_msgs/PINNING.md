# px4_msgs pinning

## Baseline oficial

- PX4-Autopilot: `v1.16.1`
- Linha de mensagens: `release/1.16`
- Commit upstream validado: `392e831c1f659429ca83902e66820d7094591410`
- ROS 2: `Humble`
- Sistema de referencia: `Ubuntu 22.04`

## Regra

O pacote `robotics/ros2_ws/src/px4_msgs/` deve permanecer alinhado com a mesma família de release do PX4 vendorizado em `third_party/PX4-Autopilot/`.

## Observação

Este diretório contém o pacote oficial `px4_msgs` da release compatível com o PX4 do projeto, acrescido deste manifesto local de pinagem.

Para manter a validação oficial em container reproduzível nas Fases 3 e 4, o `CMakeLists.txt` do monorepo gera apenas o subconjunto de interfaces atualmente usado por `drone_px4`. O source tree continua alinhado à `release/1.16`, e a ampliação do subconjunto deve seguir a evolução real da arquitetura.
