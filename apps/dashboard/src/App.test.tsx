import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

describe("App", () => {
  let sessionStatus: "active" | "idle";
  let missionStatus: "idle" | "arming";
  let activeFaults: Array<{ fault_type: string; detail: string }>;
  let postedPaths: string[];
  let runInventory: Array<{
    run_id: string;
    run_kind: string;
    name: string;
    status: string;
    session_id: string;
    artifacts: string[];
    summary: string;
  }>;
  let scenarioState: {
    takeoff_land: { status: string; active_run_id: string | null; last_run_id: string | null; summary: string };
    patrol_basic: { status: string; active_run_id: string | null; last_run_id: string | null; summary: string };
  };

  beforeEach(() => {
    sessionStatus = "active";
    missionStatus = "idle";
    activeFaults = [];
    postedPaths = [];
    runInventory = [
      {
        run_id: "telemetry-run",
        run_kind: "telemetry_session",
        name: "telemetry:telemetry-run",
        status: "running",
        session_id: "session-1",
        artifacts: [],
        summary: "5 events, 3 metrics",
      },
    ];
    scenarioState = {
      takeoff_land: {
        status: "idle",
        active_run_id: null,
        last_run_id: null,
        summary: "takeoff_land ready",
      },
      patrol_basic: {
        status: "idle",
        active_run_id: null,
        last_run_id: null,
        summary: "patrol_basic ready",
      },
    };

    vi.stubGlobal("confirm", vi.fn(() => true));
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        const method = init?.method ?? "GET";

        if (url.includes("/api/v1/control/status")) {
          return new Response(
            JSON.stringify({
              status: "ok",
              data: {
                service: { name: "control-api", phase: "R15", mode: "final-acceptance", status: "ok" },
                session: {
                  session_id: "session-1",
                  status: sessionStatus,
                  mode: "headless",
                  environment: {
                    environment_name: "mark1-local-sim",
                    simulator_family: "px4-gazebo-harmonic",
                    vehicle_profile: "x500",
                    baseline: "ubuntu-22.04-ros2-humble",
                  },
                  components: [],
                  started_at: "2026-04-07T12:00:00+00:00",
                  stopped_at: null,
                },
                runs: {
                  run_count: runInventory.length,
                  active_run:
                    scenarioState.takeoff_land.active_run_id !== null
                      ? {
                          run_id: scenarioState.takeoff_land.active_run_id,
                          run_kind: "scenario_execution",
                          name: "scenario.run:takeoff_land",
                          status: "running",
                          session_id: "session-1",
                          artifacts: [],
                          summary: "running",
                        }
                      : null,
                },
                catalog: { action_count: 23, capability_count: 11, scenario_count: 6 },
              },
              errors: [],
            }),
          );
        }

        if (url.includes("/api/v1/control/capabilities")) {
          return new Response(
            JSON.stringify({
              status: "ok",
              data: [
                {
                  capability_name: "simulation.lifecycle",
                  status: "available",
                  action_names: ["simulation.start", "simulation.stop", "simulation.restart"],
                  constraints: {},
                },
                {
                  capability_name: "mission.control",
                  status: "available",
                  action_names: ["mission.start", "mission.abort", "mission.reset"],
                  constraints: {},
                },
                {
                  capability_name: "vehicle.basic_control",
                  status: "available",
                  action_names: ["vehicle.arm", "vehicle.disarm", "vehicle.takeoff", "vehicle.land"],
                  constraints: {},
                },
                {
                  capability_name: "safety.fault_injection",
                  status: "available",
                  action_names: ["safety.inject_fault", "safety.clear_fault"],
                  constraints: {},
                },
                {
                  capability_name: "telemetry.read_model",
                  status: "available",
                  action_names: ["telemetry.snapshot.get", "telemetry.metrics.get"],
                  constraints: {},
                },
              ],
              errors: [],
            }),
          );
        }

        if (method === "GET" && url.includes("/api/v1/control/scenarios") && !url.includes("/status")) {
          return new Response(
            JSON.stringify({
              status: "ok",
              data: [
                {
                  scenario_name: "takeoff_land",
                  scenario_kind: "flight",
                  input_contract: "simulation/scenarios/takeoff_land.json",
                  output_contract: "ActionResult",
                  supports_visual: true,
                  supports_headless: true,
                  objective: "quick flight smoke",
                  control_plane_status: "available",
                  phase_hint: "available through the unified scenario surface in R4",
                },
                {
                  scenario_name: "patrol_basic",
                  scenario_kind: "mission",
                  input_contract: "simulation/scenarios/patrol_basic.json",
                  output_contract: "ActionResult",
                  supports_visual: true,
                  supports_headless: true,
                  objective: "patrol mission",
                  control_plane_status: "available",
                  phase_hint: "available through the mission control surface in R5",
                },
              ],
              errors: [],
            }),
          );
        }

        if (url.includes("/api/v1/control/scenarios/takeoff_land/status")) {
          return new Response(JSON.stringify({ status: "ok", data: { scenario_name: "takeoff_land", ...scenarioState.takeoff_land }, errors: [] }));
        }

        if (url.includes("/api/v1/control/scenarios/patrol_basic/status")) {
          return new Response(JSON.stringify({ status: "ok", data: { scenario_name: "patrol_basic", ...scenarioState.patrol_basic }, errors: [] }));
        }

        if (url.includes("/api/v1/control/missions/status")) {
          return new Response(
            JSON.stringify({
              status: "ok",
              data: {
                mission_id: "patrol_basic",
                mission_type: "patrol",
                status: missionStatus,
                plan_ref: "simulation/scenarios/patrol_basic.json",
                constraints: {
                  detail: missionStatus === "idle" ? "mission idle" : "waypoint 1",
                  current_waypoint_index: missionStatus === "idle" ? 0 : 1,
                  total_waypoints: 3,
                  last_command: missionStatus === "idle" ? "reset" : "start",
                  terminal: false,
                },
                fallback_policy: "return_to_home",
                required_capabilities: ["mission.control"],
              },
              errors: [],
            }),
          );
        }

        if (url.includes("/api/v1/control/safety/status")) {
          return new Response(
            JSON.stringify({
              status: "ok",
              data: {
                state: activeFaults.length ? "active" : "clear",
                active_faults: activeFaults,
                summary: activeFaults.length ? "gps_loss | land | operator test" : "safety state clear",
              },
              errors: [],
            }),
          );
        }

        if (url.includes("/api/v1/control/perception/status")) {
          return new Response(
            JSON.stringify({
              status: "ok",
              data: {
                healthy: true,
                detections_available: true,
                detail: "heartbeat ok | tracked object present | label=person | event=perception_event | latency=0.110s",
                last_heartbeat_age_ms: 180,
              },
              errors: [],
            }),
          );
        }

        if (url.includes("/api/v1/control/perception/stream/status")) {
          return new Response(
            JSON.stringify({
              status: "ok",
              data: {
                stream_available: true,
                detail: "camera stream proxy configured for operator access",
                source: "http://127.0.0.1:9000/stream",
                fps: 24,
              },
              errors: [],
            }),
          );
        }

        if (url.includes("/api/v1/read/snapshot")) {
          return new Response(
            JSON.stringify({
              status: "ok",
              data: {
                current_run_id: "telemetry-run",
                run_id: "telemetry-run",
                session_id: "session-1",
                updated_at_ns: 123456789,
                vehicle_state: {
                  connected: true,
                  armed: true,
                  nav_state: "AUTO_LOITER",
                  relative_altitude_m: 3.2,
                },
                mission_status: {
                  phase: missionStatus,
                  detail: missionStatus === "idle" ? "mission idle" : "waypoint 1",
                  current_waypoint_index: missionStatus === "idle" ? 0 : 1,
                  total_waypoints: 3,
                  last_command: missionStatus === "idle" ? "reset" : "start",
                },
                safety_status: {
                  active: activeFaults.length > 0,
                  rule: activeFaults.length ? "gps_loss" : "none",
                  action: activeFaults.length ? "land" : "none",
                },
                tracked_object: { tracked: true, label: "person", confidence: 0.93 },
                perception_heartbeat: { healthy: true, pipeline_latency_s: 0.11, frame_age_s: 0.18 },
                perception_event: { event_type: "tracking_update", detail: "target reacquired" },
                latest_by_kind: {
                  vehicle_state: {
                    run_id: "telemetry-run",
                    source: "telemetry_bridge",
                    kind: "vehicle_state",
                    topic: "/drone/vehicle_state",
                    stamp_ns: 10,
                    sequence: 1,
                    received_ns: 11,
                    payload: { connected: true, armed: true },
                  },
                },
              },
              errors: [],
            }),
          );
        }

        if (url.includes("/api/v1/read/runs")) {
          return new Response(
            JSON.stringify({
              status: "ok",
              data: {
                current_telemetry_run_id: "telemetry-run",
                telemetry_runs: [
                  {
                    run_id: "telemetry-run",
                    session_id: "session-1",
                    source: "telemetry_bridge",
                    event_count: 5,
                    metrics_count: 3,
                    last_kind: "mission_status",
                  },
                ],
                runs: runInventory,
              },
              errors: [],
            }),
          );
        }

        if (url.includes("/api/v1/read/metrics")) {
          return new Response(
            JSON.stringify({
              status: "ok",
              data: {
                run_id: "telemetry-run",
                session_id: "session-1",
                source: "telemetry_api",
                metrics: [
                  {
                    seq: 1,
                    run_id: "telemetry-run",
                    session_id: "session-1",
                    mission_phase: missionStatus,
                    altitude_m: 12.3,
                    relative_altitude_m: 3.2,
                    perception_latency_s: 0.11,
                    safety_action: activeFaults.length ? "land" : "none",
                  },
                ],
              },
              errors: [],
            }),
          );
        }

        if (url.includes("/api/v1/read/events")) {
          return new Response(
            JSON.stringify({
              status: "ok",
              data: {
                run_id: "telemetry-run",
                session_id: "session-1",
                source: "telemetry_api",
                events: [
                  {
                    run_id: "telemetry-run",
                    source: "telemetry_bridge",
                    kind: "mission_status",
                    topic: "/drone/mission_status",
                    stamp_ns: 100,
                    sequence: 2,
                    received_ns: 101,
                    payload: { phase: missionStatus },
                  },
                ],
              },
              errors: [],
            }),
          );
        }

        if (url.includes("/api/v1/read/replay")) {
          return new Response(
            JSON.stringify({
              status: "ok",
              data: {
                run_id: "telemetry-run",
                session_id: "session-1",
                snapshot: {
                  run_id: "telemetry-run",
                  session_id: "session-1",
                  vehicle_state: { connected: true },
                  vehicle_command_status: {},
                  mission_status: {},
                  safety_status: {},
                  tracked_object: {},
                  perception_heartbeat: {},
                  perception_event: {},
                  latest_by_kind: {},
                },
                events: [
                  {
                    run_id: "telemetry-run",
                    source: "telemetry_bridge",
                    kind: "mission_status",
                    topic: "/drone/mission_status",
                    stamp_ns: 100,
                    sequence: 2,
                    received_ns: 101,
                    payload: { phase: missionStatus },
                  },
                ],
                metrics: [],
              },
              errors: [],
            }),
          );
        }

        if (method === "POST" && url.includes("/api/v1/control/simulation/start")) {
          postedPaths.push("/api/v1/control/simulation/start");
          sessionStatus = "active";
          runInventory = [
            {
              run_id: "run-start",
              run_kind: "session_lifecycle",
              name: "simulation.start",
              status: "completed",
              session_id: "session-1",
              artifacts: [],
              summary: "simulation session started",
            },
            ...runInventory,
          ];
          return new Response(
            JSON.stringify({
              status: "ok",
              data: {
                request_id: "req-1",
                accepted: true,
                status: "completed",
                message: "simulation session started",
                run_id: "run-start",
                artifacts: [],
                errors: [],
              },
              errors: [],
            }),
          );
        }

        if (method === "POST" && url.includes("/api/v1/control/scenarios/takeoff_land/run")) {
          postedPaths.push("/api/v1/control/scenarios/takeoff_land/run");
          scenarioState.takeoff_land = {
            status: "running",
            active_run_id: "run-scenario",
            last_run_id: "run-scenario",
            summary: "takeoff_land started through the unified scenario surface",
          };
          runInventory = [
            {
              run_id: "run-scenario",
              run_kind: "scenario_execution",
              name: "scenario.run:takeoff_land",
              status: "running",
              session_id: "session-1",
              artifacts: [],
              summary: "takeoff_land running",
            },
            ...runInventory,
          ];
          return new Response(
            JSON.stringify({
              status: "ok",
              data: {
                request_id: "req-2",
                accepted: true,
                status: "running",
                message: "takeoff_land started through the unified scenario surface",
                run_id: "run-scenario",
                artifacts: [],
                errors: [],
              },
              errors: [],
            }),
          );
        }

        if (method === "POST" && url.includes("/api/v1/control/missions/start")) {
          postedPaths.push("/api/v1/control/missions/start");
          missionStatus = "arming";
          scenarioState.patrol_basic = {
            status: "running",
            active_run_id: "run-mission",
            last_run_id: "run-mission",
            summary: "patrol_basic started through mission control",
          };
          runInventory = [
            {
              run_id: "run-mission",
              run_kind: "mission_execution",
              name: "mission.start:patrol_basic",
              status: "running",
              session_id: "session-1",
              artifacts: [],
              summary: "patrol_basic accepted by mission control",
            },
            ...runInventory,
          ];
          return new Response(
            JSON.stringify({
              status: "ok",
              data: {
                request_id: "req-3",
                accepted: true,
                status: "running",
                message: "patrol_basic started through mission control",
                run_id: "run-mission",
                artifacts: [],
                errors: [],
              },
              errors: [],
            }),
          );
        }

        if (method === "POST" && url.includes("/api/v1/control/missions/abort")) {
          postedPaths.push("/api/v1/control/missions/abort");
          missionStatus = "idle";
          runInventory = [
            {
              run_id: "run-mission-abort",
              run_kind: "mission_control",
              name: "mission.abort:patrol_basic",
              status: "completed",
              session_id: "session-1",
              artifacts: [],
              summary: "patrol_basic abort requested through mission control",
            },
            ...runInventory,
          ];
          return new Response(
            JSON.stringify({
              status: "ok",
              data: {
                request_id: "req-3b",
                accepted: true,
                status: "completed",
                message: "patrol_basic abort requested",
                run_id: "run-mission-abort",
                artifacts: [],
                errors: [],
              },
              errors: [],
            }),
          );
        }

        if (method === "POST" && url.includes("/api/v1/control/safety/faults/inject")) {
          postedPaths.push("/api/v1/control/safety/faults/inject");
          activeFaults = [{ fault_type: "gps_loss", detail: "operator test" }];
          runInventory = [
            {
              run_id: "run-safety",
              run_kind: "safety_control",
              name: "safety.inject_fault",
              status: "completed",
              session_id: "session-1",
              artifacts: [],
              summary: "gps_loss injected through the safety control surface",
            },
            ...runInventory,
          ];
          return new Response(
            JSON.stringify({
              status: "ok",
              data: {
                request_id: "req-4",
                accepted: true,
                status: "completed",
                message: "safety fault gps_loss injected",
                run_id: "run-safety",
                artifacts: [],
                errors: [],
              },
              errors: [],
            }),
          );
        }

        if (method === "POST" && url.includes("/api/v1/control/safety/faults/clear")) {
          postedPaths.push("/api/v1/control/safety/faults/clear");
          activeFaults = [];
          runInventory = [
            {
              run_id: "run-safety-clear",
              run_kind: "safety_control",
              name: "safety.clear_fault",
              status: "completed",
              session_id: "session-1",
              artifacts: [],
              summary: "gps_loss cleared through the safety control surface",
            },
            ...runInventory,
          ];
          return new Response(
            JSON.stringify({
              status: "ok",
              data: {
                request_id: "req-5",
                accepted: true,
                status: "completed",
                message: "safety fault gps_loss cleared",
                run_id: "run-safety-clear",
                artifacts: [],
                errors: [],
              },
              errors: [],
            }),
          );
        }

        if (method === "POST" && url.includes("/api/v1/control/vehicles/arm")) {
          postedPaths.push("/api/v1/control/vehicles/arm");
          runInventory = [
            {
              run_id: "run-vehicle-arm",
              run_kind: "vehicle_control",
              name: "vehicle.arm",
              status: "completed",
              session_id: "session-1",
              artifacts: [],
              summary: "vehicle.arm requested through the vehicle control surface",
            },
            ...runInventory,
          ];
          return new Response(
            JSON.stringify({
              status: "ok",
              data: {
                request_id: "req-6",
                accepted: true,
                status: "completed",
                message: "vehicle.arm requested",
                run_id: "run-vehicle-arm",
                artifacts: [],
                errors: [],
              },
              errors: [],
            }),
          );
        }

        if (method === "POST" && url.includes("/api/v1/control/vehicles/goto")) {
          postedPaths.push("/api/v1/control/vehicles/goto");
          runInventory = [
            {
              run_id: "run-vehicle-goto",
              run_kind: "vehicle_control",
              name: "vehicle.goto",
              status: "completed",
              session_id: "session-1",
              artifacts: [],
              summary: "vehicle.goto requested through the vehicle control surface",
            },
            ...runInventory,
          ];
          return new Response(
            JSON.stringify({
              status: "ok",
              data: {
                request_id: "req-7",
                accepted: true,
                status: "completed",
                message: "vehicle.goto requested",
                run_id: "run-vehicle-goto",
                artifacts: [],
                errors: [],
              },
              errors: [],
            }),
          );
        }

        return new Response("not found", { status: 404 });
      }),
    );
  });

  it("renders the operator shell with control, perception and read model surfaces", async () => {
    render(<App />);

    expect(screen.getByText("Mark 1 Operator Console")).toBeInTheDocument();
    expect(await screen.findByText("Capability surface")).toBeInTheDocument();
    expect(screen.getByText("takeoff_land")).toBeInTheDocument();
    expect(screen.getAllByText("telemetry-run")[0]).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Perception" }));
    expect(await screen.findByText("Perception pipeline")).toBeInTheDocument();
    expect(screen.getByText("Camera / stream proxy")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Runs / Replay" }));
    expect(await screen.findByText("Run inventory")).toBeInTheDocument();
    expect(screen.getByText("Metric samples")).toBeInTheDocument();
    expect(screen.getByText("Replay")).toBeInTheDocument();
  });

  it("invokes the session start action through the control api", async () => {
    sessionStatus = "idle";
    render(<App />);

    await userEvent.click(await screen.findByRole("button", { name: "Control" }));
    await userEvent.click(screen.getByRole("button", { name: "Start simulation" }));

    expect(await screen.findByText("simulation session started")).toBeInTheDocument();
    expect(postedPaths).toContain("/api/v1/control/simulation/start");
  });

  it("runs takeoff_land and correlates the run in the replay view", async () => {
    render(<App />);

    await userEvent.click(await screen.findByRole("button", { name: "Control" }));
    await userEvent.click(screen.getByRole("button", { name: "Run scenario" }));

    expect((await screen.findAllByText("takeoff_land started through the unified scenario surface")).length).toBeGreaterThan(0);
    expect(postedPaths).toContain("/api/v1/control/scenarios/takeoff_land/run");

    await userEvent.click(screen.getByRole("button", { name: "Open run" }));
    expect(await screen.findByText("Action correlation")).toBeInTheDocument();
    expect(screen.getAllByText("run-scenario")[0]).toBeInTheDocument();
  });

  it("starts and aborts the mission, then injects and clears a safety fault from dedicated panels", async () => {
    render(<App />);

    await userEvent.click(await screen.findByRole("button", { name: "Mission" }));
    await userEvent.click(screen.getByRole("button", { name: "Start mission" }));
    expect(await screen.findByText("patrol_basic started through mission control")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Abort mission" }));
    expect(await screen.findByText("patrol_basic abort requested")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Safety" }));
    await userEvent.click(screen.getByRole("button", { name: "Inject fault" }));
    expect(await screen.findByText("safety fault gps_loss injected")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Clear fault" }));
    expect(await screen.findByText("safety fault gps_loss cleared")).toBeInTheDocument();

    expect(postedPaths).toContain("/api/v1/control/missions/start");
    expect(postedPaths).toContain("/api/v1/control/missions/abort");
    expect(postedPaths).toContain("/api/v1/control/safety/faults/inject");
    expect(postedPaths).toContain("/api/v1/control/safety/faults/clear");
  });

  it("dispatches vehicle control actions from the dedicated panel", async () => {
    render(<App />);

    await userEvent.click(await screen.findByRole("button", { name: "Control" }));
    await userEvent.click(screen.getByRole("button", { name: "Arm" }));
    expect(await screen.findByText("vehicle.arm requested")).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText("Latitude"), "-22.9984");
    await userEvent.type(screen.getByLabelText("Longitude"), "-43.3657");
    await userEvent.click(screen.getByRole("button", { name: "Send goto" }));
    expect(await screen.findByText("vehicle.goto requested")).toBeInTheDocument();

    expect(postedPaths).toContain("/api/v1/control/vehicles/arm");
    expect(postedPaths).toContain("/api/v1/control/vehicles/goto");
  });
});
