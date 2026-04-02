# PROJECT-EXECUTION-CHECKLIST.md

## Propósito

Esta checklist descreve, em ordem de execução, o caminho do repositório do zero ate uma simulação madura e repetivel.

## Regras de uso

- Nenhuma fase deve ser iniciada antes da anterior ter seus criterios de aceite atendidos.
- Toda fase precisa entregar arquivos, validação e atualização documental quando houver mudança de fluxo, arquitetura ou teste.
- PX4 continua sendo o dono do voo.
- ROS 2 continua sendo o middleware principal.
- MAVSDK continua sendo a camada principal de controle de alto nivel e cenarios.
- O projeto permanece simulation-first durante toda a execução desta checklist.

## Status atual

- Fase 0: concluida
- Fase 1: em andamento
- Fases 2 a 8: pendentes

## Ownership por fase

| Fase | Agente lider | Apoio principal |
|---|---|---|
| 0 | Repo Bootstrap Agent | Architecture Agent |
| 1 | PX4 Vendor Agent | Simulation Orchestrator Agent |
| 2 | PX4 Interface Agent | Repo Bootstrap Agent |
| 3 | ROS 2 Workspace Agent | PX4 Interface Agent |
| 4 | Mission Agent | Architecture Agent |
| 5 | Safety Agent | Mission Agent |
| 6 | Perception Agent | ROS 2 Workspace Agent |
| 7 | Telemetry Agent | Dashboard Agent |
| 8 | CI Agent | Safety Agent |

## Fase 0 - Bootstrap

### Objetivo

Estabelecer o esqueleto do monorepo para que as fases seguintes tenham contratos, estrutura e pontos de entrada claros, sem tentar subir PX4, Gazebo ou ROS 2 ainda.

### Status da fase

- [x] Checklist executavel criada
- [x] Scaffold inicial de `simulation/` e `robotics/ros2_ws/` criado
- [x] Diretórios-base de `services/`, `apps/`, `packages/` e `third_party/` registrados
- [x] Validacao local e teste automatizado do bootstrap adicionados

### Entregaveis

- [x] Criar `docs/PROJECT-EXECUTION-CHECKLIST.md`
- [x] Criar `docs/PHASE-0-OPEN-DECISIONS.md`
- [x] Criar a estrutura local de `simulation/` com documentação de cada subdiretorio
- [x] Criar o esqueleto minimo de `robotics/ros2_ws/`
- [x] Registrar os contratos basicos de `gazebo/`, `worlds/`, `models/`, `resources/` e `scenarios/`
- [x] Registrar placeholders de `services/`, `apps/`, `packages/` e `third_party/`
- [x] Definir validacoes estruturais simples para confirmar a arvore do bootstrap
- [x] Definir um teste automatizado da Fase 0 sem depender de ROS 2 completo

### Validação

- `bash scripts/bootstrap/validate-phase-0.sh`
- `bash -n scripts/bootstrap/validate-phase-0.sh`
- `bash robotics/ros2_ws/scripts/validate-workspace.sh`
- `python3 -m unittest scripts.tooling.tests.test_phase0_structure`
- `find simulation -maxdepth 4 -type f | sort`
- `rg --files simulation`
- `test -f docs/PROJECT-EXECUTION-CHECKLIST.md`

### Criterios de aceite

- A arvore de `simulation/` existe e explica o papel de cada pasta.
- A arvore base de `robotics/`, `services/`, `apps/`, `packages/` e `third_party/` existe.
- Nenhum processo de simulacao e iniciado nesta fase.
- As decisoes abertas e fechadas da Fase 0 ficam registradas em `docs/PHASE-0-OPEN-DECISIONS.md`.
- A checklist cobre as fases 0 a 8 com foco em entrega, validacao e criterio de aceite.

## Fase 1 - Simulação minima

### Objetivo

Subir a combinacao minima de PX4 SITL e Gazebo para validar que o ambiente de simulacao pode iniciar de forma repetivel.

### Status da fase

