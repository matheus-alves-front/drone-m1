# Mark 1 Scope

## Objetivo
Construir a primeira versão da **Drone Control Platform**, unificando as superfícies de controle do sistema atual.

## Entram no escopo

### 1. Control Plane
- API de controle
- actions formais
- run/session management
- orchestration do lifecycle da simulação
- orchestration de cenários e missão

### 2. Operator UI
- console operacional
- controles de simulação
- controles de cenário
- controles de missão
- controles de safety fault injection
- estado consolidado
- telemetria e replay
- visão de câmera/percepção quando disponível

### 3. Unified Action Model
- ações de simulação
- ações de veículo
- ações de missão
- ações de safety
- ações de cenário
- leitura de capabilities disponíveis

### 4. Unified Scenario Model
- contrato comum de cenário
- execução homogênea
- diferença clara entre contrato, executor e run

### 5. Runtime Architecture Cleanup
- runtime orchestrator
- separação control API vs read model
- cleanup da duplicação da telemetry API
- estratégia de ambiente mais explícita

### 6. Final Validation and QA
- validação integrada do Mark 1
- QA terminal
- runbook final
- checklist terminal de pronto

## Fora de escopo do Mark 1

- múltiplos tipos reais de veículo
- braço robótico operacional completo
- capability registry completo em runtime
- MCP funcional completo
- hardware deployment real
- integração física real
- runtime multi-robot completo

## Escopo obrigatório de compatibilidade
Mesmo fora do escopo imediato, o Mark 1 precisa preservar compatibilidade com:
- payloads futuros
- actuators futuros
- múltiplos tipos de runtime
- actions programáticas orientadas a capability
