# failsafe_gps_loss

## Objetivo

Injetar perda de GPS durante a patrulha e verificar que o safety aborta a missão e força `land`.

## Contrato executavel

- `simulation/scenarios/failsafe_gps_loss.json`

## Sinais observaveis

- `/drone/safety_status` publica `rule=gps_loss` e `action=land`
- `/drone/mission_status` termina em `aborted`
- `/drone/vehicle_state` observa pouso ao final

## Mecanismo de injecao

- o validador oficial espera a fase `patrol`
- depois publica `SafetyFault{fault_type=gps_loss, active=true}`

## Comando oficial

```bash
bash robotics/ros2_ws/scripts/validate-phase-5-container.sh
```
