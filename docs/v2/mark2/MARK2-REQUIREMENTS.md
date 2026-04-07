# Mark 2 Requirements

## Functional requirements planned

### MR2-FR-1 — Vehicle family support
A plataforma deve conseguir suportar mais de uma família de veículo sem refactor destrutivo.

### MR2-FR-2 — Payload lifecycle
A plataforma deve modelar payloads plugáveis com:
- mount
- unmount
- health
- capabilities
- constraints

### MR2-FR-3 — Actuator lifecycle
A plataforma deve modelar actuators adicionais com:
- command surface
- safety constraints
- state reporting

### MR2-FR-4 — Capability registry
A plataforma deve listar capabilities disponíveis, versões, dependências e riscos.

### MR2-FR-5 — Machine interface for AI/MCP
A plataforma deve expor actions/capabilities de forma limpa para futura camada MCP.

### MR2-FR-6 — Mission planning extensível
Missões devem poder declarar:
- required capabilities
- required payloads
- constraints
- fallback policies
- risk profile

### MR2-FR-7 — Hardware readiness
A plataforma deve separar:
- simulation drivers
- hardware drivers
- runtime policies
- safety gates

## Non-functional requirements planned
- plugin-friendly
- hardware-aware
- vehicle-agnostic where possible
- safety-governed
- auditable
- versioned contracts
