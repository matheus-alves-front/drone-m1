# Gazebo

Espaco para os artefatos de Gazebo usados pelo projeto.

## Baseline oficial

- Gazebo Harmonic
- Nao usar Gazebo Classic
- Manter compatibilidade com Ubuntu 22.04 e ROS 2 Humble

## Conteudo esperado

- `worlds/` - mundos SDF e variações de ambiente
- `models/` - modelos reutilizaveis do veiculo, obstaculos e referencias
- `resources/` - meshes, texturas e materiais

## Baseline oficial da Fase 1

- Gazebo Harmonic e a variante suportada no projeto.
- Gazebo Classic nao deve ser introduzido.
- O primeiro world deve ser pequeno, reproduzivel e focado em smoke test.
- O primeiro modelo deve servir como placeholder do veiculo base, nao como tuning real.

## Contrato

- Os mundos devem ser reprodutiveis.
- Os modelos devem ser reaproveitaveis.
- Os recursos devem ser versionados de forma previsivel.
- Nenhum fluxo de execução deve assumir que estes arquivos ja estao prontos para voo autonomo real.
