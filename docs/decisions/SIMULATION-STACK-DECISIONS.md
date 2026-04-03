# SIMULATION-STACK-DECISIONS.md

## Baseline oficial

| Camada | Decisao oficial | Nota operacional |
|---|---|---|
| Autopilot | `PX4-Autopilot v1.16.1` como baseline | Deve ser vendorado como git submodule em `third_party/PX4-Autopilot/`. |
| Mensagens PX4/ROS 2 | `px4_msgs` na linha `release/1.16` | Deve permanecer alinhado com a familia de mensagens do PX4 escolhido. |
| Middleware | `ROS 2 Humble` | Ubuntu 22.04 e a referencia de desenvolvimento no devcontainer. |
| Simulador | `Gazebo Harmonic` | Gazebo Classic nao faz parte do baseline oficial. |
| Bridge | `Micro XRCE-DDS Agent v2.4.3` | Instalacao standalone from source, rodando como processo externo ao workspace. |
| Controle de cenarios | `MAVSDK` | A direcao preferida para a Fase 2 e uma CLI Python com logica reutilizavel. |
| Percepcao | `OpenCV` primeiro | Isaac ROS permanece opcional e apenas quando houver motivo claro de aceleracao. |

## Implicações de integração

- `px4_msgs` e o firmware do PX4 devem permanecer na mesma linha de mensagens sempre que possivel.
- Se houver divergencia entre a definicao de mensagens do firmware e do workspace ROS 2, a traducao de mensagens deve ser tratada explicitamente.
- O stack deve preservar a separação entre simulador externo, autopilot, middleware e autonomia.
- A Fase 1 prepara o baseline, os contratos e os artefatos minimos, mas nao deve fingir que a orquestração completa ja esta pronta.
