# SIMULATION-OPERATIONS-TROUBLESHOOTING.md

## Objetivo

Concentrar a trilha operacional e os principais procedimentos de troubleshooting para reproduzir a simulacao madura do projeto.

## Ordem operacional recomendada

1. `bash scripts/bootstrap/validate-phase-0.sh`
2. `bash scripts/sim/validate-phase-1.sh`
3. `bash scripts/scenarios/validate-phase-2.sh`
4. `bash robotics/ros2_ws/scripts/validate-workspace.sh`
5. `bash robotics/ros2_ws/scripts/validate-phase-4.sh`
6. `bash robotics/ros2_ws/scripts/validate-phase-5.sh`
7. `bash robotics/ros2_ws/scripts/validate-phase-6.sh`
8. `bash robotics/ros2_ws/scripts/validate-phase-7.sh`
9. `bash scripts/ci/validate-phase-8.sh --check`
10. `bash scripts/ci/validate-phase-8.sh`

## Onde olhar logs e artefatos

- bootstrap:
  - validacao local em stdout
- stack minimo:
  - `.sim-logs/phase-1-container/`
- MAVSDK:
  - `.sim-logs/phase-2-container/`
- missao:
  - `.sim-logs/phase-4-container/`
- safety:
  - `.sim-logs/phase-5-container/<cenario>/`
- percepcao:
  - `.sim-logs/phase-6-container/<caso>/`
- observabilidade:
  - `services/telemetry-api/data/`

## Problemas comuns

### PX4 submodule ausente

- Sintoma:
  - `third_party/PX4-Autopilot/` vazio ou sem `git submodule status`
- Acao:
  - garantir checkout com submodules recursivos
  - rodar `git submodule update --init --recursive`

### Gazebo Harmonic nao responde a `gz topic` ou `gz service`

- Sintoma:
  - `gz sim` sobe, mas `gz topic -l` nao enxerga a world
- Causa provavel:
  - `GZ_PARTITION` diferente entre processos
- Acao:
  - usar sempre os validadores oficiais
  - se for reproduzir manualmente, exportar a mesma `GZ_PARTITION` para `gz sim`, `gz topic` e `gz service`

### Micro XRCE-DDS Agent nao encontrado

- Sintoma:
  - falha ao iniciar `start.sh` ou validadores containerizados
- Acao:
  - executar primeiro `bash scripts/sim/validate-phase-1-container.sh`
  - confirmar cache em `.cache/phase-1/micro-xrce-agent/`
  - se o `PATH` local nao tiver `MicroXRCEAgent`, o `scripts/sim/start.sh` agora tenta reutilizar automaticamente:
    - `.cache/phase-1/micro-xrce-agent/install/bin/MicroXRCEAgent`
    - `.cache/phase-1/micro-xrce-agent/build/MicroXRCEAgent`
  - para forcar manualmente:
    - `MICRO_XRCE_AGENT_BIN="$PWD/.cache/phase-1/micro-xrce-agent/build/MicroXRCEAgent" bash scripts/sim/start.sh`

### PX4 SITL para no configure com `kconfiglib` ou `menuconfig`

- Sintoma:
  - `ModuleNotFoundError: No module named 'menuconfig'`
  - `kconfiglib is not installed or not in PATH`
- Acao:
  - criar uma virtualenv local no repositorio:
    - `python3 -m venv .venv`
    - `. .venv/bin/activate`
    - `python -m pip install --upgrade pip`
    - `python -m pip install -r third_party/PX4-Autopilot/Tools/setup/requirements.txt`
  - confirmar:
    - `.venv/bin/python -c "import kconfiglib; print('ok')"`
  - o `scripts/sim/start.sh` tenta usar `.venv/bin/python` automaticamente quando ela existe

### PX4 SITL para no build com `em.RAW_OPT`, `jinja2` ou `jsonschema`

