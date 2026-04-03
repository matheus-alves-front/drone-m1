# PHASE-1-STARTUP-ORDER.md

## Objetivo

Registrar a ordem oficial de subida do stack minimo de simulacao da Fase 1, sem fingir que a orquestracao completa ja esta pronta.

## Ordem oficial

1. Preparar o ambiente do simulador e os paths do Gazebo Harmonic.
2. Subir o `Micro XRCE-DDS Agent v2.4.3` como processo externo.
3. Subir o `PX4 SITL` junto do mundo base em Gazebo Harmonic.
4. Verificar que o veiculo e o mundo foram carregados.
5. Deixar a entrada para ROS 2 bringup preparada para a Fase 3.
6. Deixar a entrada para runner MAVSDK preparada para a Fase 2.

## Entradas operacionais

- `scripts/sim/build-phase-1-container-image.sh` constroi a imagem oficial de validacao Jammy + Harmonic sem baseline Garden preinstalado.
- `scripts/sim/start.sh` executa a ordem acima, registra logs e rastreia PIDs.
- `scripts/sim/stop.sh` encerra a sessão e limpa o estado de runtime.
- `scripts/sim/start.sh --check` valida o contrato sem iniciar processos.
- `scripts/sim/stop.sh --check` valida o contrato de parada sem encerrar nada.

## Comando minimo oficial

Dentro de `third_party/PX4-Autopilot/`:

```bash
HEADLESS=1 make px4_sitl gz_x500
```

## Pre-requisitos oficiais

- Git worktree valido no repositório principal.
- Submodule `third_party/PX4-Autopilot/` inicializado e pinado em `v1.16.1`.
- `Gazebo Harmonic` instalado no baseline de referencia.
- `Ubuntu 22.04` como ambiente operacional de referencia.
- `px4_msgs` alinhado com a linha `release/1.16`.
- Ferramentas de build disponiveis: `git`, `cmake`, `make`, `ninja` e `python3`.

## Escopo desta fase

- A Fase 1 consolida baseline, vendorizaçao do PX4, world minimo e contratos.
- A Fase 1 ainda nao depende de bringup ROS 2 funcional.
- A Fase 1 ainda nao depende de runner MAVSDK funcional.

## Bloqueios atuais

- O workspace ROS 2 ainda nao esta alinhado com `px4_msgs` da linha `release/1.16`.
- A imagem default antiga baseada em `px4io/px4-dev-simulation-jammy:latest` nao deve mais ser usada para a validacao oficial, porque misturava baseline Garden com o baseline Harmonic do projeto.
- A subida ponta a ponta de `PX4 SITL + Gazebo Harmonic` ainda depende de confirmar a saude do runtime `gz` na nova imagem limpa de validacao.
- O bloqueio operacional atual esta registrado em `docs/runbooks/PHASE-1-BLOCKER-GAZEBO-HARMONIC-CONTAINER.md`.
