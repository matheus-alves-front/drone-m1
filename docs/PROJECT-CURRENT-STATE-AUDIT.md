# PROJECT-CURRENT-STATE-AUDIT.md

## Escopo desta auditoria

Esta auditoria descreve o estado atual do repositório **a partir do código, scripts, configurações e documentação versionados**, sem implementar mudanças nem reexecutar toda a suíte nesta rodada.

Leitura-base usada nesta auditoria:

- `docs/PROJECT-SCOPE.md`
- `docs/SIMULATION-ARCHITECTURE.md`
- `docs/PROJECT-ARCHITECTURE.md`
- `docs/MONOREPO-STRUCTURE.md`
- `docs/DEVELOPMENT-STANDARDS.md`
- `docs/TESTING-AND-FAILURE-MODEL.md`
- `docs/CHECKLIST-FRAMEWORK.md`
- `README.md`
- `docs/PROJECT-EXECUTION-CHECKLIST.md`

Legenda usada abaixo:

- `existe`: há arquivo, pacote ou entrypoint versionado.
- `funciona`: há superfície implementada e validada por script/validator oficial do repositório.
- `parcial`: existe, mas com escopo limitado, dependência forte de ambiente, trilha legada ou ausência de interface operacional clara.
- `não existe`: não há superfície operacional clara no repositório hoje.

## 1. Visão geral do estado atual do projeto

### Resumo executivo

O repositório já materializa um stack simulation-first completo em camadas:

- simulação mínima com `PX4 SITL + Gazebo Harmonic + Micro XRCE-DDS Agent`
- runner MAVSDK para cenário simples
- fronteira ROS 2 real com `px4_msgs` e `drone_msgs`
- missão, safety, percepção, telemetria e dashboard
- validadores locais e runtime/containerizados por fase
- CI em camadas para bootstrap, qualidade local e runtime smoke/autonomy

O ponto forte do projeto hoje é a **correção arquitetural em camadas com provas de runtime por fase**. O principal limite atual é que o sistema ainda não se apresenta como **plataforma controladora unificada**; ele continua operado por uma combinação de:

- shell scripts
- validadores por fase
- tópicos ROS 2
- um runner MAVSDK específico
- uma API/dash de observabilidade essencialmente read-only

### O que realmente já está implementado

#### Implementado e com superfície operacional clara

- Stack mínimo de simulação:
  - `scripts/sim/start.sh`
  - `scripts/sim/stop.sh`
  - `scripts/sim/check-gz-harmonic-cli.sh`
  - `scripts/sim/validate-phase-1.sh`
  - `scripts/sim/validate-phase-1-container.sh`
- Runner MAVSDK reutilizável:
  - `packages/shared-py/src/drone_scenarios/cli.py`
  - `packages/shared-py/src/drone_scenarios/runner.py`
  - `packages/shared-py/src/drone_scenarios/gateways/mavsdk_backend.py`
  - `scripts/scenarios/run_scenario.sh`
  - `scripts/scenarios/run_takeoff_land.sh`
- Workspace ROS 2 com pacotes reais:
  - `robotics/ros2_ws/src/drone_px4/`
  - `robotics/ros2_ws/src/drone_mission/`
  - `robotics/ros2_ws/src/drone_safety/`
  - `robotics/ros2_ws/src/drone_perception/`
  - `robotics/ros2_ws/src/drone_telemetry/`
  - `robotics/ros2_ws/src/drone_bringup/`
  - `robotics/ros2_ws/src/drone_msgs/`
  - `robotics/ros2_ws/src/px4_msgs/`
- Bringup principal ROS 2:
  - `robotics/ros2_ws/src/drone_bringup/drone_bringup/launch/bringup.launch.py`
- Telemetry API:
  - `services/telemetry-api/telemetry_api/app.py`
  - `services/telemetry-api/telemetry_api/main.py`
- Dashboard React:
  - `apps/dashboard/src/App.tsx`
  - `apps/dashboard/src/lib/api.ts`
  - `apps/dashboard/package.json`
- Suite final:
  - `scripts/ci/validate-phase-8.sh`
  - `.github/workflows/simulation-maturity.yml`

#### Implementado, mas com escopo limitado ou fragmentado

- Runner MAVSDK cobre **apenas** `takeoff_land`:
  - `packages/shared-py/src/drone_scenarios/cli.py`
  - `scripts/scenarios/run_scenario.sh`
