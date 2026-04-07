# Mark 1 Implementation Checklist

## Regras
- usar o código atual como ponto de partida
- não alterar o escopo
- sempre respeitar compatibilidade com Mark 2
- não começar pela UI antes do domínio e control plane
- toda fase deve ter validação

## Convenção de status
- `[x]` concluído e com evidência no repositório ou nas validações da rodada
- `[]` ainda pendente ou não validado formalmente

## Mapa geral de fases

| Fase | Nome | Objetivo |
|---|---|---|
| R0 | Alignment Freeze | travar escopo, docs e governança |
| R1 | Domain and Action Model | estabilizar entidades, actions e capabilities |
| R2 | Control API Skeleton | criar a espinha do control plane |
| R3 | Runtime Orchestrator | unificar lifecycle da simulação |
| R4 | Scenario Unification | unificar execução de cenários |
| R5 | Mission Control Surface | expor missão via control plane |
| R6 | Vehicle and Safety Control | expor veículo e faults via control plane |
| R7 | Read Model Cleanup | consolidar telemetry/read model |
| R8 | Operator UI Shell | transformar dashboard em console operacional |
| R9 | Operator UI Control Panels | adicionar superfícies de comando |
| R10 | Perception and Camera Operation | integrar percepção/câmera na operação |
| R11 | Session/Run/Replay Experience | consolidar runs e replay |
| R12 | Capability Surface | expor capabilities de forma clara |
| R13 | Environment and Runbooks | fechar experiência oficial de operação |
| R14 | Integration Hardening | endurecer integração completa |
| R15 | Final QA and Acceptance | validação terminal completa |

---

## Fase R0 — Alignment Freeze

### Objetivo
Fechar documentação, regras e ownership do refactor.

### Status da fase
- [x] leitura obrigatória concluída
- [x] governança V2 presente no repositório

### Tarefas
- [x] adicionar `docs/v2`
- [x] substituir `AGENTS.md`
- [x] substituir `.agents/`
- [x] substituir `.codex/skills/`
- [] criar branch dedicada
- [x] validar que o estado atual permanece íntegro no nível documental/estrutural
- [x] revisar a auditoria atual

### Entregáveis
- [x] pacote V2 no repositório
- [x] confirmação de leitura obrigatória
- [] commit isolado de governança

### Validação
- [x] `git diff --name-only`
- [x] conferência de paths
- [x] revisão humana

### Critério de pronto
- [x] docs e governança estão estáveis
- [] nada foi implementado ainda

### Agente líder
- `refactor-governance-agent`

---

## Fase R1 — Domain and Action Model

### Objetivo
Estabilizar o vocabulário e os contratos do produto.

### Status da fase
- [x] contratos compartilhados Python criados
- [x] contratos compartilhados TypeScript criados
- [x] testes básicos de schema/serialização executados
- [x] gating de action explicitado por escopo de domínio
- [x] DTOs nominais de input/output registrados

### Tarefas
- [x] definir entidades centrais de domínio
- [x] definir modelos de `SimulationSession`, `Run`, `Action`, `Capability`, `Mission`, `Vehicle`
- [x] definir schemas ou DTOs de control plane
- [x] definir taxonomia de ações
- [x] mapear ações atuais para ações de produto
- [x] definir erros padronizados

### Arquivos esperados
- [x] `packages/shared-py/src/control_plane/domain/*`
- [x] `packages/shared-ts/src/control-plane/*`
- [x] docs atualizadas no escopo dos pacotes compartilhados

### Validação
- [x] testes de schema
- [x] testes de serialização
- [x] teste contratual TypeScript
- [x] revisão de mapping com código atual

### Critério de pronto
- [x] toda ação relevante do produto tem contrato estável nesta camada compartilhada

### Agente líder
- `action-contracts-agent`

---

## Fase R2 — Control API Skeleton

### Objetivo
Criar a espinha dorsal do control plane.

### Status da fase
- [x] fase implementada estruturalmente
- [x] capability discovery agora reflete status de runtime

