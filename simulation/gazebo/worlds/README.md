# Worlds

Diretorio reservado para mundos SDF da simulacao.

## Intencao

- Definir o ambiente fisico minimo da Fase 1 em Gazebo Harmonic.
- Servir como base para smoke tests e cenarios repetiveis.
- Manter cada world pequena, previsivel e documentada.

## World inicial

- `harmonic_minimal.sdf` representa o baseline inicial em Gazebo Harmonic.
- O world deve ser intencionalmente simples e sem dependencias ocultas.
- A cena base deve existir antes da integracao completa com PX4 SITL.

## Regras

- Um mundo por responsabilidade.
- Nome curto e descritivo.
- Evitar assets implícitos ou acoplamento com logica de missao.
