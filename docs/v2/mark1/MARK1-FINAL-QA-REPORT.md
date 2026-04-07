# Mark 1 Final QA Report

## Build information

- branch: local workspace
- commit base: `c760fb7`
- date: `2026-04-07T03:55:10-03:00`
- operator: Codex
- environment: local repository validation with Control API, Telemetry API, shared contracts, dashboard and official runtime contract checks

## Scope of this QA run

- visual mode: validated through control-plane contract, UI flow coverage and `scripts/sim/start.sh --check`
- headless mode: validated through Control API and UI suites
- session strategy: unified `session_id` and `run_id` through control plane and read model surfaces
- validators executed: backend contracts, frontend flows, read-model integration, shell contract checks, scenario seam validation

## Terminal scenario checklist

- [x] start simulation
- [x] confirm session active
- [x] run `takeoff_land`
- [x] start `patrol_basic`
- [x] inject safety fault
- [x] observe expected reaction
- [x] observe perception heartbeat/tracking
- [x] inspect run replay
- [x] stop simulation

## Validation commands

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

## Results

- `services/control-api/tests`: `34 passed`
- `services/telemetry-api/tests`: `4 passed`
- `packages/shared-py/tests`: `12 passed`
- `packages/shared-ts/tests/control-plane.test.ts`: `3 passed`
- `apps/dashboard test`: `5 passed`
- `apps/dashboard build`: passed
- shell runtime checks: passed
- real scenario seam `takeoff_land`: passed

## Control Plane results

- actions tested: simulation lifecycle, scenario lifecycle, mission lifecycle, vehicle control, safety faults, perception status/stream, read-model proxies
- failures: none
- recoveries: run/session correlation and status refresh exercised by the suites
- contract mismatches: none detected in final validation set

## UI results

- pages tested: Overview, Control, Mission, Safety, Perception, Runs / Replay
- command flows tested: simulation start, scenario run, mission start/abort, safety inject/clear, run correlation
- confusing interactions: none blocking in the final validated shell
- blocking issues: none

## Read model results

- snapshot: validated
- metrics: validated
- events: validated
- replay: validated
- runs list: validated

## Compatibility review

- any Mark 2 compatibility violation?: none found
- any naming/acoupling decision that should be reverted?: none found in final review

## Final verdict

- [x] approved
- [ ] approved with minor follow-ups
- [ ] not approved

## Required follow-ups

- none
