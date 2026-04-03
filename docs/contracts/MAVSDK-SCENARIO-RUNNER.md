# MAVSDK-SCENARIO-RUNNER.md

## Objetivo

Registrar o contrato operacional da Fase 2 para execucao de cenarios MAVSDK sem antecipar a bridge ROS 2 da Fase 3.

## Decisao de implementacao

- Entrada principal: CLI Python.
- Logica reutilizavel: biblioteca em `packages/shared-py/src/drone_scenarios/`.
- Wrappers de shell: somente em `scripts/scenarios/`.
- Manifestos executaveis: `simulation/scenarios/*.json`.

## Fronteiras da Fase 2

- O runner fala diretamente com PX4 via MAVSDK.
- O runner ainda nao depende de nodes ROS 2 reais.
- O runner nao implementa mission manager, safety manager ou telemetry bridge.
- O runner serve para smoke scenarios E2E e harness de automacao.
- A validacao E2E real do smoke scenario oficial passa contra `PX4 SITL + Gazebo Harmonic` no ambiente oficial de container da Fase 2.

## Manifesto de cenario

Cada manifesto JSON da Fase 2 precisa declarar:

- `name`
- `objective`
- `connection`
- `flight`

## Contrato de conexao

Campos obrigatorios em `connection`:

- `system_address`
- `connection_timeout_s`
- `ready_timeout_s`
- `action_timeout_s`

Baseline inicial do projeto:

- endereco MAVSDK padrao para PX4 SITL: `udp://:14540`

## Parametros de voo

Campos obrigatorios em `flight`:

- `takeoff_altitude_m`
- `hover_duration_s`
- `waypoint_offset_north_m`
- `waypoint_offset_east_m`
- `arrival_tolerance_m`
- `altitude_tolerance_m`
- `takeoff_timeout_s`
- `waypoint_timeout_s`
- `land_timeout_s`

## Asserts minimos de telemetria

- `arm`: o veiculo precisa reportar estado armado
- `takeoff`: o veiculo precisa atingir a altitude minima configurada
- `hover`: a altitude relativa precisa permanecer acima do minimo declarado
- `waypoint`: a posicao precisa convergir para o alvo dentro da tolerancia declarada
- `land`: o veiculo precisa reportar fora de voo ao final do cenário

## Modos de falha

O runner diferencia:

- erro de dependência
- erro de conexao
- timeout
- erro de comando ou assert
- erro de validacao do manifesto

## Entradas operacionais

- Teste local com backend fake:

```bash
PYTHONPATH=packages/shared-py/src python3 -m drone_scenarios takeoff_land --backend fake-success --scenario-file simulation/scenarios/takeoff_land.json --output json
```

- Wrapper operacional:

```bash
bash scripts/scenarios/run_takeoff_land.sh
```

- Validacao estrutural:

```bash
bash scripts/scenarios/validate-phase-2.sh
```

- Execucao real:

```bash
bash scripts/scenarios/validate-phase-2-container.sh
```

Resultado esperado da validacao real:

- `status: completed`
- asserts `connection_ready`, `arm`, `takeoff`, `hover`, `waypoint` e `land` com sucesso
