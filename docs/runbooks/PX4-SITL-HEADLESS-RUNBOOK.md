# PX4-SITL-HEADLESS-RUNBOOK.md

## Objetivo

Registrar o comando minimo e os pre-requisitos para subir PX4 SITL com Gazebo Harmonic em modo headless a partir do submodule `v1.16.1`.

## Comando minimo

Executar dentro de `third_party/PX4-Autopilot/`:

```bash
HEADLESS=1 make px4_sitl gz_x500
```

Entrada operacional recomendada pelo monorepo:

```bash
bash scripts/sim/start.sh
```

O `start.sh` injeta uma `GZ_PARTITION` estavel por padrao para evitar falhas de discovery entre processos `gz` em runtime containerizado.

Para abrir o Gazebo com GUI no ambiente local:

```bash
PHASE1_HEADLESS=0 bash scripts/sim/start.sh
```

Parada recomendada:

```bash
bash scripts/sim/stop.sh
```

Validacao real recomendada da Fase 1:

```bash
bash scripts/sim/build-phase-1-container-image.sh
bash scripts/sim/validate-phase-1-container.sh
```

Preflight isolado do Gazebo Harmonic CLI:

```bash
bash scripts/sim/check-gz-harmonic-cli.sh
```

## Pre-requisitos

- Repositorio principal em um Git worktree valido.
- Submodule `third_party/PX4-Autopilot/` inicializado e pinado em `v1.16.1`.
- `Gazebo Harmonic` instalado no ambiente de referencia.
- `Ubuntu 22.04` como baseline operacional do devcontainer.
- `PX4-Autopilot` na linha `v1.16.1`, com `px4_msgs` alinhado com `release/1.16`.
- Ferramentas de build disponiveis: `git`, `cmake`, `make`, `ninja` e `python3`.
- Paths do ambiente de simulacao preparados antes de iniciar a execucao.

## O que este comando faz

- Sobe PX4 SITL.
- Inicia a simulacao `gz_x500` do PX4.
- Evita a interface grafica do Gazebo com `HEADLESS=1`.

## Observacoes operacionais

- O comando acima e o ponto minimo oficial de partida para a Fase 1.
- O validador em container usa uma imagem limpa do projeto, baseada em `px4io/px4-dev-base-jammy:latest`, para evitar misturar Gazebo Garden com Gazebo Harmonic no runtime oficial.
- A validacao containerizada precisa manter `gz sim`, `gz topic` e `gz service` na mesma `GZ_PARTITION`; o monorepo agora faz isso de forma explicita nos validadores.
- Em ambiente sem `cmake`, a invocacao falha antes do build de PX4 iniciar.
- Se o alvo de build nao existir, o ambiente pode ainda precisar de uma limpeza de build antes de tentar novamente.
- Se o preflight `bash scripts/sim/check-gz-harmonic-cli.sh` falhar, o runtime `gz` do ambiente atual nao esta saudavel o suficiente para validar PX4 SITL.
- Este runbook nao substitui a orquestração completa da Fase 2 em diante.

## Referencia

- PX4 Gazebo Harmonic headless mode: `HEADLESS=1 make px4_sitl gz_x500`
