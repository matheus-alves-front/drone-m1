# PHASE-0-OPEN-DECISIONS.md

## Objetivo

Registrar o fechamento das decisoes abertas da Fase 0 que destravam a Fase 1, sem inventar arquitetura fora do que ja esta documentado.

## Status

- Itens 1 a 5: fechados oficialmente.
- Item 6: permanece em aberto para a Fase 7.

## Decisoes fechadas

### 1. PX4 como submodule

- Status: fechada.
- Decisao oficial: vendorizar `PX4-Autopilot` como git submodule em `third_party/PX4-Autopilot/`.
- Pin oficial: `v1.16.1`.
- Regra de compatibilidade: alinhar `px4_msgs` com a linha `release/1.16`.
- Consequencia operacional: a vendorizaçao real deve acontecer por fluxo de submodule e falhar claramente se o repositório local nao estiver em um estado Git compativel.

### 2. ROS 2 baseline

- Status: fechada.
- Decisao oficial: adotar ROS 2 Humble como baseline do projeto.
- Ambiente oficial de referencia: Ubuntu 22.04 no devcontainer.
- Consequencia operacional: scripts, docs e exemplos da linha principal devem assumir Humble como baseline.

### 3. Gazebo baseline

- Status: fechada.
- Decisao oficial: adotar Gazebo Harmonic.
- Restricao explicita: Gazebo Classic nao sera usado.
- Consequencia operacional: worlds, recursos e comandos da simulação devem referenciar somente o baseline Harmonic.

### 4. Micro XRCE-DDS Agent

- Status: fechada.
- Decisao oficial: instalar standalone from source.
- Pin oficial: `v2.4.3`.
- Modo de execucao inicial: processo externo ao workspace ROS 2 a partir da Fase 1.
- Consequencia operacional: a orquestração deve tratar o agent como dependencia externa do stack, nao como pacote interno do workspace.

### 5. Runner MAVSDK

- Status: fechada.
- Decisao oficial: nao fechar a implementacao final agora.
- Direcao preferida para a Fase 2: Python CLI com logica reutilizavel separada de scripts soltos.
- Consequencia operacional: a Fase 2 deve privilegiar uma biblioteca Python reaproveitavel com entrada CLI.

## Decisao ainda em aberto

### 6. Contrato inicial de persistencia para telemetria e replay

- Status: aberta.
- Estado atual: a arquitetura aponta para backend leve e arquivos estruturados ou banco leve, mas sem escolha final.
- Impacto: afeta o desenho de `services/telemetry-api/` e `packages/shared-*`.
- Fase alvo: Fase 7.