- Contratos de cenário existem para fases posteriores, mas não possuem wrapper CLI equivalente:
  - `simulation/scenarios/patrol_basic.json`
  - `simulation/scenarios/geofence_breach.json`
  - `simulation/scenarios/failsafe_gps_loss.json`
  - `simulation/scenarios/failsafe_rc_loss.json`
  - `simulation/scenarios/perception_target_tracking.json`
- `packages/shared-ts/` existe, mas hoje está mais para placeholder/contrato potencial do que peça central em uso:
  - `packages/shared-ts/src/index.ts`
  - `packages/shared-ts/src/telemetry.ts`
- Telemetry API tem **duas trilhas de código** convivendo:
  - trilha operacional atual: `services/telemetry-api/telemetry_api/`
  - trilha legada/paralela: `services/telemetry-api/src/telemetry_api/`

#### Scaffold ou asset ainda mínimo

- `simulation/gazebo/models/` tem apenas documentação:
  - `simulation/gazebo/models/README.md`
- `simulation/gazebo/resources/` tem apenas documentação:
  - `simulation/gazebo/resources/README.md`
- a world própria do repositório é mínima:
  - `simulation/gazebo/worlds/harmonic_minimal.sdf`
- o veículo visual usado no runtime vem do stack PX4/Gazebo (`gz_x500`), não de um modelo customizado versionado no monorepo:
  - `scripts/sim/start.sh`
  - `third_party/PX4-Autopilot/`

### O que está funcional em runtime

Com base nos validators e contratos operacionais do repositório, o que hoje está tratado como runtime-proven é:

- stack mínimo `PX4 SITL + Gazebo Harmonic`:
  - `scripts/sim/validate-phase-1-container.sh`
- `takeoff_land` via MAVSDK:
  - `scripts/scenarios/validate-phase-2-container.sh`
- bridge ROS 2 real com PX4:
  - `robotics/ros2_ws/scripts/validate-phase-3-container.sh`
- `patrol_basic` via domínio ROS 2:
  - `robotics/ros2_ws/scripts/validate-phase-4-container.sh`
- safety oficial:
  - `robotics/ros2_ws/scripts/validate-phase-5-container.sh`
- percepção oficial:
  - `robotics/ros2_ws/scripts/validate-phase-6-container.sh`
- telemetria, replay e dashboard:
  - `robotics/ros2_ws/scripts/validate-phase-7.sh`
- suíte consolidada:
  - `scripts/ci/validate-phase-8.sh`

### O que depende de ambiente específico

#### Depende explicitamente do baseline oficial

- baseline oficial:
  - Ubuntu 22.04
  - ROS 2 Humble
  - Gazebo Harmonic
  - PX4 `v1.16.1`
  - `px4_msgs` em linha `release/1.16`
- referências:
  - `README.md`
  - `.devcontainer/devcontainer.json`
  - `docs/runbooks/LOCAL-SIMULATION-GUIDE.md`

#### Depende de Docker para a prova oficial de runtime

- fases 1, 2, 3, 4, 5 e 6 dependem de validadores containerizados para a prova oficial:
  - `scripts/sim/validate-phase-1-container.sh`
  - `scripts/scenarios/validate-phase-2-container.sh`
  - `robotics/ros2_ws/scripts/validate-phase-3-container.sh`
  - `robotics/ros2_ws/scripts/validate-phase-4-container.sh`
  - `robotics/ros2_ws/scripts/validate-phase-5-container.sh`
  - `robotics/ros2_ws/scripts/validate-phase-6-container.sh`

#### Depende de setup local manual

- modo visual local com Gazebo depende de pré-requisitos do host:
  - `scripts/sim/start.sh`
  - `docs/runbooks/LOCAL-SIMULATION-GUIDE.md`
- ROS 2 manual local depende de instalação real do Humble:
  - `docs/runbooks/LOCAL-SIMULATION-GUIDE.md`
- dashboard depende de `npm install`:
  - `apps/dashboard/package.json`
- telemetry API depende de `pip install -r services/telemetry-api/requirements.txt`:
  - `services/telemetry-api/requirements.txt`

#### Dependência parcial ou inconsistente

- o devcontainer declara o baseline, mas **não provisiona sozinho** ROS 2 Humble nem Gazebo Harmonic; ele usa imagem base Ubuntu e apenas roda pós-comandos leves:
  - `.devcontainer/devcontainer.json`
- isso significa que o devcontainer hoje é mais um marcador de baseline do que um ambiente completo self-contained para toda a operação do produto.

## 2. Inventário de entrypoints reais

### Entry points de bootstrap e validação