- Sintoma:
  - `AttributeError: module 'em' has no attribute 'RAW_OPT'`
  - `No module named 'jinja2'`
  - `No module named 'jsonschema'`
- Causa provavel:
  - a `.venv` tem `empy 4.x` ou esta fora do conjunto esperado pelo `Tools/setup/requirements.txt` do PX4
- Acao:
  - com a `.venv` ativada:
    - `python -m pip install --upgrade pip`
    - `python -m pip install -r third_party/PX4-Autopilot/Tools/setup/requirements.txt`
  - confirmar:
    - `.venv/bin/python - <<'PY'\nimport em, jinja2, jsonschema\nprint(hasattr(em, 'RAW_OPT'))\nPY`

### PX4 SITL para no configure com `OpenCVConfig.cmake`

- Sintoma:
  - `Could not find a package configuration file provided by "OpenCV"`
  - `OpenCVConfig.cmake` ou `opencv-config.cmake` ausente
- Acao:
  - instalar os headers e arquivos de CMake do OpenCV:
    - `sudo apt-get install -y libopencv-dev`
  - confirmar:
    - `pkg-config --modversion opencv4`
  - repetir:
    - `bash scripts/sim/stop.sh`
    - `PHASE1_HEADLESS=0 bash scripts/sim/start.sh`

### Gazebo sobe sem camera GStreamer ou mostra erro `libGstCameraSystem.so`

- Sintoma:
  - `Failed to load system plugin [libGstCameraSystem.so]`
  - camera simulada nao funciona ou recursos visuais ligados a camera falham
- Causa provavel:
  - o plugin custom do PX4 nao foi compilado porque faltam headers de desenvolvimento do GStreamer
- Acao:
  - instalar:
    - `sudo apt-get install -y libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev`
  - confirmar:
    - `pkg-config --modversion gstreamer-1.0`
    - `pkg-config --modversion gstreamer-app-1.0`
  - limpar e subir de novo:
    - `bash scripts/sim/stop.sh`
    - `rm -rf third_party/PX4-Autopilot/build/px4_sitl_default`
    - `PHASE1_HEADLESS=0 bash scripts/sim/start.sh`

### `patrol_basic` aborta antes da missao

- Sintoma:
  - `MissionStatus` nao sai de bootstrap ou o safety entra cedo demais
- Acao:
  - confirmar `VehicleCommandStatus` aceito e depois `VehicleState.armed=true`
  - confirmar parametros PX4 aplicados por `scripts/sim/configure_px4_sim_params.py`
  - inspecionar `bringup.log`, `arm_ack.json` e `mission_status.json` na pasta da fase

### `perception_timeout` ou `visual_lock_gate` falha

- Sintoma:
  - missao nao avanca para `patrol` ou safety nao reage
- Acao:
  - confirmar feed em `/simulation/camera/image_raw`
  - confirmar `/drone/perception/tracked_object`
  - confirmar `/drone/perception_heartbeat`
  - conferir os artefatos em `.sim-logs/phase-6-container/<caso>/`

### Dashboard passa em teste mas falha em build

- Sintoma:
  - `npm test` passa e `npm run build` quebra
- Acao:
  - usar o contrato local de tipos em `apps/dashboard/src/types.ts`
  - evitar aliases antigos ou contratos legados fora da Telemetry API
  - rodar `bash robotics/ros2_ws/scripts/validate-phase-7.sh`

### Telemetry API indisponivel

- Sintoma:
  - `telemetry_bridge_node` acumula erro de transporte
- Acao:
  - verificar `services/telemetry-api/data/`
  - verificar `GET /api/v1/health`
  - revisar os testes de `drone_telemetry/test/test_transport.py`

## Regra de troubleshooting

- Sempre usar primeiro o validador oficial da fase antes de depurar manualmente.
- Sempre preservar o isolamento por caso dos validadores containerizados.
- Nunca reinterpretar falha de simulacao como prontidao para hardware real.
