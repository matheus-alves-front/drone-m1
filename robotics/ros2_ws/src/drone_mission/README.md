# drone_mission

Pacote de orquestracao de missao da Fase 4.

## Papel

- executar a state machine de missao
- coordenar arm, takeoff, hover, patrol, return-to-home e land
- expor status operacional da missao no dominio ROS 2
- manter fallback de abort separado de safety dedicado

## Runtime

- node principal: `mission_manager_node`
- controle de alto nivel: MAVSDK
- status de missao: `/drone/mission_status`
- comandos de missao: `/drone/mission_command`
