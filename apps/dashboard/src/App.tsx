import { useEffect, useMemo, useRef, useState } from "react";

import type {
  MetricsResponse,
  MissionStatusPayload,
  PerceptionHeartbeatPayload,
  RunSummary,
  SafetyStatusPayload,
  SnapshotResponse,
  StoredEnvelope,
  TrackedObjectPayload,
  VehicleStatePayload,
} from "./types";

import { EventsTable } from "./components/EventsTable";
import { MetricsPanel } from "./components/MetricsPanel";
import { ReplayPanel } from "./components/ReplayPanel";
import { StatusCard } from "./components/StatusCard";
import {
  connectTelemetryStream,
  fetchEvents,
  fetchMetrics,
  fetchReplay,
  fetchRuns,
  fetchSnapshot,
} from "./lib/api";

function nsToDate(stampNs?: number): string {
  if (!stampNs) {
    return "n/a";
  }
  return new Date(Math.floor(stampNs / 1_000_000)).toLocaleString();
}

function payloadFor<T extends Record<string, unknown>>(
  snapshot: SnapshotResponse | null,
  kind: string,
): Partial<T> {
  return (snapshot?.latest_by_kind[kind]?.payload ?? {}) as Partial<T>;
}

function upsertRunSummary(runs: RunSummary[], event: StoredEnvelope): RunSummary[] {
  const next = [...runs];
  const index = next.findIndex((entry) => entry.run_id === event.run_id);
  if (index === -1) {
    next.push({
      run_id: event.run_id,
      event_count: 1,
      last_kind: event.kind,
      last_stamp_ns: event.stamp_ns,
    });
  } else {
    const current = next[index];
    next[index] = {
      ...current,
      event_count: current.event_count + 1,
      last_kind: event.kind,
      last_stamp_ns: event.stamp_ns,
    };
  }
  next.sort((left, right) => (right.last_stamp_ns ?? 0) - (left.last_stamp_ns ?? 0));
  return next;
}

