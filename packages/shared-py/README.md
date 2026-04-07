# shared-py

Espaco reservado para bibliotecas Python compartilhadas entre scripts, servicos e pacotes do projeto.

## Regras

- manter utilitarios pequenos e orientados a dominio
- evitar acoplamento com detalhes internos do PX4
- nao mover logica de missao ou safety para helpers genericos sem justificativa

## Artefatos atuais

- `src/drone_scenarios/` contem a biblioteca reutilizavel da Fase 2 para runner MAVSDK.
- `src/control_plane/` contem os contratos compartilhados de dominio, actions e capabilities do Mark 1.
- `pyproject.toml` descreve o pacote Python e suas dependencias opcionais.
- `tests/` contem os testes de contrato, CLI e runner com backend fake.
  Agora tambem validam serializacao basica do control plane.

## Papel na Fase 2

- hospedar a logica Python do runner de cenarios
- manter wrappers shell finos em `scripts/scenarios/`
- evitar que a implementacao da Fase 2 vire um conjunto de scripts soltos

## Papel no Mark 1

- estabilizar o vocabulario de `SimulationSession`, `Run`, `Action` e `Capability`
- permitir que `services/control-api/` nasca sobre contratos compartilhados
- preparar metadata de capability sem antecipar o registry completo do Mark 2
- manter DTOs nominais de input/output para actions do control plane
- tornar gating de action explicito por escopo de dominio com `availability`