| Entry point | Tipo | Estado |
|---|---|---|
| `scripts/bootstrap/validate-phase-0.sh` | shell validator | `existe`, `funciona` |
| `scripts/sim/validate-phase-1.sh` | shell validator | `existe`, `funciona` |
| `scripts/sim/validate-phase-1-container.sh` | shell validator runtime | `existe`, `funciona` |
| `scripts/scenarios/validate-phase-2.sh` | shell validator | `existe`, `funciona` |
| `scripts/scenarios/validate-phase-2-container.sh` | shell validator runtime | `existe`, `funciona` |
| `robotics/ros2_ws/scripts/validate-workspace.sh` | shell validator | `existe`, `funciona` |
| `robotics/ros2_ws/scripts/validate-phase-3-container.sh` | shell validator runtime | `existe`, `funciona` |
| `robotics/ros2_ws/scripts/validate-phase-4.sh` | shell validator | `existe`, `funciona` |
| `robotics/ros2_ws/scripts/validate-phase-4-container.sh` | shell validator runtime | `existe`, `funciona` |
| `robotics/ros2_ws/scripts/validate-phase-5.sh` | shell validator | `existe`, `funciona` |
| `robotics/ros2_ws/scripts/validate-phase-5-container.sh` | shell validator runtime | `existe`, `funciona` |
| `robotics/ros2_ws/scripts/validate-phase-6.sh` | shell validator | `existe`, `funciona` |
| `robotics/ros2_ws/scripts/validate-phase-6-container.sh` | shell validator runtime | `existe`, `funciona` |
| `robotics/ros2_ws/scripts/validate-phase-7.sh` | shell validator | `existe`, `funciona` |
| `scripts/ci/validate-phase-8.sh` | shell validator consolidado | `existe`, `funciona` |

### Entry points de simulação

| Entry point | Tipo | Estado | Observação |
|---|---|---|---|
| `scripts/sim/start.sh` | orquestrador shell | `existe`, `funciona` | sobe `MicroXRCEAgent + PX4 SITL + Gazebo` |
| `scripts/sim/stop.sh` | orquestrador shell | `existe`, `funciona` | para o stack mínimo |
| `scripts/sim/check-gz-harmonic-cli.sh` | preflight shell | `existe`, `funciona` | verifica CLI do Gazebo |
| `scripts/sim/build-phase-1-container-image.sh` | build Docker | `existe`, `funciona` | imagem Jammy/Harmonic |
| `scripts/sim/vendor-px4-submodule.sh` | vendor shell | `existe`, `funciona` | prepara submodule PX4 |

### Entry points MAVSDK / cenários

| Entry point | Tipo | Estado | Observação |
|---|---|---|---|
| `python3 -m drone_scenarios takeoff_land` | CLI Python | `existe`, `funciona` | implementado em `packages/shared-py/src/drone_scenarios/cli.py` |
| `scripts/scenarios/run_scenario.sh` | wrapper shell | `existe`, `funciona` | aceita de fato só `takeoff_land` |
| `scripts/scenarios/run_takeoff_land.sh` | wrapper shell | `existe`, `funciona` | aponta para `simulation/scenarios/takeoff_land.json` |

### Entry points ROS 2

#### Bringup

- principal launch file:
  - `robotics/ros2_ws/src/drone_bringup/drone_bringup/launch/bringup.launch.py`
- comando operacional:
  - `ros2 launch drone_bringup bringup.launch.py`

#### Console scripts ROS 2

| Pacote | Executável |
|---|---|
| `drone_px4` | `px4_bridge_node` |
| `drone_mission` | `mission_manager_node` |
| `drone_safety` | `safety_manager_node` |
| `drone_perception` | `camera_input_node` |
| `drone_perception` | `object_detector_node` |
| `drone_perception` | `tracker_node` |
| `drone_telemetry` | `telemetry_bridge_node` |

Referências:

- `robotics/ros2_ws/src/drone_px4/setup.py`
- `robotics/ros2_ws/src/drone_mission/setup.py`
- `robotics/ros2_ws/src/drone_safety/setup.py`
- `robotics/ros2_ws/src/drone_perception/setup.py`
- `robotics/ros2_ws/src/drone_telemetry/setup.py`

### Entry points utilitários ROS 2

- `robotics/ros2_ws/scripts/publish_sim_camera_stream.py`
- `robotics/ros2_ws/scripts/wait_for_vehicle_state.py`
- `robotics/ros2_ws/scripts/wait_for_command_status.py`
- `robotics/ros2_ws/scripts/wait_for_mission_status.py`
- `robotics/ros2_ws/scripts/wait_for_safety_status.py`
- `robotics/ros2_ws/scripts/wait_for_vision_detection.py`
- `robotics/ros2_ws/scripts/wait_for_tracked_object.py`
- `robotics/ros2_ws/scripts/wait_for_perception_event.py`
- `robotics/ros2_ws/scripts/wait_for_perception_heartbeat.py`

