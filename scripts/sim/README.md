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
- Scripts de start e stop reais ainda nao existem.
