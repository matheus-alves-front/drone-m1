# Operator UI Control Surface

## When to use
Quando a tarefa envolver dashboard, console operacional, painéis de ação ou UX de operação.

## Goal
Transformar o frontend em console humano forte sem mover lógica central para ele.

## Inputs required
docs de UI, control plane endpoints, read model

## Output expectations
layout, painéis, clientes, fluxos de ação, feedback

## Rules
UI chama APIs; não chama ROS 2/MAVSDK/PX4 direto

## Anti-patterns
bypass do control plane

## Validation
tests/build/smoke de ações críticas