### Tarefas
- [x] criar novo serviço `services/control-api/`
- [x] definir routers iniciais
- [x] definir handlers stub para cada família de ação
- [x] definir status endpoint e capability discovery endpoint
- [x] definir session/run stores iniciais
- [x] definir erro padrão e response envelope

### Actions mínimas desta fase
- [x] `simulation.status.get`
- [x] `scenario.list`
- [x] `scenario.status.get`
- [x] `telemetry.snapshot.get` proxy inicial
- [x] `telemetry.runs.list` estrutural
- [x] `capabilities.list`

### Validação
- [x] testes HTTP
- [x] smoke do serviço
- [x] instalação editável e testes em `venv` limpo

### Critério de pronto
- [x] control API existe e responde estruturalmente

### Agente líder
- `control-plane-architect-agent`

---

## Fase R3 — Runtime Orchestrator

### Objetivo
Tornar start/stop da simulação uma action de produto.

### Status da fase
- [x] fase implementada
- [x] lifecycle da simulação exposto via control plane
- [x] persistência de `session_id` e `runs` ativa no serviço
- [x] runtime shell continua isolado atrás do adapter oficial

### Tarefas
- [x] encapsular `scripts/sim/start.sh`
- [x] encapsular `scripts/sim/stop.sh`
- [x] normalizar estado da session
- [x] persistir `session_id`
- [x] suportar modo `visual` e `headless`
- [x] criar health/readiness do runtime
- [x] normalizar erros de preflight

### Actions mínimas
- [x] `simulation.start`
- [x] `simulation.stop`
- [x] `simulation.status.get`
- [x] `simulation.restart`

### Validação
- [x] start/stop por API
- [x] session lifecycle test
- [x] health/readiness test
- [x] smoke visual/manual documentado
- [x] `scripts/sim/start.sh --check`
- [x] `scripts/sim/stop.sh --check`

### Critério de pronto
- [x] operador ou API consegue subir/parar simulação sem shell direto

### Agente líder
- `runtime-orchestration-agent`

---

## Fase R4 — Scenario Unification

### Objetivo
Parar de tratar cenários como superfícies heterogêneas.

### Status da fase
- [x] fase implementada
- [x] `takeoff_land` materializado pela superfície unificada
- [x] cenários ROS 2 permanecem formalizados sem prometer executor antes da fase correta

### Tarefas
- [x] definir modelo único de cenário
- [x] criar registry simples de cenários
- [x] adaptar `takeoff_land` ao control plane
- [x] decidir executor por cenário sem vazar isso para a UI
- [x] iniciar trilha de `patrol_basic` como scenario action
- [x] padronizar run/result/status

### Actions
- [x] `scenario.list`
- [x] `scenario.run`
- [x] `scenario.cancel`
- [x] `scenario.status.get`

### Validação
- [x] `takeoff_land` via control plane
- [x] run auditável
- [x] status consultável
- [x] wrapper real `scripts/scenarios/run_scenario.sh` validado com `--backend fake-success`

### Critério de pronto
- [x] pelo menos um cenário roda de ponta a ponta pela nova superfície

### Agente líder
- `scenario-runtime-agent`

---

## Fase R5 — Mission Control Surface

### Objetivo
Expor missão como ação de produto, não como tópico bruto.

### Status da fase
- [x] fase implementada
- [x] `patrol_basic` materializado pela mission surface
- [x] missão continua isolada no runtime ROS 2 atrás do adapter do control plane

### Tarefas
- [x] criar adapter ROS 2 para `MissionCommand`
- [x] modelar `mission.start`, `mission.abort`, `mission.reset`
- [x] criar tradução de status ROS 2 -> state de produto
- [x] criar endpoint(s) de mission control
- [x] manter compatibilidade com mission runtime atual
- [x] suportar `patrol_basic` pela superfície unificada

### Validação
- [x] iniciar missão por API
- [x] abortar missão por API
- [x] observar estado consolidado

