# Safety Runtime Design

## When to use
Quando a tarefa envolver safety manager, faults, fallback ou geofence.

## Goal
Expor safety com soberania, visibilidade e acionamento controlado.

## Inputs required
rules.py, safety runtime atual, docs de safety

## Output expectations
fault actions, safety status normalization, docs e testes

## Rules
safety não depende da IA nem da UI

## Anti-patterns
bypass safety por conveniência

## Validation
fault injection e reação observáveis