Esses entrypoints existem e funcionam como ferramentas de prova/observação, mas **não formam uma interface de produto**.

### Entry points backend / frontend

#### Telemetry API

- entrypoint operacional atual:
  - `services/telemetry-api/telemetry_api/main.py`
- comando esperado:
  - `python -m telemetry_api.main`
  - ou `uvicorn telemetry_api.main:app`

#### Dashboard

- `npm run --prefix apps/dashboard dev`
- `npm run --prefix apps/dashboard build`
- `npm test --prefix apps/dashboard`

Referências:

- `apps/dashboard/package.json`
- `apps/dashboard/src/App.tsx`
- `apps/dashboard/src/lib/api.ts`

## 3. Mapeamento de capacidades já existentes

| Capacidade | Estado | Evidência principal | Observação |
|---|---|---|---|
| voo básico | `funciona` | `scripts/sim/start.sh`, `scripts/sim/validate-phase-1-container.sh` | stack mínimo sobe |
| `takeoff_land` | `funciona` | `packages/shared-py/src/drone_scenarios/runner.py`, `scripts/scenarios/run_takeoff_land.sh`, `scripts/scenarios/validate-phase-2-container.sh` | capacidade mais amigável ao operador hoje |
| `patrol` | `funciona`, mas `parcial` como superfície operacional | `simulation/scenarios/patrol_basic.json`, `robotics/ros2_ws/src/drone_mission/drone_mission/mission_manager_node.py`, `robotics/ros2_ws/scripts/validate-phase-4-container.sh` | existe via ROS 2/missão, não via wrapper simples |
| missão | `funciona` | `robotics/ros2_ws/src/drone_mission/`, `robotics/ros2_ws/src/drone_bringup/config/drone_mission.yaml` | controlada por tópico ROS 2 |
| safety | `funciona` | `robotics/ros2_ws/src/drone_safety/`, `robotics/ros2_ws/scripts/validate-phase-5-container.sh` | geofence/gps_loss/rc_loss runtime; `data_link_loss` e `perception_latency` ficam mais em regra/teste |
| percepção | `funciona` | `robotics/ros2_ws/src/drone_perception/`, `robotics/ros2_ws/scripts/validate-phase-6-container.sh` | pipeline sintético com `Image -> Detection -> Tracking -> Heartbeat` |
| telemetria | `funciona` | `robotics/ros2_ws/src/drone_telemetry/`, `services/telemetry-api/telemetry_api/app.py`, `robotics/ros2_ws/scripts/validate-phase-7.sh` | bridge ROS 2 -> HTTP |
| replay | `funciona` | `services/telemetry-api/telemetry_api/store.py`, `/api/v1/replay/{run_id}` | persistência JSONL por run |
| dashboard | `funciona`, mas read-only | `apps/dashboard/src/App.tsx`, `apps/dashboard/src/lib/api.ts`, `robotics/ros2_ws/scripts/validate-phase-7.sh` | observabilidade, não controle |
| fault injection | `funciona`, mas `parcial` como UX | `drone_safety` consome `/drone/safety_fault`; `validate-phase-5-container.sh` publica faults | injeção existe via tópico bruto, não via painel/API |
| camera pipeline | `funciona`, mas depende de ambiente | `publish_sim_camera_stream.py`, `drone_perception` nodes, `validate-phase-6-container.sh` | oficial via stream sintético; câmera visual host depende de GStreamer/plugin |
| observabilidade | `funciona` | `drone_telemetry`, Telemetry API, dashboard, websocket | forte como leitura |
| CI/runtime | `funciona` | `.github/workflows/bootstrap-check.yml`, `.github/workflows/simulation-maturity.yml` | CI em camadas |

### Observações por capacidade

#### Voo básico

- existe runtime real em `scripts/sim/start.sh`
- existe modo visual local com `PHASE1_HEADLESS=0`
- depende de ambiente PX4/Gazebo/MicroXRCE e, para o host local, de pré-requisitos documentados em `docs/runbooks/LOCAL-SIMULATION-GUIDE.md`

#### `takeoff_land`

- é a única capacidade de cenário hoje com:
  - contrato JSON
  - CLI Python
  - wrapper shell simples
  - backend fake
  - backend MAVSDK
