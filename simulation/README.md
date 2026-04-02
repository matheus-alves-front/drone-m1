# Simulation

Diretorio raiz para o ambiente de simulacao do projeto simulation-first.

## Status atual

Esta pasta contem o scaffold inicial da Fase 0 e o baseline minimo da Fase 1. Nenhum processo de PX4, Gazebo ou ROS 2 deve ser iniciado a partir daqui ainda.

## Baseline oficial

- Gazebo Harmonic
- ROS 2 Humble
- Ubuntu 22.04 como referencia de devcontainer
- Gazebo Classic fora de escopo

## Estrutura

- `gazebo/` - contratos, mundos, modelos e recursos da simulacao
- `scenarios/` - cenarios executaveis, manifests e smoke tests futuros

## Regras locais

- Manter mundos e modelos reproduziveis.
- Nao misturar logica de missao ou safety com assets de simulacao.
- Guardar cada cenário com nome explicito e criterio de aceite claro.
- Preferir arquivos pequenos e bem documentados a placeholders opacos.