- [x] Baseline oficial do simulador e do ambiente de referencia registrada
- [x] Decisoes bloqueadoras da Fase 1 fechadas em `docs/PHASE-0-OPEN-DECISIONS.md`
- [x] Manifesto inicial da Fase 1 criado
- [x] Validador leve da Fase 1 criado
- [x] Script de vendorizaçao do submodule do PX4 preparado
- [ ] Vendorizar PX4 Autopilot em `third_party/PX4-Autopilot/`
- [x] Criar o primeiro world, modelo e cenario da simulacao minima
- [ ] Verificar a subida real de PX4 SITL + Gazebo Harmonic

### Entregaveis

- [ ] Vendorizar PX4 Autopilot em `third_party/PX4-Autopilot/`
- [x] Definir a primeira world minimalista em `simulation/gazebo/worlds/`
- [x] Criar modelo base do veiculo em `simulation/gazebo/models/`
- [x] Registrar recursos visuais e fisicos em `simulation/gazebo/resources/`
- [x] Criar o primeiro cenário de smoke test em `simulation/scenarios/`
- [x] Registrar baseline oficial de PX4, ROS 2, Gazebo e XRCE-DDS
- [x] Preparar script seguro para vendorizaçao do submodule do PX4
- [ ] Documentar a ordem de subida do stack de simulação
- [ ] Consolidar a pinagem de `px4_msgs` com a mesma release family do PX4 escolhido

### Validação

- `find third_party -maxdepth 2 -type d`
- `find simulation/gazebo -maxdepth 3 -type f | sort`
- `find simulation/scenarios -maxdepth 2 -type f | sort`
- `bash scripts/sim/validate-phase-1.sh`
- `bash -n scripts/sim/validate-phase-1.sh`
- `bash -n scripts/sim/vendor-px4-submodule.sh`
- `rg -n "v1.16.1|release/1.16|Humble|Harmonic|v2.4.3" docs README.md scripts/sim third_party`

### Criterios de aceite

- PX4 SITL inicia em modo de simulacao.
- Gazebo inicia com a world base do projeto.
- O veiculo aparece na cena.
- A base documental permite repetir a subida sem depender de memoria manual.
- O baseline oficial deixa claro que Gazebo Harmonic e ROS 2 Humble sao a referencia do projeto.
- O PX4 esta vendorizado como submodule no caminho oficial.
- O fluxo de vendorizaçao do PX4 como submodule esta documentado e falha claramente fora de um repositorio Git valido.

## Fase 2 - Integração MAVSDK

### Objetivo

Conectar um runner de cenarios MAVSDK ao ambiente minimo de simulacao para comandos de alto nivel e automacao de testes.

### Entregaveis

- [ ] Criar o runner de cenarios baseado em MAVSDK
- [ ] Definir contratos de conexao com o autopilot em simulação
- [ ] Implementar comandos de arm, takeoff, hover, waypoint e land
- [ ] Registrar asserts basicos de telemetria para cada comando
- [ ] Garantir que o runner falhe de forma clara quando o simulador nao responder

### Validação

- `pytest`
- `python -m <runner_mavsdk>`
- `rg -n "takeoff|land|waypoint" scripts simulation robotics`

### Criterios de aceite

- Um cenário consegue mandar o veiculo de armamento ate pouso.
- O runner diferencia sucesso, timeout e falha de conexao.
- A execucao fica reproduzivel em ambiente limpo.

## Fase 3 - ROS 2 bridge

### Objetivo

Criar o workspace ROS 2, os pacotes de dominio e as bridges necessarias para desacoplar mission, safety, perception e telemetria do controle direto.

### Entregaveis

- [ ] Inicializar `robotics/ros2_ws/`
- [ ] Criar `px4_msgs` e `drone_msgs`
- [ ] Criar `drone_bringup`
- [ ] Criar `drone_px4`
- [ ] Definir launch files e params externos
- [ ] Documentar QoS, topicos e fronteiras entre pacotes

### Validação

- `colcon build`
- `colcon test`
- `ros2 launch <package> <launch_file>`

### Criterios de aceite

- O workspace compila.
- As mensagens do dominio reduzem acoplamento com detalhes internos do PX4.
- O bringup descreve claramente a ordem de subida dos nodes.

## Fase 4 - Missão

### Objetivo

Implementar a orquestracao de missao com estado explicito, sem misturar safety com a logica principal de patrulha.

### Entregaveis

- [ ] Criar `mission_manager_node`
- [ ] Definir state machine de mission
- [ ] Cobrir arm, takeoff, hover, patrol, return-to-home e land
- [ ] Adicionar fallback seguro de abort
- [ ] Criar testes unitarios para transicoes de estado

