# MAVSDK-SCENARIO-RUNNER-RUNBOOK.md

## Objetivo

Registrar a entrada oficial da Fase 2 para cenarios MAVSDK, mantendo a separacao entre runner de cenario e o workspace ROS 2 da Fase 3.

## Estrutura da Fase 2

- Biblioteca Python reutilizavel: `packages/shared-py/src/drone_scenarios/`
- Wrappers operacionais: `scripts/scenarios/`
- Contratos de cenário: `simulation/scenarios/`

## Cenario disponivel

### takeoff_land

```bash
bash scripts/scenarios/run_takeoff_land.sh
```

### Wrapper generico

```bash
bash scripts/scenarios/run_scenario.sh simulation/scenarios/takeoff_land.json
```

## Dependencias Python

```bash
python3 -m pip install -r packages/shared-py/requirements-phase2.txt
python3 -m pip install -r packages/shared-py/requirements-test.txt
```

## Validacao

```bash
bash scripts/scenarios/validate-phase-2.sh
bash scripts/scenarios/validate-phase-2-container.sh
```

## Evidencia minima de sucesso

- O runner descobre o sistema em `udp://:14540`
- O cenario `takeoff_land` termina com JSON final em `status: completed`
- Os asserts `connection_ready`, `arm`, `takeoff`, `hover`, `waypoint` e `land` aparecem como sucesso

## Limites da Fase 2

- O runner fala com PX4 via MAVSDK.
- O runner nao inicializa bringup ROS 2.
- O runner nao implementa mission manager, safety manager ou bridges.
- A logica de cenário fica separada de scripts shell por uma biblioteca Python reutilizavel.
