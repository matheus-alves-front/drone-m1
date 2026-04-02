# TESTING-AND-FAILURE-MODEL.md

## Objetivo

Definir como o projeto será validado em simulação e como falhas serão tratadas e testadas.

## Níveis de teste

1. Unit tests
2. Component tests
3. Integration tests
4. E2E simulation tests

## Cenários obrigatórios

- `takeoff_land`
- `patrol_basic`
- `failsafe_gps_loss`
- `failsafe_rc_loss`
- `geofence_breach`

## Falhas obrigatórias para simular

- perda de GPS
- perda de RC
- perda de data link
- violação de geofence
- travamento de node de percepção
- atraso excessivo no pipeline
- perda de comunicação com backend
