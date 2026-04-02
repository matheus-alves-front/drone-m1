# PROJECT-SCOPE.md

## Visão geral

Este projeto tem como objetivo construir um stack completo de autonomia de drone **100% focado em simulação**, do zero até um estado de maturidade suficiente para:

- voar em simulação
- executar missões
- lidar com falhas simuladas
- processar percepção visual
- publicar telemetria
- manter observabilidade e replay
- servir como base para futura migração para hardware

A meta **não** é pilotar um drone real neste estágio.  
A meta é construir um software stack robusto, modular, reproduzível e testável.

## Objetivo principal

Criar um projeto monorepo simulation-first que permita:

- subir PX4 SITL + Gazebo
- conectar ROS 2
- controlar missões via MAVSDK
- integrar percepção com câmera simulada
- implementar regras de missão e segurança
- rodar cenários automatizados de teste
- usar IA e code agents para acelerar quase todo o desenvolvimento

## Objetivos funcionais

### Missão
- armar o drone
- decolar
- pairar
- navegar por waypoints
- executar rota de patrulha
- retornar à origem
- pousar
- abortar missão com fallback seguro

### Segurança
- aplicar geofence
- reagir a perda de link
- reagir a falha de missão
- reagir a eventos de failsafe
- reagir a falhas injetadas em simulação

### Percepção
- consumir feed de câmera simulada
- pré-processar frames
- rodar detecção
- rodar tracking
- gerar eventos visuais
- integrar eventos com a lógica de missão

### Operação
- expor telemetria
- registrar logs
- salvar métricas
- permitir replay
- exibir estado operacional num dashboard

## Objetivos não funcionais

- reprodutibilidade
- modularidade
- observabilidade
- versionamento claro
- forte compatibilidade com code agents
- arquitetura desacoplada
- documentação completa
- facilidade de teste em CI

## Fora de escopo neste estágio

- voo real
- compra de hardware
- tuning físico
- HIL
- operação em área urbana real
- BVLOS real
- payload físico real
- LLM em loop crítico de controle de voo

## Restrições

- o projeto deve ser guiado por simulação primeiro
- a arquitetura deve assumir que o PX4 continua sendo o autopilot
- a autonomia deve ser construída fora do PX4, principalmente em ROS 2 + MAVSDK
- a visão computacional deve começar simples
- o sistema deve ser projetado para ser desenvolvido em fases

## Critérios de sucesso

O projeto será considerado bem-sucedido quando conseguir:

1. subir o stack completo de simulação
2. rodar ao menos uma missão de patrulha completa
3. reagir a ao menos 3 falhas simuladas
4. registrar logs e métricas reproduzíveis
5. ter documentação suficiente para permitir execução por code agents
6. permitir evolução incremental para hardware no futuro
