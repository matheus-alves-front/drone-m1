# Mission Runtime Refactor

## When to use
Quando a tarefa envolver mission manager, mission commands ou mission status.

## Goal
Expor missão via produto sem destruir o runtime ROS 2.

## Inputs required
mission runtime atual, control plane docs, domain model

## Output expectations
adapters, status normalization, mission actions

## Rules
frontend não carrega state machine

## Anti-patterns
mission logic dentro da UI

## Validation
mission start/abort via control plane
