# Mark 1 Operator UI Architecture

## Objetivo
Fazer o dashboard evoluir para uma **Operator Console** real.

## Princípio
O frontend deve ser a interface humana do sistema, não o lugar da lógica central.

## Estado atual

`R8-R11` entregam a Operator Console funcional do Mark 1 com:
- `Control API` para action surfaces
- `Read API` para snapshot, metrics, events, runs e replay
- correlação `action -> run -> replay` materializada na própria UI
- painéis reais para simulação, cenário, missão, veículo, safety e percepção

## Superfícies da UI

### 1. Session Control
- Start simulation
- Stop simulation
- Restart simulation
- Visual/headless mode
- session status

### 2. Scenario Console
- list scenarios
- run scenario
- watch scenario status
- cancel scenario
- open run details

### 3. Mission Console
- mission status
- start mission
- abort mission
- reset mission

### 4. Vehicle Console
- arm/disarm
- takeoff
- land
- rtl
- goto when enabled

### 5. Safety Console
- current safety status
- inject fault
- clear fault
- observe reaction timeline

### 6. Perception Console
- heartbeat
- detection list
- tracked object
- camera panel or stream proxy

### 7. Telemetry Console
- snapshot
- metrics
- events
- run timeline
- replay viewer

## Navigation model

### Primary pages
- Overview
- Control
- Mission
- Safety
- Perception
- Runs / Replay
- Settings / Environment

### Navigation actually delivered
- Overview
- Control
- Mission
- Safety
- Perception
- Runs / Replay
- Settings / Environment

## State model
UI state deve ser derivado de:
- control plane state
- read model state

Evitar:
- estado duplicado com semântica própria no frontend
- lógica de polling dispersa
- efeitos colaterais diretos em múltiplas APIs

## Client split
- `controlApi.ts` concentra `status`, `capabilities`, `scenarios`, `mission`, `safety`, `perception` e actions formais do control plane
- `readApi.ts` concentra `snapshot`, `metrics`, `events`, `runs` e `replay`
- a UI não decide executor, não reconstrói state machine e não traduz shell/ROS 2 para semântica de produto

## Current operational panels
- `Control` cobre simulation lifecycle, scenario run/cancel e vehicle commands
- `Mission` cobre `start`, `abort`, `reset` e constraints consolidadas
- `Safety` cobre `inject_fault`, `clear_fault`, active faults e audit trail recente
- `Perception` cobre heartbeat, tracked object, latest event e stream/proxy status
- `Runs / Replay` cobre inventory, run details, action correlation, replay e metrics

## Suggested frontend modules
- `features/session-control`
- `features/scenario-control`
- `features/mission-control`
- `features/vehicle-control`
- `features/safety-control`
- `features/perception-console`
- `features/read-model`

## UX rules
1. Toda action deve mostrar:
   - intenção
   - status
   - resultado
   - erro quando existir
2. Toda run deve ser clicável e auditável
3. Toda ação destrutiva deve pedir confirmação
4. A UI deve sempre mostrar se está operando:
   - headless
   - visual
   - local
   - containerizado
