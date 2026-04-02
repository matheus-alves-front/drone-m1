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

Smoke test estrutural do workspace ROS 2:

```bash
bash robotics/ros2_ws/scripts/validate-workspace.sh
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

## Estrutura

- `docs/` — documentação estratégica e técnica
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

## Observação

Este kit é **simulation-first**. Ele existe para levar o projeto do zero até um estado de simulação madura antes de qualquer compra de hardware.