- referências:
  - `simulation/scenarios/takeoff_land.json`
  - `packages/shared-py/src/drone_scenarios/cli.py`
  - `packages/shared-py/src/drone_scenarios/runner.py`

#### `patrol`

- está implementado como missão de domínio ROS 2:
  - `simulation/scenarios/patrol_basic.json`
  - `robotics/ros2_ws/src/drone_mission/drone_mission/loader.py`
  - `robotics/ros2_ws/src/drone_mission/drone_mission/mission_manager_node.py`
- não existe hoje um `run_patrol_basic.sh` equivalente ao `takeoff_land`

#### Safety

- política separada de missão:
  - `robotics/ros2_ws/src/drone_safety/drone_safety/rules.py`
  - `robotics/ros2_ws/src/drone_safety/drone_safety/safety_manager_node.py`
- faults oficiais com contrato JSON:
  - `simulation/scenarios/geofence_breach.json`
  - `simulation/scenarios/failsafe_gps_loss.json`
  - `simulation/scenarios/failsafe_rc_loss.json`
- injeção manual hoje acontece via tópico ROS 2 `/drone/safety_fault`

#### Percepção

- pipeline é real e separado:
  - `camera_input_node`
  - `object_detector_node`
  - `tracker_node`
- o feed oficial de validação é sintético:
  - `robotics/ros2_ws/scripts/publish_sim_camera_stream.py`
- o gate da missão usa estado persistente em `TrackedObject`, não evento transitório:
  - `robotics/ros2_ws/src/drone_mission/drone_mission/mission_manager_node.py`

## 4. Mapeamento arquitetural do código atual

### Pacotes ROS 2 existentes

| Pacote | Papel |
|---|---|
| `drone_bringup` | launch e params externos |
| `drone_msgs` | contratos de domínio |
| `drone_mission` | orquestração e state machine |
| `drone_px4` | fronteira ROS 2 <-> PX4 |
| `drone_safety` | política de safety |
| `drone_perception` | câmera, detector, tracker |
| `drone_telemetry` | bridge ROS 2 -> backend |
| `px4_msgs` | mensagens oficiais PX4 |

Referências:

- `robotics/ros2_ws/src/*/package.xml`
- `robotics/ros2_ws/src/*/setup.py`

### Services e apps existentes

#### Services

- `services/telemetry-api/telemetry_api/`
  - runtime atual da API
- `services/telemetry-api/src/telemetry_api/`
  - trilha legada/paralela ainda versionada

#### Apps

- `apps/dashboard/`
  - frontend React/Vite
  - consome somente API de telemetria

### Scripts existentes

#### Shell

- bootstrap:
  - `scripts/bootstrap/validate-phase-0.sh`
- simulação:
  - `scripts/sim/start.sh`
  - `scripts/sim/stop.sh`
  - `scripts/sim/check-gz-harmonic-cli.sh`
  - `scripts/sim/build-phase-1-container-image.sh`
  - `scripts/sim/validate-phase-1.sh`
  - `scripts/sim/validate-phase-1-container.sh`
  - `scripts/sim/vendor-px4-submodule.sh`
- cenários:
  - `scripts/scenarios/run_scenario.sh`
  - `scripts/scenarios/run_takeoff_land.sh`
  - `scripts/scenarios/validate-phase-2.sh`
  - `scripts/scenarios/validate-phase-2-container.sh`
- ROS 2:
  - `robotics/ros2_ws/scripts/build-phase-3-container-image.sh`
  - `robotics/ros2_ws/scripts/validate-phase-3-container.sh`
  - `robotics/ros2_ws/scripts/validate-phase-4.sh`
  - `robotics/ros2_ws/scripts/validate-phase-4-container.sh`
  - `robotics/ros2_ws/scripts/validate-phase-5.sh`
  - `robotics/ros2_ws/scripts/validate-phase-5-container.sh`
  - `robotics/ros2_ws/scripts/validate-phase-6.sh`
  - `robotics/ros2_ws/scripts/validate-phase-6-container.sh`
  - `robotics/ros2_ws/scripts/validate-phase-7.sh`
  - `robotics/ros2_ws/scripts/validate-workspace.sh`
- suíte final:
  - `scripts/ci/validate-phase-8.sh`

#### Python utilitário

- `scripts/sim/configure_px4_sim_params.py`
- `robotics/ros2_ws/scripts/publish_sim_camera_stream.py`
- waiters `wait_for_*`

### Contratos e messages existentes

#### Contratos de cenário

