import { act, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

class MockWebSocket {
  static instances: MockWebSocket[] = [];

  onmessage: ((event: MessageEvent) => void) | null = null;
  url: string;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  close() {
    return undefined;
  }

  emit(payload: unknown) {
    this.onmessage?.({ data: JSON.stringify(payload) } as MessageEvent);
  }
}

describe("App", () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    vi.stubGlobal("WebSocket", MockWebSocket as unknown as typeof WebSocket);
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/v1/snapshot")) {
          return new Response(
            JSON.stringify({
              current_run_id: "run-1",
              latest_by_kind: {
                vehicle_state: {
                  run_id: "run-1",
                  source: "telemetry_bridge_node",
                  kind: "vehicle_state",
                  topic: "/drone/vehicle_state",
                  stamp_ns: 2,
                  sequence: 1,
                  received_ns: 3,
                  payload: {
                    connected: true,
                    armed: true,
                    relative_altitude_m: 3.2,
                    failsafe: false,
                  },
                },
                mission_status: {
                  run_id: "run-1",
                  source: "telemetry_bridge_node",
                  kind: "mission_status",
                  topic: "/drone/mission_status",
                  stamp_ns: 2,
                  sequence: 2,
                  received_ns: 3,
                  payload: {
                    phase: "hover",
                    detail: "waiting",
                    current_waypoint_index: 0,
                    total_waypoints: 3,
                    terminal: false,
                  },
                },
                safety_status: {
                  run_id: "run-1",
                  source: "telemetry_bridge_node",
                  kind: "safety_status",
                  topic: "/drone/safety_status",
                  stamp_ns: 2,
                  sequence: 3,
                  received_ns: 3,
                  payload: {
                    active: false,
                    rule: "none",
                    action: "none",
                    trigger_count: 0,
                  },
                },
                tracked_object: {
                  run_id: "run-1",
                  source: "telemetry_bridge_node",
                  kind: "tracked_object",
                  topic: "/drone/perception/tracked_object",
                  stamp_ns: 2,
                  sequence: 4,
                  received_ns: 3,
                  payload: {
                    tracked: false,
                    label: "sim_target",
                  },
                },
                perception_heartbeat: {
                  run_id: "run-1",
                  source: "telemetry_bridge_node",
                  kind: "perception_heartbeat",
                  topic: "/drone/perception_heartbeat",
                  stamp_ns: 2,
                  sequence: 5,
                  received_ns: 3,
                  payload: {
                    healthy: true,
                    pipeline_latency_s: 0.11,
                  },
                },
              },
            }),
          );
        }
        if (url.includes("/api/v1/metrics")) {
          return new Response(
            JSON.stringify({
              total_events: 5,
              counts_by_kind: {
                vehicle_state: 1,
                mission_status: 1,
                safety_status: 1,
                tracked_object: 1,
                perception_heartbeat: 1,
              },
              counts_by_run: {
                "run-1": 5,
              },
            }),
          );
        }
        if (url.includes("/api/v1/events")) {
          return new Response(
            JSON.stringify([
              {
                run_id: "run-1",
                source: "telemetry_bridge_node",
                kind: "vehicle_state",
                topic: "/drone/vehicle_state",
                stamp_ns: 2,
                sequence: 1,
                received_ns: 3,
                payload: {
                  connected: true,
                  armed: true,
                },
              },
            ]),
          );
        }
        if (url.includes("/api/v1/runs")) {
          return new Response(
            JSON.stringify([
              {
                run_id: "run-1",
                event_count: 5,
                last_kind: "perception_heartbeat",
                last_stamp_ns: 2,
              },
            ]),
          );
        }
        if (url.includes("/api/v1/replay/run-1")) {
          return new Response(
            JSON.stringify([
              {
                run_id: "run-1",
                source: "telemetry_bridge_node",
                kind: "mission_status",
                topic: "/drone/mission_status",
                stamp_ns: 100,
                sequence: 2,
                received_ns: 101,
                payload: { phase: "hover" },
              },
            ]),
          );
        }
        return new Response("not found", { status: 404 });
      }),
    );
  });

  it("renders the current operational state and updates from websocket", async () => {
    render(<App />);

    expect(screen.getByText("Operations dashboard")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("hover")).toBeInTheDocument());
    expect(screen.getByText("run-1 (5)")).toBeInTheDocument();
    expect(screen.getByText("3.20 m")).toBeInTheDocument();
    expect(screen.getByText("Replay")).toBeInTheDocument();
    expect(screen.getByText("5 total envelopes")).toBeInTheDocument();

    await act(async () => {
      MockWebSocket.instances[0].emit({
        type: "telemetry_event",
        event: {
          run_id: "run-1",
          source: "telemetry_bridge_node",
          kind: "mission_status",
          topic: "/drone/mission_status",
          stamp_ns: 3,
          sequence: 6,
          received_ns: 4,
          payload: {
            phase: "patrol",
            detail: "waypoint 1",
            current_waypoint_index: 1,
            total_waypoints: 3,
            terminal: false,
          },
        },
      });
    });

    await waitFor(() => expect(screen.getByText("patrol")).toBeInTheDocument());
    expect(screen.getByText("6 total envelopes")).toBeInTheDocument();
  });
});