export function App() {
  const [snapshot, setSnapshot] = useState<SnapshotResponse | null>(null);
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [recentEvents, setRecentEvents] = useState<StoredEnvelope[]>([]);
  const [replayEvents, setReplayEvents] = useState<StoredEnvelope[]>([]);
  const [selectedReplayIndex, setSelectedReplayIndex] = useState(0);
  const [selectedRunId, setSelectedRunId] = useState<string>("");
  const [error, setError] = useState<string>("");
  const selectedRunRef = useRef<string>("");

  const currentRunId = selectedRunId || snapshot?.current_run_id || runs[0]?.run_id || "";

  useEffect(() => {
    selectedRunRef.current = currentRunId;
  }, [currentRunId]);

  useEffect(() => {
    let cancelled = false;
    let socket: WebSocket | null = null;

    async function bootstrap() {
      try {
        const [nextSnapshot, nextMetrics, nextRuns] = await Promise.all([
          fetchSnapshot(),
          fetchMetrics(),
          fetchRuns(),
        ]);
        if (cancelled) {
          return;
        }

        const nextRunId = nextSnapshot.current_run_id || nextRuns[0]?.run_id || "";
        const [nextEvents, nextReplay] = await Promise.all([
          fetchEvents(12, nextRunId || undefined),
          nextRunId ? fetchReplay(nextRunId) : Promise.resolve([]),
        ]);
        if (cancelled) {
          return;
        }

        setSnapshot(nextSnapshot);
        setMetrics(nextMetrics);
        setRuns(nextRuns);
        setSelectedRunId(nextRunId);
        setRecentEvents(nextEvents);
        setReplayEvents(nextReplay);
        setSelectedReplayIndex(Math.max(nextReplay.length - 1, 0));

        socket = connectTelemetryStream((message) => {
          if (cancelled) {
            return;
          }

          if (message.type === "snapshot") {
            setSnapshot(message.snapshot);
            const snapshotRunId = message.snapshot.current_run_id || selectedRunRef.current;
            if (snapshotRunId && !selectedRunRef.current) {
              setSelectedRunId(snapshotRunId);
            }
            return;
          }

          const event = message.event;
          setSnapshot((current) => ({
            current_run_id: event.run_id,
            latest_by_kind: {
              ...(current?.latest_by_kind ?? {}),
              [event.kind]: event,
            },
          }));
          setMetrics((current) => {
            const base: MetricsResponse = current ?? {
              total_events: 0,
              counts_by_kind: {},
              counts_by_run: {},
            };
            return {
              total_events: base.total_events + 1,
              counts_by_kind: {
                ...base.counts_by_kind,
                [event.kind]: (base.counts_by_kind[event.kind] ?? 0) + 1,
              },
              counts_by_run: {
                ...base.counts_by_run,
                [event.run_id]: (base.counts_by_run[event.run_id] ?? 0) + 1,
              },
            };
          });
          setRuns((current) => upsertRunSummary(current, event));

          if (!selectedRunRef.current) {
            setSelectedRunId(event.run_id);
          }

          if (!selectedRunRef.current || selectedRunRef.current === event.run_id) {
            setRecentEvents((current) => [...current, event].slice(-12));
            setReplayEvents((current) => [...current, event].slice(-250));
          }
        });
      } catch (nextError) {
        if (!cancelled) {
          setError(nextError instanceof Error ? nextError.message : String(nextError));
        }
      }
    }

    void bootstrap();

    return () => {
      cancelled = true;
      socket?.close();
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadRunArtifacts() {
      if (!currentRunId) {
        setRecentEvents([]);
        setReplayEvents([]);
        setSelectedReplayIndex(0);
        return;
      }
      try {
        const [nextEvents, nextReplay] = await Promise.all([
          fetchEvents(12, currentRunId),
          fetchReplay(currentRunId),
        ]);
        if (cancelled) {
          return;
        }
        setRecentEvents(nextEvents);
        setReplayEvents(nextReplay);
        setSelectedReplayIndex(Math.max(nextReplay.length - 1, 0));
      } catch (nextError) {
        if (!cancelled) {
          setError(nextError instanceof Error ? nextError.message : String(nextError));
        }
      }
    }

    void loadRunArtifacts();

    return () => {
      cancelled = true;
    };
  }, [currentRunId]);

  const vehicleState = useMemo(
    () => payloadFor<VehicleStatePayload>(snapshot, "vehicle_state"),
    [snapshot],
  );
  const missionStatus = useMemo(
    () => payloadFor<MissionStatusPayload>(snapshot, "mission_status"),
    [snapshot],
  );
  const safetyStatus = useMemo(
    () => payloadFor<SafetyStatusPayload>(snapshot, "safety_status"),
    [snapshot],
  );
  const trackedObject = useMemo(
    () => payloadFor<TrackedObjectPayload>(snapshot, "tracked_object"),
    [snapshot],
  );
  const perceptionHeartbeat = useMemo(
    () => payloadFor<PerceptionHeartbeatPayload>(snapshot, "perception_heartbeat"),
    [snapshot],
  );

  const replayTitle = useMemo(() => {
    if (!currentRunId) {
      return "No active run";
    }
    const summary = runs.find((entry) => entry.run_id === currentRunId) ?? null;
    return `${currentRunId} • last envelope ${nsToDate(summary?.last_stamp_ns ?? undefined)}`;
  }, [currentRunId, runs]);

  return (
    <main className="dashboard-shell">
      <section className="hero">
        <div className="hero__copy">
          <p className="hero__eyebrow">Simulation Operations</p>
          <h1>Operations dashboard</h1>
          <p className="hero__summary">
            Live operational state, persisted event history, metrics and replay for the simulation stack.
          </p>
        </div>
        <div className="hero__meta">
          <div className="hero__meta-label">Current run</div>
          <div className="hero__meta-value">{replayTitle}</div>
          <label className="hero__meta-label" htmlFor="run-selector">
            Replay source
          </label>
          <select
            id="run-selector"
            className="hero__select"
            value={currentRunId}
            onChange={(event) => setSelectedRunId(event.target.value)}
          >
            {runs.length === 0 ? <option value="">No runs available</option> : null}
            {runs.map((run) => (
              <option key={run.run_id} value={run.run_id}>
                {run.run_id} ({run.event_count})
              </option>
            ))}
          </select>
          <p className="hero__meta-note">Presentation only. Mission and safety decisions stay inside ROS 2.</p>
        </div>
      </section>

      {error ? <div className="dashboard-error">{error}</div> : null}

      <section className="status-grid">
        <StatusCard title="Vehicle" accent="#ffb347">
          <dl>
            <dt>Connected</dt>
            <dd>{String(vehicleState.connected ?? false)}</dd>
            <dt>Armed</dt>
            <dd>{String(vehicleState.armed ?? false)}</dd>
            <dt>Altitude</dt>
            <dd>{vehicleState.relative_altitude_m?.toFixed(2) ?? "0.00"} m</dd>
            <dt>Failsafe</dt>
            <dd>{String(vehicleState.failsafe ?? false)}</dd>
          </dl>
        </StatusCard>

        <StatusCard title="Mission" accent="#4dd0e1">
          <dl>
            <dt>Phase</dt>
            <dd>{missionStatus.phase ?? "idle"}</dd>
            <dt>Detail</dt>
            <dd>{missionStatus.detail ?? "n/a"}</dd>
            <dt>Waypoint</dt>
            <dd>
              {missionStatus.current_waypoint_index ?? 0}/{missionStatus.total_waypoints ?? 0}
            </dd>
            <dt>Terminal</dt>
            <dd>{String(missionStatus.terminal ?? false)}</dd>
          </dl>
        </StatusCard>

        <StatusCard title="Safety" accent="#ff6f91">
          <dl>
            <dt>Active</dt>
            <dd>{String(safetyStatus.active ?? false)}</dd>
            <dt>Rule</dt>
            <dd>{safetyStatus.rule ?? "none"}</dd>
            <dt>Action</dt>
            <dd>{safetyStatus.action ?? "none"}</dd>
            <dt>Trigger count</dt>
            <dd>{safetyStatus.trigger_count ?? 0}</dd>
          </dl>
        </StatusCard>

        <StatusCard title="Perception" accent="#8bc34a">
          <dl>
            <dt>Tracked</dt>
            <dd>{String(trackedObject.tracked ?? false)}</dd>
            <dt>Track label</dt>
            <dd>{trackedObject.label ?? "n/a"}</dd>
            <dt>Heartbeat healthy</dt>
            <dd>{String(perceptionHeartbeat.healthy ?? false)}</dd>
            <dt>Latency</dt>
            <dd>{perceptionHeartbeat.pipeline_latency_s?.toFixed(3) ?? "0.000"} s</dd>
          </dl>
        </StatusCard>
      </section>

      <section className="lower-grid">
        <EventsTable events={recentEvents} />
        <ReplayPanel
          events={replayEvents}
          selectedIndex={selectedReplayIndex}
          onSelectedIndexChange={setSelectedReplayIndex}
        />
      </section>

      <section className="lower-grid">
        <MetricsPanel
          metrics={
            metrics ?? {
              total_events: 0,
              counts_by_kind: {},
              counts_by_run: {},
            }
          }
        />

        <section className="event-feed">
          <div className="event-feed__header">
            <h2>Run inventory</h2>
            <span>{runs.length} persisted runs</span>
          </div>
          <ul>
            {runs.map((run) => (
              <li key={run.run_id}>
                <strong>{run.run_id}</strong>
                <span>
                  events={run.event_count} last_kind={run.last_kind ?? "n/a"}
                </span>
                <code>{nsToDate(run.last_stamp_ns ?? undefined)}</code>
              </li>
            ))}
          </ul>
        </section>
      </section>
    </main>
  );
}

export default App;
