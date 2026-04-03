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
- Fase 1: concluida
- Fase 2: concluida
- Fase 3: concluida
- Fase 4: concluida
- Fase 5: concluida
- Fase 6: concluida
- Fase 7: concluida
- Fase 8: concluida

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
- [x] Registrar a trilha inicial de `px4_msgs`
- [x] Diretórios-base de `services/`, `apps/`, `packages/` e `third_party/` registrados
- [x] Validacao local e teste automatizado do bootstrap adicionados

### Entregaveis

- [x] Criar `docs/PROJECT-EXECUTION-CHECKLIST.md`
- [x] Criar `docs/decisions/PHASE-0-OPEN-DECISIONS.md`
- [x] Criar `docs/reference/ROBOTICS-ROS2-WORKSPACE-PX4-MSGS.md`
- [x] Criar a estrutura local de `simulation/` com documentação de cada subdiretorio
- [x] Criar o esqueleto minimo de `robotics/ros2_ws/`
- [x] Registrar a trilha inicial de `px4_msgs`
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
- As decisoes abertas e fechadas da Fase 0 ficam registradas em `docs/decisions/PHASE-0-OPEN-DECISIONS.md`.
- A checklist cobre as fases 0 a 8 com foco em entrega, validacao e criterio de aceite.

## Fase 1 - Simulação minima

### Objetivo

Subir a combinacao minima de PX4 SITL e Gazebo para validar que o ambiente de simulacao pode iniciar de forma repetivel.

### Status da fase

- [x] Baseline oficial do simulador e do ambiente de referencia registrada
- [x] Decisoes bloqueadoras da Fase 1 fechadas em `docs/decisions/PHASE-0-OPEN-DECISIONS.md`
- [x] Manifesto inicial da Fase 1 criado
- [x] Validador leve da Fase 1 criado
- [x] Script de vendorizaçao do submodule do PX4 preparado
- [x] Vendorizar PX4 Autopilot em `third_party/PX4-Autopilot/`
- [x] Criar o primeiro world, modelo e cenario da simulacao minima
- [x] Documentar a ordem oficial de subida do stack minimo
- [x] Documentar o comando minimo headless e os pre-requisitos oficiais
- [x] Criar os scripts `start.sh` e `stop.sh` da Fase 1
- [x] Corrigir o baseline da imagem oficial de validacao para evitar mistura Garden + Harmonic
- [x] Verificar a subida real de PX4 SITL + Gazebo Harmonic
- [x] Confirmar um runtime containerizado compativel com Gazebo Harmonic CLI
- [x] Fixar uma `GZ_PARTITION` explicita na validacao containerizada para garantir discovery entre processos `gz`

### Entregaveis

- [x] Vendorizar PX4 Autopilot em `third_party/PX4-Autopilot/`
- [x] Definir a primeira world minimalista em `simulation/gazebo/worlds/`
- [x] Criar modelo base do veiculo em `simulation/gazebo/models/`
- [x] Registrar recursos visuais e fisicos em `simulation/gazebo/resources/`
- [x] Criar o primeiro cenário de smoke test em `simulation/scenarios/`
- [x] Registrar baseline oficial de PX4, ROS 2, Gazebo e XRCE-DDS
- [x] Preparar script seguro para vendorizaçao do submodule do PX4
- [x] Documentar a ordem de subida do stack de simulação
- [x] Documentar o comando minimo headless e os pre-requisitos oficiais
- [x] Consolidar a pinagem inicial de `px4_msgs` com a mesma release family do PX4 escolhido
- [x] Criar os scripts reais de start e stop do stack minimo
- [x] Definir uma imagem oficial de validacao Jammy + Harmonic sem `gz-garden` preinstalado
- [x] Garantir discovery estavel do Gazebo em container com `GZ_PARTITION` explicita

### Validação

