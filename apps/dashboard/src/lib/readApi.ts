import type { ApiEnvelope, EventsResponse, MetricsResponse, ReplayPayload, RunListPayload, SnapshotResponse } from "../types";

const readApiBaseUrl =
  import.meta.env.VITE_READ_API_BASE_URL ??
  import.meta.env.VITE_CONTROL_API_BASE_URL ??
  "http://127.0.0.1:8090";
const requestTimeoutMs = Number(import.meta.env.VITE_READ_API_TIMEOUT_MS ?? 15000);

function normalizeHttpUrl(baseUrl: string): string {
  return baseUrl.replace(/\/+$/, "");
}

function buildUrl(path: string, params?: Record<string, string | number | undefined>): string {
  const url = new URL(`${normalizeHttpUrl(readApiBaseUrl)}${path}`);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

async function fetchEnvelope<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), requestTimeoutMs);
  let response: Response;
  try {
    response = await fetch(buildUrl(path, params), { signal: controller.signal });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error(`read api request timed out for ${path}`);
    }
    throw error;
  } finally {
    window.clearTimeout(timeoutId);
  }
  const payload = (await response.json()) as ApiEnvelope<T>;
  if (!response.ok || payload.errors.length > 0) {
    const message = payload.errors[0]?.message ?? `read api request failed for ${path}: ${response.status}`;
    throw new Error(message);
  }
  return payload.data;
}

export function fetchReadSnapshot(): Promise<SnapshotResponse> {
  return fetchEnvelope<SnapshotResponse>("/api/v1/read/snapshot");
}

export function fetchReadMetrics(runId?: string, limit = 24): Promise<MetricsResponse> {
  return fetchEnvelope<MetricsResponse>("/api/v1/read/metrics", {
    run_id: runId,
    limit,
  });
}

export function fetchReadEvents(runId?: string, limit = 12, kind?: string): Promise<EventsResponse> {
  return fetchEnvelope<EventsResponse>("/api/v1/read/events", {
    run_id: runId,
    kind,
    limit,
  });
}

export function fetchReadRuns(): Promise<RunListPayload> {
  return fetchEnvelope<RunListPayload>("/api/v1/read/runs");
}

export function fetchReadReplay(runId: string, limit = 250): Promise<ReplayPayload> {
  return fetchEnvelope<ReplayPayload>("/api/v1/read/replay", {
    run_id: runId,
    limit,
  });
}