- `simulation/scenarios/takeoff_land.json`
- `simulation/scenarios/patrol_basic.json`
- `simulation/scenarios/geofence_breach.json`
- `simulation/scenarios/failsafe_gps_loss.json`
- `simulation/scenarios/failsafe_rc_loss.json`
- `simulation/scenarios/perception_target_tracking.json`

#### Contratos de domínio ROS 2

- `robotics/ros2_ws/src/drone_msgs/msg/VehicleState.msg`
- `robotics/ros2_ws/src/drone_msgs/msg/VehicleCommand.msg`
- `robotics/ros2_ws/src/drone_msgs/msg/VehicleCommandStatus.msg`
- `robotics/ros2_ws/src/drone_msgs/msg/MissionCommand.msg`
- `robotics/ros2_ws/src/drone_msgs/msg/MissionStatus.msg`
- `robotics/ros2_ws/src/drone_msgs/msg/SafetyFault.msg`
- `robotics/ros2_ws/src/drone_msgs/msg/SafetyStatus.msg`
- `robotics/ros2_ws/src/drone_msgs/msg/VisionDetection.msg`
- `robotics/ros2_ws/src/drone_msgs/msg/TrackedObject.msg`
- `robotics/ros2_ws/src/drone_msgs/msg/PerceptionEvent.msg`
- `robotics/ros2_ws/src/drone_msgs/msg/PerceptionHeartbeat.msg`

#### Contratos PX4

- `robotics/ros2_ws/src/px4_msgs/msg/*`

### Como as camadas se conectam hoje no código

#### PX4 <-> Gazebo

- orquestrado por `scripts/sim/start.sh`
- binário PX4 vindo de `third_party/PX4-Autopilot/`
- world mínima em `simulation/gazebo/worlds/harmonic_minimal.sdf`
- sim principal usa `gz_x500` do stack PX4/Gazebo, não um modelo do monorepo

#### PX4 <-> ROS 2

- `drone_px4` assina `/fmu/out/*` e publica em `/drone/*`
- `drone_px4` encaminha `/drone/vehicle_command` para `/fmu/in/vehicle_command`
- arquivos principais:
  - `robotics/ros2_ws/src/drone_px4/drone_px4/px4_bridge_node.py`
  - `robotics/ros2_ws/src/drone_px4/drone_px4/state_model.py`

#### ROS 2 <-> missão

- `mission_manager_node` consome:
  - `/drone/vehicle_state`
  - `/drone/vehicle_command_status`
  - `/drone/perception/event`
  - `/drone/perception/tracked_object`
  - `/drone/mission_command`
- publica:
  - `/drone/mission_status`
  - `/drone/vehicle_command`

#### ROS 2 <-> safety

- `safety_manager_node` consome:
  - `/drone/vehicle_state`
  - `/drone/mission_status`
  - `/drone/safety_fault`
  - `/drone/perception_heartbeat`
- publica:
  - `/drone/safety_status`
  - `/drone/mission_command`
  - `/drone/vehicle_command`

#### ROS 2 <-> percepção

- `camera_input_node`: `/simulation/camera/image_raw` -> `/drone/perception/preprocessed_image`
- `object_detector_node`: `/drone/perception/preprocessed_image` -> `/drone/perception/detection` + `/drone/perception/event`
- `tracker_node`: `/drone/perception/detection` -> `/drone/perception/tracked_object` + `/drone/perception/event` + `/drone/perception_heartbeat`

#### ROS 2 <-> backend/dashboard

- `telemetry_bridge_node` consome tópicos de domínio e envia envelopes HTTP para `/api/v1/ingest`
- Telemetry API persiste e serve `snapshot`, `metrics`, `events`, `runs`, `replay`
- dashboard consome a API e o websocket `/ws/telemetry`

## 5. Mapeamento de superfícies de controle existentes

### Controlado hoje por script shell

- subir/parar stack mínimo:
  - `scripts/sim/start.sh`
  - `scripts/sim/stop.sh`
- rodar cenário simples:
  - `scripts/scenarios/run_takeoff_land.sh`
- rodar validações por fase:
  - `scripts/*/validate-*.sh`

### Controlado hoje por MAVSDK

- `takeoff_land`
- comandos de alto nível encapsulados no backend MAVSDK:
  - connect
  - arm
  - set_takeoff_altitude
  - takeoff
  - goto_location
  - land

Referências:

- `packages/shared-py/src/drone_scenarios/gateways/mavsdk_backend.py`
- `packages/shared-py/src/drone_scenarios/runner.py`

### Controlado hoje por tópicos ROS 2

#### Missão

- `/drone/mission_command`
  - `start`
  - `abort`
  - `reset`
