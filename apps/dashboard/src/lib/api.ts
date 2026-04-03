import type {
  MetricsResponse,
  RunSummary,
  SnapshotResponse,
  StoredEnvelope,
  TelemetryMessage,
} from "../types";

const apiBaseUrl = import.meta.env.VITE_TELEMETRY_API_BASE_URL ?? "http://127.0.0.1:8080";

function normalizeHttpUrl(baseUrl: string): string {
  return baseUrl.replace(/\/+$/, "");
}

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${normalizeHttpUrl(apiBaseUrl)}${path}`);
  if (!response.ok) {
    throw new Error(`request failed for ${path}: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function fetchSnapshot(): Promise<SnapshotResponse> {
  return fetchJson<SnapshotResponse>("/api/v1/snapshot");
}

export function fetchMetrics(): Promise<MetricsResponse> {
  return fetchJson<MetricsResponse>("/api/v1/metrics");
}

export function fetchEvents(limit = 12, runId?: string): Promise<StoredEnvelope[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (runId) {
    params.set("run_id", runId);
  }
  return fetchJson<StoredEnvelope[]>(`/api/v1/events?${params.toString()}`);
}

export function fetchRuns(): Promise<RunSummary[]> {
  return fetchJson<RunSummary[]>("/api/v1/runs");
}

export function fetchReplay(runId: string, limit = 250): Promise<StoredEnvelope[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  return fetchJson<StoredEnvelope[]>(`/api/v1/replay/${runId}?${params.toString()}`);
}

export function connectTelemetryStream(onMessage: (payload: TelemetryMessage) => void): WebSocket {
  const baseUrl = normalizeHttpUrl(apiBaseUrl);
  const wsUrl = baseUrl.replace(/^http/, "ws");
  const socket = new WebSocket(`${wsUrl}/ws/telemetry`);
  socket.onmessage = (event) => {
    onMessage(JSON.parse(event.data) as TelemetryMessage);
  };
  return socket;
}
