# Mark 1 Final Acceptance Matrix

| Área | Critério | Evidência esperada | Status |
|---|---|---|---|
| Control Plane | existe Control API unificada | endpoints, docs e testes | PASS |
| Simulation Session | start/stop/status via surface única | action logs + runbook | PASS |
| Scenario Control | `takeoff_land` roda pela nova superfície | run status + replay | PASS |
| Mission Control | missão pode iniciar/abortar por surface única | run status + state transitions | PASS |
| Vehicle Control | arm/land/rtl via action formal | action results + events | PASS |
| Safety | faults podem ser injetados/limpos via action formal | status + reação observável | PASS |
| Perception | heartbeat/tracking observáveis pela interface humana | UI + read model | PASS |
| Read Model | snapshot, metrics, events, runs e replay consistentes | APIs + UI | PASS |
| Operator UI | UI controla e observa o sistema | walkthrough operacional | PASS |
| Environment | experiência local visual oficial documentada | runbook | PASS |
| QA | suíte terminal completa executada | relatório final | PASS |
| Compatibility | Mark 1 preserva caminho para Mark 2 | revisão arquitetural | PASS |

## Evidência consolidada

- Control Plane: `services/control-api/tests/test_app.py`, `services/control-api/README.md`
- Simulation Session: `simulation.start`, `simulation.stop`, `simulation.restart` cobertos na suíte da Control API e checks oficiais de `scripts/sim/*.sh`
- Scenario Control: `takeoff_land` validado pela Control API, pela UI e pelo seam real `scripts/scenarios/run_scenario.sh --backend fake-success`
- Mission Control: `mission.start`, `mission.abort` e `mission.reset` cobertos na suíte da Control API e na suíte da UI
- Vehicle Control: `vehicle.*` coberto pela suíte da Control API
- Safety: `safety.inject_fault`, `safety.clear_fault` e `safety.status.get` cobertos pela Control API e pela UI
- Perception: `perception.status.get` e `perception.stream.status.get` cobertos na Control API e apresentados na UI
- Read Model: `snapshot`, `metrics`, `events`, `runs` e `replay` cobertos em `services/telemetry-api/tests/*` e `services/control-api/tests/test_app.py`
- Operator UI: `apps/dashboard/src/App.test.tsx` e `apps/dashboard/README.md`
- Environment: `docs/v2/mark1/MARK1-ENVIRONMENT-STRATEGY.md`, `services/control-api/README.md`
- QA: `docs/v2/mark1/MARK1-FINAL-QA-REPORT.md`
- Compatibility: `docs/v2/mark1/MARK1-ACCEPTANCE-REPORT.md`, `docs/v2/MARK1-TO-MARK2-COMPATIBILITY-RULES.md`
