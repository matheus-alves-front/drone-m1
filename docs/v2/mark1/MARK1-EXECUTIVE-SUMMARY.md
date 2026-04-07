# Mark 1 Executive Summary

O projeto atual já provou que o stack simulation-first funciona em camadas.  
O problema não é falta de base técnica. O problema é falta de uma superfície unificada de produto.

## O Mark 1 resolve isso

### Antes
- shell scripts
- MAVSDK runner
- tópicos ROS 2
- validators por fase
- dashboard read-only

### Depois
- control plane explícito
- actions formais
- operator UI
- read model separado
- cenários homogêneos
- lifecycle claro de simulação e run
- base pronta para IA/MCP no futuro

## Resultado esperado
Ao final do Mark 1, um operador deve conseguir:
- subir/parar a simulação
- executar cenários
- iniciar/abortar missão
- injetar faults
- ver telemetria
- ver replay
- operar a percepção/câmera
- usar tudo isso sem depender de múltiplos terminais técnicos
