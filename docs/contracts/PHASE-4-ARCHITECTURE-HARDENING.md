# PHASE-4-ARCHITECTURE-HARDENING.md

## Objetivo

Registrar o hardening arquitetural que fortaleceu a semantica entre `VehicleCommandStatus` e `VehicleState` depois da conclusao funcional da Fase 4.

## Problema original

O fluxo validado da Fase 4 usa duas fontes reais diferentes para perguntas diferentes:

- `VehicleCommandStatus`
  - confirma se o PX4 aceitou ou rejeitou um comando
- `VehicleState`
  - confirma o estado observado do veiculo durante voo, patrulha e pouso

Isso passou no E2E funcional inicial, mas o dominio ainda nao estava no formato mais forte possivel para a etapa de `arm`, porque a progressao do arm nao dependia de `VehicleState.armed=true` como gate obrigatorio.

## Estado funcional anterior

- `arm`
  - gate primario: `VehicleCommandStatus.accepted=true`
- `takeoff`
  - gate primario: `VehicleState.relative_altitude_m`
- `patrol`
  - gate primario: `VehicleState` e `MissionStatus`
- `return-to-home`
  - gate primario: `VehicleState` e `MissionStatus`
- `land`
  - gate primario: `VehicleState.landed=true`

## Forma arquitetural desejada

### Papel de `VehicleCommandStatus`

- manter o contrato transacional de comando
- responder:
  - o PX4 aceitou?
  - rejeitou?
  - retornou `TEMPORARILY_REJECTED`, `DENIED` ou `FAILED`?

### Papel de `VehicleState`

- manter o contrato canonico de estado do veiculo no dominio
- responder:
  - conectado
  - armado
  - landed
  - nav_state
  - failsafe
  - posicao e altitude validas

### Estado alvo

O fluxo desejado para `arm` no dominio e:

1. enviar `arm`
2. observar `VehicleCommandStatus.accepted=true`
3. observar `VehicleState.armed=true`
4. somente depois liberar `takeoff`

## Implementacao realizada

- O gateway ROS 2 da missao voltou a exigir `VehicleState.armed=true` antes de liberar a etapa de `takeoff`
- O bridge `drone_px4` permaneceu como fronteira canonica de estado, com `armed` vindo da telemetria real de `vehicle_status` e fallback de `vehicle_control_mode` apenas para degradacao controlada
- A validacao oficial da Fase 4 passou a impor uma barreira temporal depois do pre-arm desarmado para provar:
  - `VehicleCommandStatus.accepted=true`
  - seguido de `VehicleState.armed=true`
  - no mesmo fluxo observado

## Estado atual

- `VehicleCommandStatus` permanece como contrato transacional para aceitacao ou rejeicao de comandos
- `VehicleState` voltou a ser o estado canonico para destravar a transicao `arm -> takeoff`
- O validador oficial rejeita estados antigos por timestamp e exige a sequencia `pre-arm desarmado -> ACK -> armed`

## Resultado

- prioridade original: alta
- estado: implementado
- bloqueio formal restante: nao
- recomendacao atual: manter esse contrato canonico nas fases seguintes para que safety se apoie em uma semantica de estado uniforme