- implementação:
  - `robotics/ros2_ws/src/drone_mission/drone_mission/mission_manager_node.py`

#### Veículo

- `/drone/vehicle_command`
  - `arm`
  - `disarm`
  - `takeoff`
  - `land`
  - `return_to_home`
  - `goto`
- encaminhado para PX4 por `drone_px4`

#### Safety fault injection

- `/drone/safety_fault`
- implementação:
  - `robotics/ros2_ws/src/drone_safety/drone_safety/safety_manager_node.py`

### Controlado hoje pelo dashboard

- **nada no plano de atuação**
- o dashboard hoje é somente:
  - snapshot
  - métricas
  - eventos
  - replay
  - runs
  - stream websocket

Referências:

- `apps/dashboard/src/App.tsx`
- `apps/dashboard/src/lib/api.ts`

### Controlado hoje pela Telemetry API

- somente ingestão e leitura
- não há endpoints de ação para:
  - start/stop simulator
  - start/abort mission
  - inject fault
  - run scenario
  - command vehicle

### O que hoje não possui interface operacional clara

- executar `patrol_basic` visualmente por um comando único de produto
- ligar percepção + missão + safety + telemetria + dashboard com um entrypoint de operador único
- injetar falhas via UI ou API de produto
- controlar missão/veículo via dashboard
- acionar cenários de fase 4, 5 e 6 fora dos validators/container scripts
- operar o sistema inteiro como “uma plataforma” em vez de várias camadas técnicas

## 6. Gaps para virar uma control platform unificada

### O que impede o sistema de parecer um produto único

1. O sistema é operado por superfícies fragmentadas.
   - shell scripts para simulação
   - CLI MAVSDK para `takeoff_land`
   - tópicos ROS 2 para missão/safety
   - validators containerizados para provas oficiais
   - dashboard read-only para observabilidade

2. Não existe um modelo central de “ação do operador”.
   - não há API unificada para `start_simulation`, `run_scenario`, `start_mission`, `abort_mission`, `inject_fault`, `reset_run`

3. O dashboard não é control plane.
   - ele lê o estado, mas não atua sobre o sistema
   - não há formulários, ações ou rotas de comando

4. Os cenários mudam de executor por fase.
   - `takeoff_land` usa MAVSDK CLI
   - `patrol_basic` usa ROS 2 mission
   - safety/perception usam validators

### O que impede uma interface centralizadora

- ausência de um backend/orquestrador que seja dono do ciclo:
  - simulação
  - missão
  - safety fault injection
  - percepção
  - telemetria
  - replay
- hoje a API de telemetria não é uma API de controle
- o bringup ROS 2 sobe o grafo, mas não é exposto como capability de produto

### O que precisa ser abstraído

- lifecycle do simulador:
  - hoje é shell puro em `scripts/sim/start.sh` e `scripts/sim/stop.sh`
- operações de missão:
  - hoje são `MissionCommand` em tópico ROS 2
- fault injection:
  - hoje é `SafetyFault` em tópico ROS 2
- cenários:
  - hoje são misto de JSON + runner Python + validators
- inspeção de estado:
  - hoje fica dividida entre ROS topics, logs, API e dashboard

### O que hoje está fragmentado por camada técnica

- controle de voo simples: MAVSDK
- controle de missão: ROS 2
- controle de safety: ROS 2
- observabilidade: Telemetry API + dashboard
- orquestração do stack: shell + Docker

## 7. Gaps para virar MCP/tool no futuro

### Capacidades que já podem ser expostas por API com pouco atrito

- leitura de snapshot operacional:
  - `/api/v1/snapshot`
- leitura de métricas:
  - `/api/v1/metrics`
- leitura de eventos:
  - `/api/v1/events`
- listagem de runs:
  - `/api/v1/runs`
- replay por run:
  - `/api/v1/replay/{run_id}`
- execução de `takeoff_land`:
  - já há contrato JSON + CLI Python + resultado em JSON

### Capacidades que ainda estão acopladas demais

- `patrol_basic`
  - depende de ROS 2 graph + mission_manager + topics + validator
- safety fault injection
  - depende de publicação em tópico ROS 2 cru
- start/stop da simulação
  - depende de shell e env vars
- percepção
  - depende de bringup ROS 2 e publishers específicos

### Contratos que faltam para uma superfície MCP/tool forte

- contrato formal de ações:
  - iniciar simulação
  - parar simulação
  - iniciar missão
  - abortar missão
  - resetar missão
  - injetar falha
  - limpar falha
  - executar cenário
  - consultar estado consolidado