- `find third_party -maxdepth 2 -type d`
- `find simulation/gazebo -maxdepth 3 -type f | sort`
- `find simulation/scenarios -maxdepth 2 -type f | sort`
- `bash scripts/sim/validate-phase-1.sh`
- `bash -n scripts/sim/validate-phase-1.sh`
- `bash -n scripts/sim/start.sh`
- `bash -n scripts/sim/stop.sh`
- `bash -n scripts/sim/vendor-px4-submodule.sh`
- `bash -n scripts/sim/validate-phase-1-container.sh`
- `bash -n scripts/sim/build-phase-1-container-image.sh`
- `git submodule status --recursive`
- `bash robotics/ros2_ws/scripts/validate-workspace.sh`
- `rg -n "v1.16.1|release/1.16|Humble|Harmonic|v2.4.3" docs README.md scripts/sim third_party`
- `rg -n "HEADLESS=1 make px4_sitl gz_x500" docs scripts/sim`
- `bash scripts/sim/start.sh --check`
- `bash scripts/sim/stop.sh --check`
- `bash scripts/sim/build-phase-1-container-image.sh --check`
- `bash scripts/sim/validate-phase-1-container.sh --check`
- `bash scripts/sim/validate-phase-1-container.sh`
- `bash scripts/sim/check-gz-harmonic-cli.sh`

### Criterios de aceite

- PX4 SITL inicia em modo de simulacao.
- Gazebo inicia com a world base do projeto.
- O veiculo e carregado na world base do projeto, inclusive em validacao headless via `gz_x500`.
- A base documental permite repetir a subida sem depender de memoria manual.
- O baseline oficial deixa claro que Gazebo Harmonic e ROS 2 Humble sao a referencia do projeto.
- O PX4 esta vendorizado como submodule no caminho oficial.
- O fluxo de vendorizaçao do PX4 como submodule esta documentado e falha claramente fora de um repositorio Git valido.
- A ordem oficial de subida do stack minimo fica registrada antes da orquestração completa existir.
- O comando minimo headless e seus pre-requisitos estao explicitamente documentados.
- O alinhamento inicial de `px4_msgs` com `release/1.16` fica documentado no workspace.
- O stack minimo pode ser orquestrado por `start.sh` e parado por `stop.sh` sem misturar responsabilidade com mission ou safety.
- A validacao real em container so conta como concluida quando o preflight de Gazebo Harmonic CLI e a subida de PX4 SITL passarem no mesmo ambiente.
- O runtime containerizado do Gazebo usa uma `GZ_PARTITION` explicita e reproduzivel para evitar falhas silenciosas de discovery entre `gz sim`, `gz topic` e `gz service`.

## Fase 2 - Integração MAVSDK

### Objetivo

Conectar um runner de cenarios MAVSDK ao ambiente minimo de simulacao para comandos de alto nivel e automacao de testes.

### Status da fase

- [x] Runner Python CLI implementado
- [x] Contrato executavel `takeoff_land.json` consolidado
- [x] Backend fake e testes locais passando
- [x] Infraestrutura minima da Fase 2 validada contra a base real da Fase 1
- [x] Validacao E2E real concluida contra `PX4 SITL + Gazebo Harmonic`
- [x] Fase liberada formalmente

### Entregaveis

- [x] Criar o runner de cenarios baseado em MAVSDK
- [x] Definir contratos de conexao com o autopilot em simulação
- [x] Implementar comandos de arm, takeoff, hover, waypoint e land
- [x] Registrar asserts basicos de telemetria para cada comando
- [x] Garantir que o runner falhe de forma clara quando o simulador nao responder

### Validação

- `bash scripts/scenarios/validate-phase-2.sh`
- `bash scripts/scenarios/validate-phase-2-container.sh`
- `PYTHONPATH=packages/shared-py/src python3 -m drone_scenarios takeoff_land --backend fake-success --scenario-file simulation/scenarios/takeoff_land.json --output json`
- `rg -n "takeoff|land|waypoint" scripts simulation robotics`

### Criterios de aceite

