# Mark 2 Software Architecture

## Arquitetura-alvo

```text
Operator UI / Machine API / MCP Surface
                 |
                 v
          Unified Control Plane
                 |
     ---------------------------------
     |               |               |
     v               v               v
 Capability Registry   Mission Runtime   Read Model
     |               |               |
     v               v               v
 Vehicle Runtime   Payload Runtime   Actuator Runtime
     |               |               |
     ---------------------------------
                 |
                 v
        Runtime Adapters / Drivers
                 |
         Simulation or Hardware
```

## Main layers

### 1. Unified Control Plane
Orquestra:
- actions
- sessions
- runs
- capability negotiation
- policy routing

### 2. Capability Registry
Declara:
- capability name
- version
- provider
- required vehicle family
- required payloads
- required actuators
- safety constraints

### 3. Mission Runtime
Executa planos com base em capabilities e constraints.

### 4. Vehicle Runtime
Abstrai o veículo base:
- aerial
- future ground
- future stationary

### 5. Payload Runtime
Gerencia módulos plugáveis acoplados ao veículo.

### 6. Actuator Runtime
Gerencia action surfaces de módulos que interagem fisicamente com o ambiente.

### 7. Read Model
Permanece como camada de observabilidade e replay.

### 8. Adapter Layer
Traduz o runtime lógico para:
- simulation adapters
- hardware adapters

## Architectural rule
O Mark 2 é a generalização do Mark 1, não uma negação do Mark 1.
