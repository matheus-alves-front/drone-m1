# Simulation Scripts

Ponto de entrada reservado para a subida e a parada do stack de simulacao.

## Contrato da Fase 0

- Nenhum script operacional de PX4 ou Gazebo existe aqui ainda.
- As fases seguintes devem introduzir `start.sh` e `stop.sh` sem misturar logica de missao.
- Toda automacao daqui deve tratar o simulador como ambiente externo orquestrado pelo monorepo.

## Artefatos atuais da Fase 1

- `phase-1-manifest.md` consolida o baseline oficial da fase.
- `validate-phase-1.sh` valida o scaffold minimo da fase.
- `vendor-px4-submodule.sh` prepara a vendorizaçao oficial do PX4 como git submodule.
- `docs/runbooks/PHASE-1-STARTUP-ORDER.md` registra a ordem oficial de subida do stack minimo.
- `docs/runbooks/PX4-SITL-HEADLESS-RUNBOOK.md` registra o comando minimo headless e os pre-requisitos.
- `start.sh` sobe o stack minimo em headless mode e rastreia PIDs/logs.
- `stop.sh` encerra o stack minimo e limpa o estado de runtime.
- `validate-phase-1-container.sh` executa a validacao real da Fase 1 em container Jammy com Gazebo Harmonic e PX4 SITL.