- Um cenário consegue mandar o veiculo de armamento ate pouso.
- O runner diferencia sucesso, timeout e falha de conexao.
- A execucao fica reproduzivel em ambiente limpo.
- A validacao local passa com backend fake e a validacao real passa contra `PX4 SITL + Gazebo Harmonic`.
- A Fase 2 so e considerada concluida quando `bash scripts/scenarios/validate-phase-2-container.sh` retornar sucesso no ambiente oficial Jammy + Harmonic.

## Fase 3 - ROS 2 bridge

### Objetivo

Criar o workspace ROS 2, os pacotes de dominio e as bridges necessarias para desacoplar mission, safety, perception e telemetria do controle direto.

### Status da fase

- [x] Workspace ROS 2 materializado com pacotes compilaveis
- [x] `drone_msgs` consolidado como contrato de dominio
- [x] `drone_px4` criado como fronteira de adaptação para PX4
- [x] `drone_bringup` criado com launch e params externos
- [x] QoS, topicos e fronteiras documentados
- [x] Build, test e launch validados no ambiente oficial Humble/Jammy
- [x] Bridge real com `px4_msgs` e uXRCE-DDS validada em runtime
- [x] `VehicleCommandStatus` exposto como contrato de ACK do autopilot
- [x] Telemetria ROS 2 observada durante o cenario MAVSDK oficial

### Entregaveis

- [x] Inicializar `robotics/ros2_ws/`
- [x] Consolidar `px4_msgs` e `drone_msgs`
- [x] Criar `drone_bringup`
- [x] Criar `drone_px4`
- [x] Definir launch files e params externos
- [x] Documentar QoS, topicos e fronteiras entre pacotes
- [x] Consumir topicos reais de PX4 via `/fmu/out/*`
- [x] Encaminhar `VehicleCommand` para `/fmu/in/vehicle_command`
- [x] Publicar `VehicleCommandStatus` a partir de `VehicleCommandAck`
- [x] Validar observacao de takeoff e land do cenário real pelo tópico `/drone/vehicle_state`

### Validação

- `bash robotics/ros2_ws/scripts/validate-workspace.sh`
- `bash robotics/ros2_ws/scripts/validate-phase-3-container.sh --check`
- `bash robotics/ros2_ws/scripts/validate-phase-3-container.sh`
- `colcon build --symlink-install`
- `colcon test`
- `ros2 launch drone_bringup bringup.launch.py`
- `ros2 topic echo /drone/vehicle_state --once`
- `ros2 topic pub --once /drone/vehicle_command drone_msgs/msg/VehicleCommand "{command: arm, target_altitude_m: 0.0}"`

### Criterios de aceite

- O workspace compila.
- As mensagens do dominio reduzem acoplamento com detalhes internos do PX4.
- O bringup descreve claramente a ordem de subida dos nodes.
- O grafo ROS 2 sobe no ambiente oficial Humble/Jammy contra `PX4 SITL + Gazebo Harmonic + Micro XRCE-DDS Agent`.
- O `drone_px4` aceita comandos de alto nivel e publica `VehicleState` a partir de topicos reais de PX4 em runtime.
- O `drone_px4` publica `VehicleCommandStatus` a partir de `VehicleCommandAck` real do autopilot.
- A validacao oficial observa `connected`, `armed`, voo e pouso em `/drone/vehicle_state` durante o cenário `takeoff_land`.
- A Fase 3 so e considerada concluida quando `bash robotics/ros2_ws/scripts/validate-phase-3-container.sh` retornar sucesso no ambiente oficial Humble/Jammy.

## Fase 4 - Missão

### Objetivo

Implementar a orquestracao de missao com estado explicito, sem misturar safety com a logica principal de patrulha.

### Status da fase

- [x] `mission_manager_node` materializado no workspace ROS 2
- [x] State machine de missao implementada e coberta por testes
- [x] Sequencia real `arm -> takeoff -> hover -> patrol -> return-to-home -> land` validada
- [x] Abort seguro implementado como fallback terminal da fase
- [x] Validacao E2E oficial concluida contra `PX4 SITL + Gazebo Harmonic + Micro XRCE-DDS Agent`