- contrato formal de sessão/run operacional
  - hoje `run_id` está forte na telemetria
  - mas não é o identificador central de todo o control plane
- contrato formal de capability discovery
  - hoje as capacidades estão implícitas em scripts e tópicos

### O que precisa virar action/capability formal

- `simulation.start`
- `simulation.stop`
- `scenario.takeoff_land.run`
- `scenario.patrol_basic.run`
- `mission.start`
- `mission.abort`
- `mission.reset`
- `vehicle.arm`
- `vehicle.disarm`
- `vehicle.land`
- `vehicle.return_to_home`
- `safety.inject_fault`
- `safety.clear_fault`
- `telemetry.snapshot.get`
- `telemetry.replay.get`

Hoje essas ações estão espalhadas entre shell, ROS 2, MAVSDK e validators.

## 8. Recomendações de refatoração

### Frente 1: definir uma camada única de control plane

Objetivo:

- consolidar start/stop simulação, comando de missão, fault injection e execução de cenários em uma única superfície de produto

Sem implementar ainda, o melhor desenho de transição parece ser:

- uma API de controle separada da Telemetry API
- dono explícito do lifecycle do runtime
- adaptação das superfícies atuais (shell, ROS topics, MAVSDK) para ações de produto

### Frente 2: unificar o modelo operacional do sistema

Hoje faltam modelos de produto consistentes para:

- `SimulationSession`
- `Run`
- `Vehicle`
- `Mission`
- `Safety`
- `Perception`
- `Action`

O passo de refatoração aqui é **nomear e estabilizar** essas entidades antes de mexer em UI/MCP.

### Frente 3: separar “API de observabilidade” de “API de controle”

Hoje:

- Telemetry API = leitura e ingestão
- não há Control API

Recomendação:

- manter a Telemetry API como read model
- criar uma camada nova para command/control
- não misturar missão/safety com dashboard

### Frente 4: reduzir superfícies legadas e duplicadas

Pontos concretos a resolver em refatoração futura:

- escolher uma única implementação para a Telemetry API:
  - `services/telemetry-api/telemetry_api/`
  - ou `services/telemetry-api/src/telemetry_api/`
- decidir o papel real de `packages/shared-ts/`
- remover drift documental onde a doc não reflete mais a maturidade atual
  - por exemplo `simulation/README.md` ainda descreve a pasta como scaffold inicial e diz que nenhum processo deve ser iniciado dali

### Frente 5: transformar cenários em capabilities homogêneas

Hoje os cenários são heterogêneos:

- `takeoff_land` é CLI de produto
- `patrol_basic` é missão ROS 2
- safety/perception são validators

Refatoração recomendada:

- padronizar todos os cenários sob um mesmo conceito operacional
- separar claramente:
  - contrato de cenário
  - executor
  - action API
  - observabilidade/replay

### Frente 6: preparar a UI para virar interface humana principal

Hoje o dashboard é ótimo como painel de estado, mas não como central de comando.

A refatoração futura deve preparar:

- comandos de simulação
- comandos de missão
- fault injection
- inspeção de runs
- replay operacional

Sem mover regra de missão ou safety para o frontend.

### Frente 7: explicitar a estratégia de ambiente

Hoje o baseline oficial é claro, mas a experiência operacional ainda está espalhada entre:

- host local visual
- Docker validators
- devcontainer parcial

Refatoração recomendada:

- definir qual ambiente é o “produto local oficial”
- tratar Docker validators como prova de runtime
- tratar o modo visual local como experiência suportada explicitamente, não como side path

## Resumo curto

### O que já temos de muito forte

- separação arquitetural madura entre PX4, ROS 2, missão, safety, percepção, telemetria e dashboard
- contratos de domínio claros em `drone_msgs`
- validadores por fase e suíte consolidada em CI
- replay e observabilidade já auditáveis por `run_id`
- um stack simulation-first tecnicamente consistente

### Qual é o principal gap técnico hoje

O principal gap é a **ausência de um control plane unificado**. O projeto já tem as capacidades, mas elas estão distribuídas entre shell, MAVSDK, ROS 2 topics, validators e um dashboard read-only.

### Qual é o melhor próximo passo de refatoração

Antes de qualquer reescrita grande, o melhor próximo passo é definir e estabilizar um **modelo único de ação/capability de produto**, cobrindo:

- lifecycle da simulação
- ações de missão
- ações de veículo
- fault injection
- execução de cenários
- leitura consolidada de estado/run

Sem isso, qualquer tentativa de expor o sistema como interface humana centralizadora ou como MCP/tool para IA vai continuar acoplada demais às camadas técnicas atuais.
