import test from "node:test";
import assert from "node:assert/strict";

import { initialActionCatalog, initialCapabilityCatalog } from "../src/control-plane/catalog.ts";
import { actionExecutionStatuses } from "../src/control-plane/contracts.ts";

test("shared control-plane catalog covers the R1 action surface", () => {
  const actionNames = new Set(initialActionCatalog.map((definition) => definition.action_name));

  for (const requiredAction of [
    "simulation.restart",
    "scenario.status.get",
    "capabilities.list",
    "telemetry.snapshot.get",
    "telemetry.runs.list",
  ]) {
    assert.ok(actionNames.has(requiredAction), `missing required action: ${requiredAction}`);
  }
});

test("scenario capability does not leak mission executor actions", () => {
  const patrolCapability = initialCapabilityCatalog.find(
    (definition) => definition.capability_name === "scenario.patrol_basic.run",
  );

  assert.ok(patrolCapability);
  assert.deepEqual(patrolCapability.action_names, [
    "scenario.run",
    "scenario.cancel",
    "scenario.status.get",
  ]);
});

test("action execution statuses cover cancellation and timeout semantics", () => {
  assert.ok(actionExecutionStatuses.includes("cancelled"));
  assert.ok(actionExecutionStatuses.includes("timed_out"));
});
