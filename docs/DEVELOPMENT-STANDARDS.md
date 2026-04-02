# DEVELOPMENT-STANDARDS.md

## Objetivo

Padronizar o desenvolvimento para reduzir ambiguidade entre múltiplos agentes e facilitar manutenção.

## Padrões gerais

- nomes claros
- responsabilidade única por módulo
- logs estruturados
- configs externalizadas
- tipagem sempre que possível
- testes obrigatórios para lógica relevante
- documentação junto da mudança

## Python
- type hints
- módulos pequenos
- pytest
- logging com contexto

## TypeScript
- eslint
- tipagem estrita
- componentes pequenos
- estado previsível

## ROS 2
- node por responsabilidade
- launch files organizados
- params externalizados
- QoS documentado
- mensagens internas do domínio em `drone_msgs`
