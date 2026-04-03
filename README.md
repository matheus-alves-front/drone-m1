# Drone Simulation-First Autonomy Kit

Pacote completo para iniciar um projeto **100% focado em simulação** de autonomia de drone com:

- PX4 SITL
- Gazebo
- ROS 2
- MAVSDK
- OpenCV
- Isaac ROS (opcional, fase posterior)

## Bootstrap do projeto

Antes de qualquer implementação de stack, use a checklist executável em `docs/PROJECT-EXECUTION-CHECKLIST.md`.

Validação mínima da Fase 0:

```bash
bash scripts/bootstrap/validate-phase-0.sh
```

Kickoff da Fase 1:

```bash
bash scripts/sim/validate-phase-1.sh
```

Validação real da Fase 1 em ambiente Jammy/Harmonic:

```bash
bash scripts/sim/build-phase-1-container-image.sh
bash scripts/sim/validate-phase-1-container.sh
```

Preflight isolado do Gazebo Harmonic CLI:

```bash
bash scripts/sim/check-gz-harmonic-cli.sh
```

Validação estrutural da Fase 2:

```bash
bash scripts/scenarios/validate-phase-2.sh
```

Validação E2E da Fase 2:

```bash
bash scripts/sim/build-phase-1-container-image.sh
bash scripts/scenarios/validate-phase-2-container.sh
```

Smoke test estrutural do workspace ROS 2:

```bash
bash robotics/ros2_ws/scripts/validate-workspace.sh
```

Validação real da Fase 3 em ambiente Humble/Jammy:

```bash
bash robotics/ros2_ws/scripts/validate-phase-3-container.sh
```

Validação estrutural da Fase 4:

```bash
bash robotics/ros2_ws/scripts/validate-phase-4.sh
```

Validação real da Fase 4 em ambiente Humble/Jammy:

```bash
bash robotics/ros2_ws/scripts/validate-phase-4-container.sh
```

Validação estrutural da Fase 5:

```bash
bash robotics/ros2_ws/scripts/validate-phase-5.sh
```

Validação real da Fase 5 em ambiente Humble/Jammy:

```bash
bash robotics/ros2_ws/scripts/validate-phase-5-container.sh
```

Teste automatizado do bootstrap:

```bash
python3 -m unittest scripts.tooling.tests.test_phase0_structure
```

## Baseline oficial do projeto

- PX4 como git submodule em `third_party/PX4-Autopilot/`
- PX4 pinado em `v1.16.1`
- `px4_msgs` alinhado com `release/1.16`
- ROS 2 Humble
- Ubuntu 22.04 no devcontainer
- Gazebo Harmonic
- Gazebo Classic fora de escopo
- Micro XRCE-DDS Agent `v2.4.3` standalone from source
- Runner MAVSDK preferencialmente em Python CLI com logica reutilizavel
- Runner MAVSDK implementado em `packages/shared-py/src/drone_scenarios/` com wrappers em `scripts/scenarios/`

## Estrutura

- `docs/` — documentação estratégica e técnica
  - `docs/README.md` organiza o que é essencial vs. consulta
  - `docs/decisions/` guarda decisões oficiais
  - `docs/contracts/` guarda contratos técnicos e specs de fase
  - `docs/runbooks/` guarda guias operacionais e troubleshooting
  - `docs/reference/` guarda material auxiliar de consulta
- `AGENTS.md` — instruções globais para o Codex no repositório
- `.agents/` — perfis de subagentes
- `.codex/skills/` — skills especializadas reutilizáveis
- `robotics/` — workspace ROS 2 e pacotes da autonomia
- `simulation/` — assets, contratos e cenários de simulação
- `scripts/` — utilitários de bootstrap e validação
- `scripts/sim/` — contratos, manifestos e validadores da simulação
- `services/` — serviços de backend e telemetria
- `apps/` — aplicações operacionais, incluindo dashboard
- `packages/` — bibliotecas compartilhadas Python e TypeScript
- `third_party/` — dependências vendoradas ou referenciadas
- `.github/` — automações de CI
- `.devcontainer/` — ambiente de desenvolvimento reproduzível

## Ordem recomendada

1. Ler `docs/PROJECT-SCOPE.md`
2. Ler `docs/SIMULATION-ARCHITECTURE.md`
3. Ler `docs/PROJECT-ARCHITECTURE.md`
4. Ler `docs/MONOREPO-STRUCTURE.md`
5. Ler `docs/AGENTS-AND-SKILLS.md`
6. Ler `docs/DEVELOPMENT-STANDARDS.md`
7. Ler `docs/TESTING-AND-FAILURE-MODEL.md`
8. Ler `docs/CHECKLIST-FRAMEWORK.md`
9. Ler `AGENTS.md`
10. Executar `bash scripts/bootstrap/validate-phase-0.sh`
11. Executar `bash scripts/sim/validate-phase-1.sh`
12. Executar `bash scripts/sim/build-phase-1-container-image.sh`
13. Executar `bash scripts/sim/check-gz-harmonic-cli.sh`
14. Executar `bash scripts/sim/validate-phase-1-container.sh`
15. Executar `bash scripts/scenarios/validate-phase-2-container.sh`
16. Executar `bash robotics/ros2_ws/scripts/validate-phase-3-container.sh`
17. Executar `bash robotics/ros2_ws/scripts/validate-phase-4-container.sh`
18. Executar `bash robotics/ros2_ws/scripts/validate-phase-5-container.sh`
19. Executar `bash robotics/ros2_ws/scripts/validate-phase-6-container.sh`
20. Executar `bash robotics/ros2_ws/scripts/validate-phase-7.sh`
21. Executar `bash scripts/ci/validate-phase-8.sh`

## Observação

Este kit é **simulation-first**. Ele existe para levar o projeto do zero até um estado de simulação madura antes de qualquer compra de hardware.

## Status atual

- As Fases 0, 1, 2, 3, 4, 5, 6, 7 e 8 estao concluidas e validadas.
- A Fase 3 fecha a fronteira ROS 2 com `drone_msgs`, `drone_px4`, `drone_bringup`, `px4_msgs` oficial e validacao real em Humble/Jammy.
- O bridge da Fase 3 consome topicos reais de PX4 via uXRCE-DDS e publica `VehicleState` e `VehicleCommandStatus` no dominio.
- A Fase 4 fecha a orquestracao real de `patrol_basic` pelo dominio ROS 2 com `mission_manager_node`, `MissionStatus`, ACK real de arm e gate canonico `VehicleState.armed=true` antes de `takeoff`.
- A Fase 5 fecha `drone_safety` com `SafetyStatus`, fault injection, geofence, GPS loss e RC loss validados em runtime real.
- A Fase 6 fecha `drone_perception` com camera simulada, detector, tracker, gate real de visual lock e degradacao oficial por `perception_timeout`.
- A Fase 7 fecha operacao e observabilidade com `drone_telemetry`, Telemetry API, replay auditavel e dashboard React.
- A Fase 8 fecha a maturidade da simulacao com suite final, CI em camadas, troubleshooting e criterios explicitos para futura migracao a hardware.
- O projeto permanece explicitamente simulation-first; qualquer migracao a hardware continua fora do escopo atual e depende de `docs/decisions/HARDWARE-MIGRATION-CRITERIA.md`.
