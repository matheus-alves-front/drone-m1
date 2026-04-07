# Runtime Orchestration

## When to use
Quando a tarefa envolver start/stop/status da simulação, sessions ou preflight.

## Goal
Transformar o lifecycle da simulação em ação formal de produto.

## Inputs required
scripts atuais de simulação, environment strategy, control plane docs

## Output expectations
orchestrator, session state, docs de ambiente

## Rules
session lifecycle deve ser visível no control plane

## Anti-patterns
estado escondido apenas em shell ou logs

## Validation
smoke visual/headless, testes de session