### Validação

- `pytest`
- `colcon test --packages-select drone_mission`
- `rg -n "state machine|abort|return-to-home|patrol" robotics`

### Criterios de aceite

- A missao executa uma rota basica de patrulha.
- As transicoes de estado sao previsiveis e testadas.
- O modulo de missao nao assume responsabilidade de safety.

## Fase 5 - Safety

### Objetivo

Adicionar gerenciamento de safety para geofence, perda de link, failsafes e falhas injetadas em simulacao.

### Entregaveis

- [ ] Criar `safety_manager_node`
- [ ] Definir regras de geofence
- [ ] Cobrir perda de GPS, RC e data link
- [ ] Cobrir travamento de node de percepção e atraso excessivo
- [ ] Definir comportamento de abort e fallback seguro

### Validação

- `pytest`
- `colcon test --packages-select drone_safety`
- `rg -n "geofence|failsafe|loss|timeout|abort" robotics`

### Criterios de aceite

- Pelo menos tres falhas simuladas disparam respostas esperadas.
- O sistema reage de forma deterministica a eventos de safety.
- A politica de safety permanece separada da logica de missao.

## Fase 6 - Percepção

### Objetivo

Introduzir o pipeline de camera simulada, pre-processamento, deteccao e tracking, gerando eventos consumiveis pelo sistema de autonomia.

### Entregaveis

- [ ] Criar `camera_input_node`
- [ ] Criar `object_detector_node`
- [ ] Criar `tracker_node`
- [ ] Definir eventos visuais de entrada e saida
- [ ] Documentar a interface entre percepção e missão

### Validação

- `pytest`
- `colcon test --packages-select drone_perception`
- `rg -n "camera|detector|tracker|opencv|event" robotics`

### Criterios de aceite

- O pipeline consome camera simulada.
- Os eventos visuais chegam ao dominio de missao ou safety sem acoplamento excessivo.
- O comportamento degradado quando a percepcao falha esta definido e testado.

## Fase 7 - Operação

### Objetivo

Publicar telemetria, logs, metricas, replay e dashboard para observabilidade operacional do stack de simulação.

### Entregaveis

- [ ] Criar `telemetry_bridge_node`
- [ ] Criar API de telemetria em `services/telemetry-api/`
- [ ] Criar dashboard em `apps/dashboard/`
- [ ] Definir persistencia de logs, metricas e eventos
- [ ] Definir suporte a replay

### Validação

- `pytest`
- `npm test`
- `rg -n "telemetry|metrics|replay|dashboard|log" robotics services apps`

### Criterios de aceite

- O estado operacional fica visivel durante a simulacao.
- O histórico de eventos pode ser auditado depois da execucao.
- O dashboard nao mistura regra de missao com logica de apresentacao.

## Fase 8 - Maturidade de simulacao

### Objetivo

Fechar o ciclo com confiabilidade, cobertura de cenarios, CI e padronizacao para que a simulação seja repetivel e evolutiva.

### Entregaveis

- [ ] Consolidar cenarios obrigatorios: `takeoff_land`, `patrol_basic`, `failsafe_gps_loss`, `failsafe_rc_loss`, `geofence_breach`
- [ ] Garantir cobertura dos modos de falha obrigatorios
- [ ] Adicionar CI com validacao estrutural, testes e smoke scenarios
- [ ] Produzir documentação de operacao e troubleshooting
- [ ] Revisar critérios de aceite para futura migração para hardware

### Validação

- `pytest`
- `colcon test`
- `npm test`
- `bash scripts/<scenario_runner>` quando o runner existir

### Criterios de aceite

- Pelo menos um cenario completo roda do inicio ao fim sem intervenção manual.
- Tres ou mais falhas simuladas sao reproduziveis e observaveis.
- A documentacao permite que outro agente execute a mesma sequencia.

## Definição de pronto do projeto

- O stack completo sobe em simulacao de forma reproduzivel.
- A missao basica e os failsafes foram exercitados.
- A percepcao gera eventos uteis para o dominio.
- Telemetria, logs, metricas e replay estao disponiveis.
- A CI cobre a estrutura e os cenarios essenciais.
- O projeto continua explicitamente simulation-first.
