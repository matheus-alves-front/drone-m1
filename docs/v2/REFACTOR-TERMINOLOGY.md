# Refactor Terminology

## Simulation Session
Ciclo de vida do runtime simulado:
- start
- active
- degraded
- stopping
- stopped

## Run
Execução identificável de um cenário, missão ou sessão operacional, com `run_id` auditável.

## Vehicle
Instância controlável de mobilidade aérea no Mark 1.  
No Mark 2, vira abstração mais geral.

## Mission
Plano de alto nível com intenção operacional, restrições, pré-condições, pós-condições e fallback.

## Action
Comando formal exposto pelo control plane.  
Ex.: `mission.start`, `vehicle.land`, `safety.inject_fault`

## Capability
Capacidade declarada e descoberta do sistema.  
Ex.: `scenario.takeoff_land.run`, `mission.patrol`, `telemetry.snapshot.read`

## Payload
Módulo físico ou lógico acoplável ao veículo.  
No Mark 1 existe como conceito preparado; no Mark 2 vira entidade formal.

## Actuator
Componente que gera ação física além do voo.  
Ex.: braço robótico, gimbal, speaker, display, tool head.

## Control Plane
Camada unificada de comando, sessões, ações, capabilities, orchestration e policy application.

## Read Model
Camada otimizada para leitura e observabilidade:
- snapshot
- metrics
- events
- replay

## Operator UI
Interface humana principal do sistema.

## Machine Interface
Interface programática do sistema, incluindo futura superfície MCP.

## Compatibility Rule
Regra que impede o Mark 1 de ser codado de um jeito que mate o Mark 2.
