# Scenarios

Diretorio reservado para cenarios de simulacao, smoke tests e contratos de execucao.

## Intencao

- Descrever o que deve acontecer na simulação.
- Servir como contrato entre o runner MAVSDK e os objetivos do projeto.
- Registrar criterio de aceite, falhas esperadas e dependencias.

## Estrutura esperada

- `takeoff_land.json`
- `takeoff_land.md`
- `patrol_basic.json`
- `failsafe_gps_loss.json`
- `failsafe_gps_loss.md`
- `failsafe_rc_loss.json`
- `failsafe_rc_loss.md`
- `geofence_breach.json`
- `geofence_breach.md`
- `perception_target_tracking.json`
- `perception_target_tracking.md`

## Cenário inicial

- `takeoff_land.md` documenta o cenário inicial de smoke test.
- `takeoff_land.json` e o contrato executavel oficial da Fase 2.
- O cenario cobre arm, takeoff, hover, waypoint e land sem introduzir dependencias de ROS 2.
- O manifesto JSON existe para o runner MAVSDK, enquanto o `.md` preserva a explicacao humana do cenario.
- `patrol_basic.json` e o contrato oficial de missao da Fase 4.
- `geofence_breach`, `failsafe_gps_loss` e `failsafe_rc_loss` compoem a prova oficial da Fase 5.
- A validacao oficial da Fase 5 executa esses tres cenarios com runtime isolado por caso.
- `perception_target_tracking` registra o contrato humano e executavel da Fase 6.
- A validacao oficial da Fase 6 prova `visual_lock_gate` e `perception_timeout` com camera sintetica e runtime isolado por caso.

## Matriz consolidada da Fase 8

- `takeoff_land`
  - prova oficial: `bash scripts/scenarios/validate-phase-2-container.sh`
- `patrol_basic`
  - prova oficial: `bash robotics/ros2_ws/scripts/validate-phase-4-container.sh`
- `geofence_breach`
  - prova oficial: `bash robotics/ros2_ws/scripts/validate-phase-5-container.sh`
- `failsafe_gps_loss`
  - prova oficial: `bash robotics/ros2_ws/scripts/validate-phase-5-container.sh`
- `failsafe_rc_loss`
  - prova oficial: `bash robotics/ros2_ws/scripts/validate-phase-5-container.sh`
- `perception_timeout`
  - prova oficial: `bash robotics/ros2_ws/scripts/validate-phase-6-container.sh`

## Suite final de maturidade

```bash
bash scripts/ci/validate-phase-8.sh
```

## Contrato minimo de um cenario

- Nome e objetivo
- Contrato de conexao
- Parametros de voo e tolerancias
- Pre-requisitos
- Sinais observaveis
- Criterio de sucesso
- Criterio de falha

## Comando oficial da Fase 5

```bash
bash robotics/ros2_ws/scripts/validate-phase-5-container.sh
```

## Comando oficial da Fase 6

```bash
bash robotics/ros2_ws/scripts/validate-phase-6-container.sh
```