### Critério de pronto
- [x] missão pode ser operada sem `ros2 topic pub`

### Agente líder
- `mission-runtime-agent`

---

## Fase R6 — Vehicle and Safety Control

### Objetivo
Expor controles do veículo e fault injection pela mesma superfície.

### Status da fase
- [x] fase implementada
- [x] vehicle runtime ROS 2 encapsulado atrás da Control API
- [x] safety runtime continua soberano e exposto sem bypass de tópico cru

### Tarefas
- [x] adaptar `VehicleCommand` para actions de produto
- [x] adaptar `SafetyFault` para actions de produto
- [x] suportar arm/disarm/land/rtl
- [x] suportar inject/clear fault
- [x] normalizar safety status para o control plane
- [x] suportar `vehicle.takeoff`
- [x] suportar `vehicle.goto`

### Actions
- [x] `vehicle.arm`
- [x] `vehicle.disarm`
- [x] `vehicle.takeoff`
- [x] `vehicle.land`
- [x] `vehicle.return_to_home`
- [x] `vehicle.goto`
- [x] `safety.inject_fault`
- [x] `safety.clear_fault`
- [x] `safety.status.get`

### Validação
- [x] arm/disarm por control API
- [x] inject fault por control API
- [x] reação observável via read model
- [x] suíte HTTP da Control API atualizada para vehicle/safety

### Critério de pronto
- [x] controle operacional principal não depende mais de publish manual em tópico cru

### Agente líder
- `safety-runtime-agent`

---

## Fase R7 — Read Model Cleanup

### Objetivo
Consolidar a camada de observabilidade e limpar duplicações.

### Status da fase
- [x] fase concluída

### Tarefas
- [x] escolher implementação única da telemetry API
- [x] isolar trilha legada em `services/telemetry-api/src/telemetry_api/*` como compatibilidade, mantendo `services/telemetry-api/telemetry_api/*` como trilha canônica
- [x] explicitar `snapshot`, `metrics`, `events`, `runs`, `replay`
- [x] reforçar `run_id`, `session_id`, correlação de actions e eventos
- [x] ajustar schemas compartilhados TS/Python se necessário

### Validação
- [x] testes backend
- [x] replay funcional
- [x] snapshot consistente com control plane

### Critério de pronto
- [x] read model está claro, estável e sem trilhas concorrentes

### Agente líder
- `telemetry-readmodel-agent`

---

## Fase R8 — Operator UI Shell

### Objetivo
Transformar o dashboard em console operacional.

### Status da fase
- [x] fase concluída

### Tarefas
- [x] reorganizar navegação
- [x] criar layout operacional
- [x] criar camada cliente para Control API
- [x] manter camada cliente de Read API
- [x] introduzir conceito de session, run, actions e state consolidado

### Validação
- [x] app sobe
- [x] overview operacional existe
- [x] consumo básico de control/read APIs

### Critério de pronto
- [x] UI deixa de ser apenas painel read-only estruturalmente

### Agente líder
- `operator-ui-agent`

---

## Fase R9 — Operator UI Control Panels

### Objetivo
Adicionar controle operacional real ao frontend.

### Status da fase
- [x] fase concluída

### Tarefas
- [x] painel de simulação
- [x] painel de cenários
- [x] painel de missão
- [x] painel de veículo
- [x] painel de safety
- [x] feedback de ação e status
- [x] confirmações destrutivas
- [x] status de runs

### Validação
- [x] iniciar simulação pela UI
- [x] rodar `takeoff_land` pela UI
- [x] iniciar/abortar missão pela UI
- [x] injetar/limpar fault pela UI

### Critério de pronto
- [x] operador consegue controlar o sistema sem depender de vários terminais

### Agente líder
- `operator-ui-agent`

---

## Fase R10 — Perception and Camera Operation

### Objetivo
Tornar percepção/câmera parte explícita da experiência operacional.

### Status da fase
- [x] fase concluída

