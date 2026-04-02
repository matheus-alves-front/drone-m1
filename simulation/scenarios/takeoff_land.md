# takeoff_land

## Objetivo

Smoke test inicial da Fase 1 para validar a definicao do fluxo de simulacao antes do runner MAVSDK existir.

## Pre-requisitos

- `simulation/gazebo/worlds/harmonic_minimal.sdf` presente
- `simulation/gazebo/models/drone_base/` presente
- Baseline oficial definido para Gazebo Harmonic e ROS 2 Humble

## Sequencia esperada

1. Carregar o world minimalista.
2. Inserir o modelo base do veiculo.
3. Confirmar que o ambiente da simulacao esta descrito de forma reproduzivel.

## Sinais observaveis

- O world existe e pode ser referenciado por ferramentas futuras.
- O modelo base existe como contrato de cena.
- O cenário serve como ponte para a Fase 2.

## Criterio de sucesso

- A documentacao do cenário permite repetir a configuracao sem ambiguidade.

## Criterio de falha

- O world ou o modelo base nao existem.
- A documentacao nao deixa claro o baseline oficial da simulacao.
