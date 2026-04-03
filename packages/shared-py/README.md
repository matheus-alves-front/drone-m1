# shared-py

Espaco reservado para bibliotecas Python compartilhadas entre scripts, servicos e pacotes do projeto.

## Regras

- manter utilitarios pequenos e orientados a dominio
- evitar acoplamento com detalhes internos do PX4
- nao mover logica de missao ou safety para helpers genericos sem justificativa

## Artefatos atuais

- `src/drone_scenarios/` contem a biblioteca reutilizavel da Fase 2 para runner MAVSDK.
- `pyproject.toml` descreve o pacote Python e suas dependencias opcionais.
- `tests/` contem os testes de contrato, CLI e runner com backend fake.

## Papel na Fase 2

- hospedar a logica Python do runner de cenarios
- manter wrappers shell finos em `scripts/scenarios/`
- evitar que a implementacao da Fase 2 vire um conjunto de scripts soltos