### Entregaveis

- [x] Criar `mission_manager_node`
- [x] Definir state machine de mission
- [x] Cobrir arm, takeoff, hover, patrol, return-to-home e land
- [x] Adicionar fallback seguro de abort
- [x] Criar testes unitarios para transicoes de estado
- [x] Publicar `MissionStatus` com fase, terminalidade e ultimo comando encaminhado
- [x] Validar `patrol_basic` por ROS 2 sem bypass direto para MAVSDK no modulo de missao
- [x] Configurar os parametros runtime minimos do PX4 exigidos pelo baseline simulation-first da patrulha

### Validação

- `bash robotics/ros2_ws/scripts/validate-workspace.sh`
- `bash robotics/ros2_ws/scripts/validate-phase-4.sh`
- `bash robotics/ros2_ws/scripts/validate-phase-4-container.sh --check`
- `bash robotics/ros2_ws/scripts/validate-phase-4-container.sh`
- `PYTHONPATH=robotics/ros2_ws/src/drone_mission python3 -m unittest robotics/ros2_ws/src/drone_mission/test/test_ros2_gateway.py`
- `colcon test --packages-select drone_mission`
- `rg -n "state machine|abort|return-to-home|patrol" robotics`

### Criterios de aceite

- A missao executa uma rota basica de patrulha.
- As transicoes de estado sao previsiveis e testadas.
- O modulo de missao nao assume responsabilidade de safety.
- O progresso da missao e exposto em `/drone/mission_status` com `phase`, `completed`, `aborted`, `failed`, `terminal`, `succeeded` e `last_command`.
- O gateway ROS 2 usa `VehicleCommandStatus` real como ACK transacional e `VehicleState` real como gate canonico de estado antes de `takeoff`, durante voo, patrulha e pouso.
- A Fase 4 so e considerada concluida quando `bash robotics/ros2_ws/scripts/validate-phase-4-container.sh` retornar sucesso no ambiente oficial Humble/Jammy.

### Hardening backlog da fase

- [x] Fortalecer o `drone_px4` para que `VehicleState.armed` seja canonico o bastante para voltar a ser gate obrigatorio depois do ACK de `arm`
- [x] Revisar a observabilidade do bridge sobre `vehicle_status` e demais topicos de estado do PX4 para reduzir dependencia de fallback por etapa
- [x] Adicionar validacao oficial especifica que prove `VehicleCommandStatus.accepted=true` seguido de `VehicleState.armed=true` no mesmo fluxo de arm
- [x] Manter esse hardening separado da Fase 5 para nao misturar seguranca com semantica basica do bridge

## Fase 5 - Safety

### Objetivo

Adicionar gerenciamento de safety para geofence, perda de link, failsafes e falhas injetadas em simulacao.

### Status da fase

- [x] `safety_manager_node` materializado no workspace ROS 2
- [x] Politica de safety separada da state machine de missao
- [x] Respostas reais de `abort`, `land` e `return_to_home` validadas
- [x] Tres falhas oficiais validadas em runtime real com stack isolado por caso
- [x] Validacao E2E oficial concluida contra `PX4 SITL + Gazebo Harmonic + Micro XRCE-DDS Agent`

### Entregaveis

- [x] Criar `safety_manager_node`
- [x] Definir regras de geofence
- [x] Cobrir perda de GPS, RC e data link
- [x] Cobrir travamento de node de percepção e atraso excessivo
- [x] Definir comportamento de abort e fallback seguro
- [x] Publicar `SafetyStatus` e `SafetyFault` no dominio
- [x] Integrar o safety no bringup oficial do workspace
- [x] Validar `geofence_breach`, `failsafe_gps_loss` e `failsafe_rc_loss` em runtime real com isolamento por caso

