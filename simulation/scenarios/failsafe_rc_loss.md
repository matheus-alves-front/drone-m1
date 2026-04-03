# failsafe_rc_loss

## Objetivo

Injetar perda de RC durante a patrulha e verificar que o safety aborta a missão e força `return_to_home`.

## Contrato executavel

- `simulation/scenarios/failsafe_rc_loss.json`

## Sinais observaveis

- `/drone/safety_status` publica `rule=rc_loss` e `action=return_to_home`
- `/drone/mission_status` termina em `aborted`
- `/drone/vehicle_state` observa retorno e pouso ao final

## Mecanismo de injecao

- o validador oficial espera a fase `patrol`
- depois publica `SafetyFault{fault_type=rc_loss, active=true}`

## Comando oficial

```bash
bash robotics/ros2_ws/scripts/validate-phase-5-container.sh
```
