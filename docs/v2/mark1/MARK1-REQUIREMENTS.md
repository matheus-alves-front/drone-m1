# Mark 1 Requirements

## Functional Requirements

### FR-1 — Simulation lifecycle
O sistema deve permitir:
- iniciar simulação
- parar simulação
- consultar estado da simulação
- reiniciar uma sessão

### FR-2 — Scenario execution
O sistema deve permitir:
- listar cenários disponíveis
- executar cenário
- observar status de execução
- encerrar ou cancelar cenário

### FR-3 — Mission control
O sistema deve permitir:
- iniciar missão
- abortar missão
- resetar missão
- consultar status da missão

### FR-4 — Vehicle control
O sistema deve permitir:
- arm/disarm
- takeoff
- land
- return_to_home
- goto quando aplicável

### FR-5 — Safety control
O sistema deve permitir:
- injetar fault de teste
- limpar fault
- consultar safety status
- observar a reação do runtime

### FR-6 — Perception operation
O sistema deve permitir:
- observar estado do pipeline de percepção
- observar heartbeat
- observar detections/tracked object
- observar stream de câmera ou proxy correspondente quando disponível

### FR-7 — Telemetry and replay
O sistema deve permitir:
- consultar snapshot operacional
- consultar métricas
- consultar eventos
- listar runs
- abrir replay por run

### FR-8 — Capability discovery
O sistema deve expor quais ações e cenários estão disponíveis no runtime atual.

### FR-9 — Unified operator UI
A UI deve ser capaz de atuar como a central humana principal do sistema.

### FR-10 — Unified machine interface
O backend deve expor uma superfície de controle programática que possa ser adaptada futuramente para MCP.

## Non-Functional Requirements

### NFR-1 — Clear boundaries
Command side e read side devem ser separados.

### NFR-2 — Auditability
Toda ação relevante deve gerar rastro com `run_id`, timestamps, resultado e eventos.

### NFR-3 — Determinism where possible
Cenários e ações devem ter semântica clara de sucesso, falha, timeout e cancelamento.

### NFR-4 — Maintainability
O refactor deve reduzir, e não aumentar, o número de entrypoints mentais necessários.

### NFR-5 — Extensibility
As decisões do Mark 1 não podem bloquear payloads, actuators e capabilities futuras.

### NFR-6 — Environment clarity
Deve existir um caminho operacional oficial bem definido para:
- prova runtime
- operação visual local
- ambiente de desenvolvimento

### NFR-7 — Safety separation
Safety não pode ser acoplado ao frontend nem à IA.

### NFR-8 — Documentation completeness
A documentação do Mark 1 deve ser suficiente para:
- Codex implementar
- outro desenvolvedor operar
- outro desenvolvedor auditar

## Acceptance Criteria Macro

O Mark 1 está pronto quando:
1. existe um control plane unificado
2. existe uma UI controladora
3. cenários e missão podem ser operados por uma superfície de produto única
4. faults podem ser injetados de forma coerente
5. telemetria e replay continuam auditáveis
6. a validação final do Mark 1 passa de ponta a ponta