### Validação

- `bash robotics/ros2_ws/scripts/validate-workspace.sh`
- `bash robotics/ros2_ws/scripts/validate-phase-5.sh`
- `bash robotics/ros2_ws/scripts/validate-phase-5-container.sh --check`
- `bash robotics/ros2_ws/scripts/validate-phase-5-container.sh`
- `colcon test --packages-select drone_safety`
- `rg -n "geofence|failsafe|loss|timeout|abort" robotics`

### Criterios de aceite

- Pelo menos tres falhas simuladas disparam respostas esperadas.
- O sistema reage de forma deterministica a eventos de safety.
- A politica de safety permanece separada da logica de missao.
- O validador oficial prova `geofence_breach`, `gps_loss` e `rc_loss` no ambiente oficial Humble/Jammy.
- Cada caso oficial da Fase 5 sobe um runtime isolado de `PX4 SITL + Gazebo Harmonic + Micro XRCE-DDS Agent`.
- A Fase 5 so e considerada concluida quando `bash robotics/ros2_ws/scripts/validate-phase-5-container.sh` retornar sucesso no ambiente oficial Humble/Jammy.

## Fase 6 - Percepção

### Objetivo

Introduzir o pipeline de camera simulada, pre-processamento, deteccao e tracking, gerando eventos consumiveis pelo sistema de autonomia.

### Entregaveis

- [x] Criar `camera_input_node`
- [x] Criar `object_detector_node`
- [x] Criar `tracker_node`
- [x] Definir eventos visuais de entrada e saida
- [x] Documentar a interface entre percepção e missão

### Validação

- `pytest`
- `bash robotics/ros2_ws/scripts/validate-workspace.sh`
- `bash robotics/ros2_ws/scripts/validate-phase-6.sh`
- `bash robotics/ros2_ws/scripts/validate-phase-6-container.sh --check`
- `bash robotics/ros2_ws/scripts/validate-phase-6-container.sh`
- `colcon test --packages-select drone_perception`
- `rg -n "camera|detector|tracker|opencv|event" robotics`

### Criterios de aceite

- O pipeline consome `/simulation/camera/image_raw` e materializa `/drone/perception/preprocessed_image`, `/drone/perception/detection`, `/drone/perception/tracked_object`, `/drone/perception/event` e `/drone/perception_heartbeat`.
- A missao entra em `hover` esperando visual lock e so avanca para `patrol` depois de observar estado persistente de tracking em `/drone/perception/tracked_object`.
- `PerceptionEvent` continua exposto no dominio como contrato de notificacao e observabilidade, sem carregar frame bruto nem detalhes de OpenCV para mission ou safety.
- O comportamento degradado quando a percepcao falha esta definido e testado por `perception_timeout -> safety abort -> land`.
- O validador oficial da Fase 6 prova `visual_lock_gate` e `perception_timeout` no ambiente oficial Humble/Jammy, com runtime isolado por caso.
- A Fase 6 so e considerada concluida quando `bash robotics/ros2_ws/scripts/validate-phase-6-container.sh` retornar sucesso no ambiente oficial Humble/Jammy.

## Fase 7 - Operação

### Objetivo

Publicar telemetria, logs, metricas, replay e dashboard para observabilidade operacional do stack de simulação.

### Status da fase

- [x] `telemetry_bridge_node` materializado no workspace ROS 2
- [x] API de telemetria implementada em `services/telemetry-api/`
- [x] Dashboard operacional implementado em `apps/dashboard/`
- [x] Persistencia de eventos, snapshots, metricas e replay definida
- [x] Validador oficial da fase consolidado com `test` e `build`
- [x] Contrato tecnico da fase registrado em `docs/contracts/PHASE-7-OPERATIONS-CONTRACT.md`

### Entregaveis

