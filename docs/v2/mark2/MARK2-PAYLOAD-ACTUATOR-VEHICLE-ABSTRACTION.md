# Mark 2 Payload, Actuator and Vehicle Abstraction

## Vehicle abstraction
Representa a base de mobilidade.

### Exemplos futuros
- `vehicle.air.drone`
- `vehicle.ground.mobile_base`
- `vehicle.stationary.cell`

## Payload abstraction
Representa um módulo acoplado ao veículo.

### Exemplos futuros
- camera payload
- display payload
- speaker payload
- delivery box
- sensing pod

### Lifecycle esperado
- discover
- mount
- configure
- health
- enable
- disable
- unmount

## Actuator abstraction
Representa um componente que age fisicamente no ambiente.

### Exemplos futuros
- robotic arm
- gimbal
- sprayer
- cleaning head
- gripper

### Lifecycle esperado
- command
- health
- guardrails
- stop
- recover

## Important separation
Payload não é automaticamente actuator.  
Actuator não é automaticamente vehicle.  
Essas camadas precisam ser independentes.

## Why this matters now
Se o Mark 1 for codado de forma muito drone-only, a expansão para payloads/actuators vira refactor doloroso.
