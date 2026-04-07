# Mark 1 Final QA Report Template

## Build information
- branch:
- commit:
- date:
- operator:
- environment:

## Scope of this QA run
- visual mode:
- headless mode:
- session strategy:
- validators executed:

## Terminal scenario checklist
- [ ] start simulation
- [ ] confirm session active
- [ ] run `takeoff_land`
- [ ] start `patrol_basic`
- [ ] inject safety fault
- [ ] observe expected reaction
- [ ] observe perception heartbeat/tracking
- [ ] inspect run replay
- [ ] stop simulation

## Control Plane results
- actions tested:
- failures:
- recoveries:
- contract mismatches:

## UI results
- pages tested:
- command flows tested:
- confusing interactions:
- blocking issues:

## Read model results
- snapshot:
- metrics:
- events:
- replay:
- runs list:

## Compatibility review
- any Mark 2 compatibility violation?
- any naming/acoupling decision that should be reverted?

## Final verdict
- [ ] approved
- [ ] approved with minor follow-ups
- [ ] not approved

## Required follow-ups
- item 1
- item 2
- item 3
