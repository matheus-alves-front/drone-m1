# takeoff_land

## Objetivo

Executar o smoke scenario oficial da Fase 2 com MAVSDK: arm, takeoff, hover, waypoint relativo simples e land.

## Pre-requisitos

- `simulation/gazebo/worlds/harmonic_minimal.sdf` presente
- Baseline oficial definido para Gazebo Harmonic e ROS 2 Humble
- `simulation/scenarios/takeoff_land.json` presente como manifesto executavel
- Stack minimo da Fase 1 operacional
- `python3 -m drone_scenarios` disponivel via `PYTHONPATH=packages/shared-py/src`

## Sequencia esperada

1. Conectar ao autopilot em simulacao.
2. Aguardar readiness com `global position` e `home position`.
3. Armar o veiculo.
4. Configurar altitude de decolagem.
5. Executar takeoff.
6. Sustentar hover por alguns segundos.
7. Navegar para um waypoint relativo curto.
8. Executar land.

## Sinais observaveis

- O manifesto JSON pode ser consumido pelo runner MAVSDK.
- O runner diferencia falha de conexao, timeout e falha de assert.
- A telemetria confirma altitude positiva apos takeoff, chegada ao waypoint e retorno para `in_air = false` ao final.

## Criterio de sucesso

- O cenario consegue mandar o veiculo de armamento ate pouso.
- Os asserts minimos de telemetria passam em arm, takeoff, hover, waypoint e land.

## Criterio de falha

- O runner nao consegue conectar no autopilot.
- O comando de acao falha.
- O waypoint nao e alcancado.
- Algum assert minimo de telemetria falha.