- [x] Criar `telemetry_bridge_node`
- [x] Criar API de telemetria em `services/telemetry-api/`
- [x] Criar dashboard em `apps/dashboard/`
- [x] Definir persistencia de logs, metricas e eventos
- [x] Definir suporte a replay
- [x] Documentar o contrato operacional da fase
- [x] Adicionar validacao oficial da fase com backend e frontend

### Validação

- `bash robotics/ros2_ws/scripts/validate-workspace.sh`
- `bash robotics/ros2_ws/scripts/validate-phase-7.sh`
- `PYTHONPATH=robotics/ros2_ws/src/drone_telemetry python3 -m unittest discover -s robotics/ros2_ws/src/drone_telemetry/test -p "test_*.py"`
- `PYTHONPATH=services/telemetry-api python3 -m pytest services/telemetry-api/tests -q`
- `npm test --prefix apps/dashboard`
- `npm run --prefix apps/dashboard build`
- `rg -n "telemetry|metrics|replay|dashboard|log" robotics services apps`

### Criterios de aceite

- O `telemetry_bridge_node` consome contratos de dominio do ROS 2 e produz envelopes operacionais pequenos e auditaveis.
- A API persiste eventos por `run_id` e materializa `snapshot`, `metrics`, `events`, `runs` e `replay`.
- O estado operacional fica visivel durante a simulacao.
- O historico de eventos pode ser auditado depois da execucao.
- O dashboard consome somente a API de telemetria e nao mistura regra de missao com logica de apresentacao.
- A Fase 7 so e considerada concluida quando `bash robotics/ros2_ws/scripts/validate-phase-7.sh` retornar sucesso.

## Fase 8 - Maturidade de simulacao

### Objetivo

Fechar o ciclo com confiabilidade, cobertura de cenarios, CI e padronizacao para que a simulação seja repetivel e evolutiva.

### Status da fase

- [x] Suite terminal da fase criada em `scripts/ci/validate-phase-8.sh`
- [x] Cenarios obrigatorios consolidados na matriz final da simulacao
- [x] Cobertura oficial dos modos de falha registrada e consolidada
- [x] CI de maturidade adicionada em `.github/workflows/simulation-maturity.yml`
- [x] Documentacao de operacao e troubleshooting publicada
- [x] Criterios de migracao futura para hardware registrados sem quebrar a regra simulation-first

### Entregaveis

- [x] Consolidar cenarios obrigatorios: `takeoff_land`, `patrol_basic`, `failsafe_gps_loss`, `failsafe_rc_loss`, `geofence_breach`
- [x] Garantir cobertura dos modos de falha obrigatorios
- [x] Adicionar CI com validacao estrutural, testes e smoke scenarios
- [x] Produzir documentação de operacao e troubleshooting
- [x] Revisar critérios de aceite para futura migração para hardware
- [x] Publicar contrato tecnico final da fase

### Validação

- `bash scripts/ci/validate-phase-8.sh --check`
- `bash scripts/ci/validate-phase-8.sh --local-only`
- `bash scripts/ci/validate-phase-8.sh`
- `python3 -m unittest scripts.tooling.tests.test_phase0_structure`
- `bash robotics/ros2_ws/scripts/validate-workspace.sh`
- `npm run --prefix apps/dashboard build`
- `rg -n "phase-8|maturity|troubleshooting|hardware" docs scripts .github`

### Criterios de aceite

- Pelo menos um cenario completo roda do inicio ao fim sem intervenção manual.
- Tres ou mais falhas simuladas sao reproduziveis e observaveis.
- A documentacao permite que outro agente execute a mesma sequencia.
- A fase so conta como concluida quando `bash scripts/ci/validate-phase-8.sh` passa no ambiente oficial.

## Definição de pronto do projeto

- O stack completo sobe em simulacao de forma reproduzivel.
- A missao basica e os failsafes foram exercitados.
- A percepcao gera eventos uteis para o dominio.
- Telemetria, logs, metricas e replay estao disponiveis.
- A CI cobre a estrutura e os cenarios essenciais.
- O projeto continua explicitamente simulation-first.
