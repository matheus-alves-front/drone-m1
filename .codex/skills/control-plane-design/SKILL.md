# Control Plane Design

## When to use
Quando a tarefa envolver ações unificadas, sessions, runs, orchestration ou a nova Control API.

## Goal
Transformar superfícies fragmentadas em uma camada única de comando.

## Inputs required
auditoria atual, docs do Mark 1, modelo de domínio, contracts de action

## Output expectations
API shape, handlers, orchestration, docs e testes

## Rules
separar command side de read side; não expor ROS 2/MAVSDK cru ao produto

## Anti-patterns
usar shell scripts ou topics crus como “API final”

## Validation
testes HTTP, smoke do control plane, revisão de action coverage
