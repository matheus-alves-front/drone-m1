# Perception Operations

## When to use
Quando a tarefa envolver camera pipeline, detections, tracked objects ou heartbeat.

## Goal
Tornar percepção parte operável e observável do produto.

## Inputs required
nodes de percepção, pipeline atual, docs de UI e read model

## Output expectations
surface operacional de percepção, painéis e contratos

## Rules
UI observa/controla por API/read model, não por acoplamento direto

## Anti-patterns
perception state duplicado no frontend

## Validation
heartbeat, tracked object e stream/proxy visíveis
