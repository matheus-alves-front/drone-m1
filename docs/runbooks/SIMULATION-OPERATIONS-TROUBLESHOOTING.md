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