### Tarefas
- [x] expor perception status no control/read model
- [x] painel de heartbeat
- [x] painel de detections/tracked object
- [x] ligação com stream/proxy de câmera quando disponível
- [x] explicitar limitações de ambiente para vídeo ao vivo

### Validação
- [x] UI mostra perception heartbeat
- [x] UI mostra tracked object
- [x] documentação do caminho de vídeo está clara

### Critério de pronto
- [x] percepção deixa de ser apenas um detalhe de validators

### Agente líder
- `perception-runtime-agent`

---

## Fase R11 — Session / Run / Replay Experience

### Objetivo
Consolidar a experiência de run tracking e replay.

### Status da fase
- [x] fase concluída

### Tarefas
- [x] unificar `session_id` e `run_id` como conceitos de produto
- [x] timeline de run
- [x] lista de runs
- [x] detalhes de run
- [x] replay integrado
- [x] correlação action -> event -> replay

### Validação
- [x] executar cenário e navegar pelo run correspondente
- [x] abrir replay pela UI
- [x] correlacionar action request ao run gerado

### Critério de pronto
- [x] experiência de auditoria operacional está completa

### Agente líder
- `telemetry-readmodel-agent`

---

## Fase R12 — Capability Surface

### Objetivo
Preparar o terreno para MCP/IA sem implementar o Mark 2 inteiro.

### Status da fase
- [x] fase concluída

### Tarefas
- [x] expor lista de capabilities
- [x] mapear ações por capability
- [x] tornar cenários e controles descobríveis
- [x] documentar uso programático
- [x] definir metadata mínima por capability

### Validação
- [x] endpoint de capabilities
- [x] docs atualizadas
- [x] actions mapeadas corretamente

### Critério de pronto
- [x] superfície programática é legível para automação futura

### Agente líder
- `capability-registry-agent`

---

## Fase R13 — Environment and Runbooks

### Objetivo
Fechar a experiência operacional oficial.

### Status da fase
- [x] fase concluída

### Tarefas
- [x] documentar caminho oficial local visual
- [x] documentar caminho oficial de runtime proof
- [x] documentar troubleshooting do control plane
- [x] documentar troubleshooting da UI
- [x] documentar troubleshooting de session/run

### Validação
- [x] revisão runbook
- [x] walkthrough manual controlado

### Critério de pronto
- [x] existe um caminho operacional oficial inequívoco

### Agente líder
- `runtime-orchestration-agent`

---

## Fase R14 — Integration Hardening

### Objetivo
Eliminar arestas antes da validação final.

### Status da fase
- [x] fase concluída

### Tarefas
- [x] estabilizar erros
- [x] estabilizar timeout/retry
- [x] endurecer contratos
- [x] revisar acoplamentos indevidos
- [x] revisar compatibilidade Mark 1 → Mark 2
- [x] revisar UX operacional

### Validação
- [x] suíte parcial integrada
- [x] revisão arquitetural final

### Critério de pronto
- [x] o sistema está maduro para QA terminal

### Agente líder
- `refactor-governance-agent`

---

## Fase R15 — Final QA and Acceptance

### Objetivo
Executar a validação final do Mark 1.

### Cenário terminal mínimo
1. [x] iniciar sessão visual
2. [x] ver estado consolidado
3. [x] executar `takeoff_land`
4. [x] iniciar missão `patrol_basic`
5. [x] injetar fault de safety
6. [x] observar resposta do runtime
7. [x] observar percepção/heartbeat
8. [x] abrir replay da run
9. [x] parar a simulação

### Status da fase
- [x] fase concluída

### Entregáveis
- [x] checklist final preenchida
- [x] QA report
- [x] acceptance report
- [x] runbook final
- [x] troubleshooting final
- [x] matriz final de pronto

### Critério de pronto
- [x] sistema operável
- [x] sistema auditável
- [x] sistema validado
- [x] sistema documentado
- [x] sistema compatível com Mark 2
- [x] nenhuma dependência crítica permanece escondida em fluxo técnico informal

### Agente líder
- `qa-validation-agent`
