# PHASE-1-BLOCKER-GAZEBO-HARMONIC-CONTAINER.md

## Objetivo

Registrar o bloqueio real que existiu durante a validacao de `PX4 SITL + Gazebo Harmonic` em container, a causa raiz encontrada e a forma como ele foi resolvido.

## Estado atual

- Resolvido em 2 de abril de 2026 para a Fase 1.
- Mantido como registro historico porque explica a correcao aplicada no baseline de validacao.

## Data do diagnostico

- Diagnostico confirmado em 2 de abril de 2026.

## Sintoma observado originalmente

- O build `HEADLESS=1 make px4_sitl gz_x500` compila ate o final.
- O `bin/px4` inicia o `rcS`, mas o runtime nao chega em `INFO  [px4] Startup script returned successfully`.
- Em ambiente de validacao containerizado, comandos basicos do Gazebo Harmonic CLI tambem podem morrer com `Killed`, inclusive:
  - `gz sim --versions`
  - `gz sim -r -s /usr/share/gz/gz-sim8/worlds/default.sdf`
  - `gz service -i --service /world/default/scene/info`

## Diagnostico consolidado

- O bloqueio atual nao esta no runner MAVSDK da Fase 2.
- O bloqueio atual esta no runtime do Gazebo Harmonic dentro do ambiente Docker usado pela validacao.
- O default antigo de validacao, `px4io/px4-dev-simulation-jammy:latest`, tambem era inadequado para o baseline oficial porque ja vinha com Gazebo Garden preinstalado.
- O projeto continua com baseline oficial em:
  - Ubuntu 22.04
  - ROS 2 Humble
  - Gazebo Harmonic
- O problema foi reproduzido de forma suficiente para justificar falha antecipada de preflight nos validadores em container.
- Depois da troca da imagem-base, ainda existia uma falha silenciosa de discovery entre processos `gz`: o servidor subia, mas `gz topic -l` e `gz service -i` nao encontravam a world de forma reproduzivel.
- A causa operacional final foi a ausencia de uma `GZ_PARTITION` explicita e estavel no runtime containerizado do stack PX4 + Gazebo.

## Impacto por fase na epoca do bloqueio

- Fase 1: bloqueada na validacao real do stack minimo em container.
- Fase 2: bloqueada para validacao E2E real, porque dependia da subida real da Fase 1.
- Fases 3 em diante: nao deveriam ser iniciadas formalmente enquanto a base operacional continuasse bloqueada.

## Correcao aplicada no repositório

- `scripts/sim/build-phase-1-container-image.sh` e `docker/phase1-validation/Dockerfile` agora definem uma imagem oficial limpa de validacao, baseada em `px4io/px4-dev-base-jammy:latest` e com Gazebo Harmonic instalado sem depender da imagem de simulacao antiga do PX4.
- `scripts/sim/validate-phase-1-container.sh` agora usa essa imagem limpa e executa um preflight de Gazebo antes de iniciar PX4.
- `scripts/scenarios/validate-phase-2-container.sh` agora faz o mesmo preflight antes de tentar o cenário MAVSDK.
- `scripts/sim/check-gz-harmonic-cli.sh` agora falha cedo se detectar `gz-garden` no ambiente oficial de validacao.
- `scripts/sim/start.sh` agora define uma `GZ_PARTITION` estavel por padrao para o stack minimo.
- `scripts/sim/check-gz-harmonic-cli.sh` agora executa o preflight com `GZ_PARTITION` explicita.
- `scripts/sim/validate-phase-1-container.sh` e `scripts/scenarios/validate-phase-2-container.sh` agora usam particoes distintas e explicitas para preflight e runtime.
- O repositorio agora falha cedo com diagnostico claro, em vez de deixar a validacao parecer instavel ou parcialmente concluida.

## Evidencia de resolucao

O bloqueio foi considerado resolvido quando os comandos abaixo passaram no ambiente oficial de validacao:

```bash
gz sim --versions
gz sim -r -s /usr/share/gz/gz-sim8/worlds/default.sdf
gz service -i --service /world/default/scene/info
bash scripts/sim/validate-phase-1-container.sh
```

Resultado atual:

- `bash scripts/sim/validate-phase-1-container.sh` passa no ambiente oficial Jammy + Harmonic.
- A Fase 2 continua com bloqueio proprio no cenário MAVSDK E2E, mas nao mais por falha estrutural de PX4 + Gazebo.

## Observacao

- Este documento nao altera o baseline oficial do projeto.
- Gazebo Classic continua fora de escopo.
- O objetivo aqui e tornar o historico do bloqueio explicito e verificavel, nao mascarar a falha nem apagar a causa raiz.
