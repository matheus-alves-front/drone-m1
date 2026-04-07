import type {
  ActionResultPayload,
  ApiEnvelope,
  CapabilityDefinition,
  ControlStatusPayload,
  MissionDefinitionPayload,
  PerceptionStatusPayload,
  PerceptionStreamStatusPayload,
  SafetySurfacePayload,
  ScenarioEntry,
  ScenarioStatusPayload,
} from "../types";

const controlApiBaseUrl = import.meta.env.VITE_CONTROL_API_BASE_URL ?? "http://127.0.0.1:8090";
const requestTimeoutMs = Number(import.meta.env.VITE_CONTROL_API_TIMEOUT_MS ?? 15000);

function normalizeHttpUrl(baseUrl: string): string {
  return baseUrl.replace(/\/+$/, "");
}

async function fetchEnvelope<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), requestTimeoutMs);
  let response: Response;
  try {
    response = await fetch(`${normalizeHttpUrl(controlApiBaseUrl)}${path}`, {
      ...init,
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error(`control api request timed out for ${path}`);
    }
    throw error;
  } finally {
    window.clearTimeout(timeoutId);
  }
  const payload = (await response.json()) as ApiEnvelope<T>;
  if (!response.ok || payload.errors.length > 0) {
    const message = payload.errors[0]?.message ?? `control api request failed for ${path}: ${response.status}`;
    throw new Error(message);
  }
  return payload.data;
}

function buildActionBody(input: Record<string, unknown>): string {
  return JSON.stringify({
    input,
    requested_by: {
      type: "operator_ui",
      id: "dashboard",
    },
  });
}

function postAction<T>(path: string, input: Record<string, unknown>): Promise<T> {
  return fetchEnvelope<T>(path, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: buildActionBody(input),
  });
}

export function fetchControlStatus(): Promise<ControlStatusPayload> {
  return fetchEnvelope<ControlStatusPayload>("/api/v1/control/status");
}

export function fetchCapabilities(): Promise<CapabilityDefinition[]> {
  return fetchEnvelope<CapabilityDefinition[]>("/api/v1/control/capabilities");
}

export function fetchScenarios(): Promise<ScenarioEntry[]> {
  return fetchEnvelope<ScenarioEntry[]>("/api/v1/control/scenarios");
}

export function fetchScenarioStatus(scenarioName: string): Promise<ScenarioStatusPayload> {
  return fetchEnvelope<ScenarioStatusPayload>(`/api/v1/control/scenarios/${scenarioName}/status`);
}

export function fetchMissionStatus(): Promise<MissionDefinitionPayload> {
  return fetchEnvelope<MissionDefinitionPayload>("/api/v1/control/missions/status");
}

export function fetchSafetyStatus(): Promise<SafetySurfacePayload> {
  return fetchEnvelope<SafetySurfacePayload>("/api/v1/control/safety/status");
}

export function fetchPerceptionStatus(): Promise<PerceptionStatusPayload> {
  return fetchEnvelope<PerceptionStatusPayload>("/api/v1/control/perception/status");
}

export function fetchPerceptionStreamStatus(): Promise<PerceptionStreamStatusPayload> {
  return fetchEnvelope<PerceptionStreamStatusPayload>("/api/v1/control/perception/stream/status");
}

export function invokeSimulationStart(mode: "headless" | "visual"): Promise<ActionResultPayload> {
  return postAction<ActionResultPayload>("/api/v1/control/simulation/start", { mode });
}

export function invokeSimulationStop(): Promise<ActionResultPayload> {
  return postAction<ActionResultPayload>("/api/v1/control/simulation/stop", {});
}

export function invokeSimulationRestart(mode: "headless" | "visual"): Promise<ActionResultPayload> {
  return postAction<ActionResultPayload>("/api/v1/control/simulation/restart", { mode });
}

export function invokeScenarioRun(scenarioName: string): Promise<ActionResultPayload> {
  return postAction<ActionResultPayload>(`/api/v1/control/scenarios/${scenarioName}/run`, {});
}

export function invokeScenarioCancel(scenarioName: string): Promise<ActionResultPayload> {
  return postAction<ActionResultPayload>(`/api/v1/control/scenarios/${scenarioName}/cancel`, {});
}

export function invokeMissionStart(missionName: string): Promise<ActionResultPayload> {
  return postAction<ActionResultPayload>("/api/v1/control/missions/start", { mission_name: missionName });
}

export function invokeMissionAbort(missionName: string, reason: string): Promise<ActionResultPayload> {
  return postAction<ActionResultPayload>("/api/v1/control/missions/abort", { mission_name: missionName, reason });
}

export function invokeMissionReset(missionName: string, reason: string): Promise<ActionResultPayload> {
  return postAction<ActionResultPayload>("/api/v1/control/missions/reset", { mission_name: missionName, reason });
}

export function invokeVehicleCommand(command: string, input: Record<string, unknown> = {}): Promise<ActionResultPayload> {
  return postAction<ActionResultPayload>(`/api/v1/control/vehicles/${command}`, input);
}

export function invokeSafetyInjectFault(
  faultType: string,
  value: number,
  detail: string,
): Promise<ActionResultPayload> {
  return postAction<ActionResultPayload>("/api/v1/control/safety/faults/inject", {
    fault_type: faultType,
    value,
    detail,
  });
}

export function invokeSafetyClearFault(faultType: string): Promise<ActionResultPayload> {
  return postAction<ActionResultPayload>("/api/v1/control/safety/faults/clear", { fault_type: faultType });
}
