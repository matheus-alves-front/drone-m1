# Mark 1 QA and Validation

## Objetivo
Fechar o ciclo do refactor com validação terminal real.

## Níveis de validação

### 1. Structural validation
- paths
- contracts
- generated files
- schema checks

### 2. Unit validation
- action handlers
- domain mappers
- capability registry-like metadata
- API validation

### 3. Component validation
- control plane adapters
- ROS 2 command adapters
- read model services
- operator UI features

### 4. Integration validation
- control API + runtime adapters
- control API + telemetry read model
- UI + control API
- UI + read model

### 5. End-to-end validation
- simulation session start
- run takeoff_land
- run patrol
- mission abort
- fault injection
- replay visibility
- perception visibility
- stop simulation

## Terminal QA suite
No final do Mark 1 deve existir uma suíte terminal que prove:
1. system boots by control plane
2. operator can run a scenario
3. operator can start/abort mission
4. operator can inject a safety fault
5. operator can inspect resulting run and replay
6. operator can stop the session safely

## Final validation command set

```bash
PYTHONPATH=services/control-api:packages/shared-py/src .venv-r3/bin/python -m pytest services/control-api/tests -q
PYTHONPATH=services/telemetry-api .venv-r3/bin/python -m pytest services/telemetry-api/tests -q
PYTHONPATH=packages/shared-py/src .venv-r3/bin/python -m pytest packages/shared-py/tests -q
node --experimental-strip-types --test packages/shared-ts/tests/control-plane.test.ts
npm --prefix apps/dashboard test
npm --prefix apps/dashboard run build
bash scripts/sim/start.sh --check
bash scripts/sim/stop.sh --check
PYTHONPATH=packages/shared-py/src \
  bash scripts/scenarios/run_scenario.sh \
  simulation/scenarios/takeoff_land.json \
  --backend fake-success \
  --output json
```

## Final QA result

- a suíte terminal automatizada do Mark 1 passou
- control plane, read model e operator UI foram validados juntos
- os relatórios finais desta rodada ficam em:
- `docs/v2/mark1/MARK1-FINAL-QA-REPORT.md`
- `docs/v2/mark1/MARK1-ACCEPTANCE-REPORT.md`
- `docs/v2/mark1/MARK1-FINAL-ACCEPTANCE-MATRIX.md`

## Final QA deliverables
- runbook final em `services/control-api/README.md`, `apps/dashboard/README.md` e `docs/v2/mark1/MARK1-ENVIRONMENT-STRATEGY.md`
- troubleshooting final em `services/control-api/README.md` e `apps/dashboard/README.md`
- acceptance matrix em `docs/v2/mark1/MARK1-FINAL-ACCEPTANCE-MATRIX.md`
- final QA report template em `docs/v2/mark1/MARK1-FINAL-QA-REPORT-TEMPLATE.md`
- final QA report em `docs/v2/mark1/MARK1-FINAL-QA-REPORT.md`
- final acceptance report em `docs/v2/mark1/MARK1-ACCEPTANCE-REPORT.md`
- final validation command set nesta página

## Definition of Done for Mark 1
O Mark 1 só termina quando a suíte terminal passa e o sistema é operável por superfície unificada.
