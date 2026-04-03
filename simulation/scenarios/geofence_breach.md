# geofence_breach

## Objetivo

Executar a patrulha com um geofence propositalmente apertado e verificar que o safety detecta a violação usando telemetria real.

## Contrato executavel

- `simulation/scenarios/geofence_breach.json`

## Sinais observaveis

- `/drone/safety_status` publica `rule=geofence_breach` e `action=return_to_home`
- `/drone/mission_status` termina em `aborted`
- `/drone/vehicle_state` observa retorno e pouso ao final

## Mecanismo de injecao

- o validador oficial sobe o `safety_manager_node` com `geofence_max_distance_m` apertado
- a violacao e detectada por telemetria real durante a patrulha

## Comando oficial

```bash
bash robotics/ros2_ws/scripts/validate-phase-5-container.sh
```
