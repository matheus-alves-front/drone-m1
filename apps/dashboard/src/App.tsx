import { useEffect, useMemo, useRef, useState } from "react";

import { EventsTable } from "./components/EventsTable";
import { MetricsPanel } from "./components/MetricsPanel";
import { ReplayPanel } from "./components/ReplayPanel";
import { StatusCard } from "./components/StatusCard";
import {
  fetchCapabilities,
  fetchControlStatus,
  fetchMissionStatus,
  fetchPerceptionStatus,
  fetchPerceptionStreamStatus,
  fetchReadEvents,
  fetchReadMetrics,
  fetchReadReplay,
  fetchReadRuns,
  fetchReadSnapshot,
  fetchSafetyStatus,
  fetchScenarioStatus,
  fetchScenarios,
  invokeMissionAbort,
  invokeMissionReset,
  invokeMissionStart,
  invokeSafetyClearFault,
  invokeSafetyInjectFault,
  invokeScenarioCancel,
  invokeScenarioRun,
  invokeSimulationRestart,
  invokeSimulationStart,
  invokeSimulationStop,
  invokeVehicleCommand,
} from "./lib/api";
import type {
  ActionResultPayload,
  CapabilityDefinition,
  ControlStatusPayload,
  MetricRecord,
  MissionDefinitionPayload,
  PerceptionHeartbeatPayload,
  PerceptionStatusPayload,
  PerceptionStreamStatusPayload,
  ReplayPayload,
  RunListPayload,
  SafetySurfacePayload,
  ScenarioEntry,
  ScenarioStatusPayload,
  SnapshotResponse,
  StoredEnvelope,
  TrackedObjectPayload,
  VehicleStatePayload,
} from "./types";

const NAV_ITEMS = [
  { id: "overview", label: "Overview" },
  { id: "control", label: "Control" },
  { id: "mission", label: "Mission" },
  { id: "safety", label: "Safety" },
  { id: "perception", label: "Perception" },
  { id: "runs", label: "Runs / Replay" },
  { id: "settings", label: "Settings / Environment" },
] as const;

const DEFAULT_SCENARIO = "takeoff_land";
const DEFAULT_MISSION = "patrol_basic";

type PageId = (typeof NAV_ITEMS)[number]["id"];
type SimulationMode = "headless" | "visual";

function nsToDate(stampNs?: number | null): string {
  if (!stampNs) {
    return "n/a";
  }
  return new Date(Math.floor(stampNs / 1_000_000)).toLocaleString();
}

function isoToDate(value?: string | null): string {
  if (!value) {
    return "n/a";
  }
  return new Date(value).toLocaleString();
}

function boolLabel(value?: boolean): string {
  return value ? "yes" : "no";
}

function payloadFor<T extends Record<string, unknown>>(snapshot: SnapshotResponse | null, key: keyof SnapshotResponse): Partial<T> {
  const directValue = snapshot?.[key];
  if (directValue && typeof directValue === "object" && !Array.isArray(directValue)) {
    return directValue as Partial<T>;
  }
  return (snapshot?.latest_by_kind[String(key)]?.payload ?? {}) as Partial<T>;
}

function capabilityCounts(capabilities: CapabilityDefinition[]) {
  return capabilities.reduce(
    (counts, capability) => {
      counts.total += 1;
      counts[capability.status] = (counts[capability.status] ?? 0) + 1;
      return counts;
    },
    { total: 0, available: 0, experimental: 0, unavailable: 0 } as Record<string, number>,
  );
}

function confirmAction(message: string): boolean {
  if (typeof window === "undefined" || typeof window.confirm !== "function") {
    return true;
  }
  return window.confirm(message);
}

function capabilityAvailable(capabilities: CapabilityDefinition[], capabilityName: string): boolean {
  return capabilities.some((capability) => capability.capability_name === capabilityName && capability.status === "available");
}

function actionDisabledBySession(sessionStatus?: string | null): boolean {
  return sessionStatus !== "active" && sessionStatus !== "degraded";
}

export function App() {
  const [page, setPage] = useState<PageId>("overview");
  const [controlStatus, setControlStatus] = useState<ControlStatusPayload | null>(null);
  const [capabilities, setCapabilities] = useState<CapabilityDefinition[]>([]);
  const [scenarios, setScenarios] = useState<ScenarioEntry[]>([]);
  const [scenarioStatus, setScenarioStatus] = useState<ScenarioStatusPayload | null>(null);
  const [missionStatus, setMissionStatus] = useState<MissionDefinitionPayload | null>(null);
  const [safetyStatus, setSafetyStatus] = useState<SafetySurfacePayload | null>(null);
  const [perceptionStatus, setPerceptionStatus] = useState<PerceptionStatusPayload | null>(null);
  const [perceptionStreamStatus, setPerceptionStreamStatus] = useState<PerceptionStreamStatusPayload | null>(null);
  const [snapshot, setSnapshot] = useState<SnapshotResponse | null>(null);
  const [runs, setRuns] = useState<RunListPayload | null>(null);
  const [metrics, setMetrics] = useState<MetricRecord[]>([]);
  const [recentEvents, setRecentEvents] = useState<StoredEnvelope[]>([]);
  const [replay, setReplay] = useState<ReplayPayload | null>(null);
  const [selectedScenario, setSelectedScenario] = useState(DEFAULT_SCENARIO);
  const [selectedRunId, setSelectedRunId] = useState("");
  const [selectedReplayIndex, setSelectedReplayIndex] = useState(0);
  const [actionMode, setActionMode] = useState<SimulationMode>("headless");
  const [missionReason, setMissionReason] = useState("");
  const [faultType, setFaultType] = useState("gps_loss");
  const [faultDetail, setFaultDetail] = useState("operator test");
  const [faultValue, setFaultValue] = useState("1.0");
  const [gotoLatitude, setGotoLatitude] = useState("");
  const [gotoLongitude, setGotoLongitude] = useState("");
  const [gotoRelativeAltitude, setGotoRelativeAltitude] = useState("5");
  const [lastAction, setLastAction] = useState<ActionResultPayload | null>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const selectedRunRef = useRef("");
  const selectedScenarioRef = useRef(DEFAULT_SCENARIO);
  const refreshRef = useRef<() => Promise<void>>(async () => undefined);

  useEffect(() => {
    selectedRunRef.current = selectedRunId;
  }, [selectedRunId]);

  useEffect(() => {
    selectedScenarioRef.current = selectedScenario;
  }, [selectedScenario]);

  refreshRef.current = async () => {
    try {
      const [nextControlStatus, nextCapabilities, nextScenarios, nextMissionStatus, nextSafetyStatus, nextPerceptionStatus, nextPerceptionStreamStatus, nextSnapshot, nextRuns] =
        await Promise.all([
          fetchControlStatus(),
          fetchCapabilities(),
          fetchScenarios(),
          fetchMissionStatus(),
          fetchSafetyStatus(),
          fetchPerceptionStatus(),
          fetchPerceptionStreamStatus(),
          fetchReadSnapshot(),
          fetchReadRuns(),
        ]);

      const nextScenarioName =
        selectedScenarioRef.current ||
        nextScenarios.find((scenario) => scenario.control_plane_status === "available")?.scenario_name ||
        nextScenarios[0]?.scenario_name ||
        DEFAULT_SCENARIO;
      const nextScenarioStatus = await fetchScenarioStatus(nextScenarioName);

      const nextRunId =
        selectedRunRef.current ||
        nextScenarioStatus.last_run_id ||
        nextRuns.current_telemetry_run_id ||
        nextSnapshot.current_run_id ||
        nextSnapshot.run_id ||
        nextRuns.runs[0]?.run_id ||
        "";

      const [nextMetrics, nextEvents, nextReplay] = nextRunId
        ? await Promise.all([
            fetchReadMetrics(nextRunId, 24),
            fetchReadEvents(nextRunId, 24),
            fetchReadReplay(nextRunId, 250),
          ])
        : [
            { run_id: null, session_id: null, metrics: [], source: "operator_ui" },
            { run_id: null, session_id: null, events: [], source: "operator_ui" },
            null,
          ];

      setControlStatus(nextControlStatus);
      setCapabilities(nextCapabilities);
      setScenarios(nextScenarios);
      setSelectedScenario(nextScenarioName);
      setScenarioStatus(nextScenarioStatus);
      setMissionStatus(nextMissionStatus);
      setSafetyStatus(nextSafetyStatus);
      setPerceptionStatus(nextPerceptionStatus);
      setPerceptionStreamStatus(nextPerceptionStreamStatus);
      setSnapshot(nextSnapshot);
      setRuns(nextRuns);
      setSelectedRunId(nextRunId);
      setMetrics(nextMetrics.metrics);
      setRecentEvents(nextEvents.events);
      setReplay(nextReplay);
      setSelectedReplayIndex(Math.max((nextReplay?.events.length ?? 1) - 1, 0));
      setActionMode(nextControlStatus.session.mode === "visual" ? "visual" : "headless");
      setError("");
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : String(nextError));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refreshRef.current();
    const intervalId = window.setInterval(() => {
      void refreshRef.current();
    }, 4000);
    return () => window.clearInterval(intervalId);
  }, []);

  useEffect(() => {
    if (!selectedScenario) {
      setScenarioStatus(null);
      return;
    }

    let cancelled = false;
    void fetchScenarioStatus(selectedScenario)
      .then((nextScenarioStatus) => {
        if (!cancelled) {
          setScenarioStatus(nextScenarioStatus);
        }
      })
      .catch((nextError) => {
        if (!cancelled) {
          setError(nextError instanceof Error ? nextError.message : String(nextError));
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedScenario]);

  useEffect(() => {
    if (!selectedRunId) {
      setMetrics([]);
      setRecentEvents([]);
      setReplay(null);
      setSelectedReplayIndex(0);
      return;
    }

    let cancelled = false;
    void Promise.all([
      fetchReadMetrics(selectedRunId, 24),
      fetchReadEvents(selectedRunId, 24),
      fetchReadReplay(selectedRunId, 250),
    ])
      .then(([nextMetrics, nextEvents, nextReplay]) => {
        if (cancelled) {
          return;
        }
        setMetrics(nextMetrics.metrics);
        setRecentEvents(nextEvents.events);
        setReplay(nextReplay);
        setSelectedReplayIndex(Math.max(nextReplay.events.length - 1, 0));
      })
      .catch((nextError) => {
        if (!cancelled) {
          setError(nextError instanceof Error ? nextError.message : String(nextError));
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedRunId]);

  async function executeAction(
    actionKey: string,
    runAction: () => Promise<ActionResultPayload>,
    confirmMessage?: string,
  ) {
    if (confirmMessage && !confirmAction(confirmMessage)) {
      return;
    }

    setBusyAction(actionKey);
    setError("");
    try {
      const result = await runAction();
      setLastAction(result);
      await refreshRef.current();
      if (result.run_id) {
        setSelectedRunId(result.run_id);
      }
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : String(nextError));
    } finally {
      setBusyAction(null);
    }
  }

  const vehicleState = useMemo(() => payloadFor<VehicleStatePayload>(snapshot, "vehicle_state"), [snapshot]);
  const missionReadModel = useMemo(() => payloadFor<Record<string, unknown>>(snapshot, "mission_status"), [snapshot]);
  const trackedObject = useMemo(() => payloadFor<TrackedObjectPayload>(snapshot, "tracked_object"), [snapshot]);
  const perceptionHeartbeat = useMemo(
    () => payloadFor<PerceptionHeartbeatPayload>(snapshot, "perception_heartbeat"),
    [snapshot],
  );
  const capabilitySummary = useMemo(() => capabilityCounts(capabilities), [capabilities]);
  const session = controlStatus?.session ?? null;
  const currentTelemetryRunId = runs?.current_telemetry_run_id ?? snapshot?.current_run_id ?? snapshot?.run_id ?? null;
  const activeRun = controlStatus?.runs.active_run ?? null;
  const selectedRun = runs?.runs.find((item) => item.run_id === selectedRunId) ?? null;
  const perceptionEvent = snapshot?.perception_event ?? snapshot?.latest_by_kind.perception_event?.payload ?? {};
  const missionIsTerminal =
    missionStatus?.status === "completed" || missionStatus?.status === "aborted" || missionStatus?.status === "failed";

  const currentRunLabel = useMemo(() => {
    if (!selectedRunId) {
      return "No run selected";
    }
    return `${selectedRunId} • ${selectedRun?.run_kind ?? "read_model"} • ${selectedRun?.status ?? "n/a"}`;
  }, [selectedRun, selectedRunId]);

  return (
    <main className="operator-shell">
      <section className="console-hero">
        <div className="console-hero__copy">
          <p className="console-hero__eyebrow">Drone Control Platform</p>
          <h1>Mark 1 Operator Console</h1>
          <p className="console-hero__summary">
            Unified shell for command, auditability, perception and run tracking without pushing mission, safety or runtime
            logic into the frontend.
          </p>
        </div>
        <div className="console-hero__meta">
          <div className="console-hero__pill">
            {controlStatus?.service.phase ?? "R10"} / {controlStatus?.service.mode ?? "operator-console"}
          </div>
          <div className="console-hero__meta-block">
            <span>Session</span>
            <strong>{session?.session_id ?? "n/a"}</strong>
          </div>
          <div className="console-hero__meta-block">
            <span>Session state</span>
            <strong>{session?.status ?? "loading"}</strong>
          </div>
          <div className="console-hero__meta-block">
            <span>Telemetry run</span>
            <strong>{currentTelemetryRunId ?? "n/a"}</strong>
          </div>
        </div>
      </section>

      <nav className="console-nav" aria-label="Operator console sections">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            className={item.id === page ? "console-nav__item console-nav__item--active" : "console-nav__item"}
            type="button"
            onClick={() => setPage(item.id)}
          >
            {item.label}
          </button>
        ))}
      </nav>

      {error ? <div className="dashboard-error">{error}</div> : null}
      {lastAction ? (
        <div className="action-banner" role="status">
          <strong>Last action</strong>
          <span>{lastAction.message}</span>
          <code>{lastAction.run_id ?? "no run id"}</code>
          {lastAction.run_id ? (
            <button type="button" className="action-button action-button--secondary" onClick={() => setPage("runs")}>
              Open run
            </button>
          ) : null}
        </div>
      ) : null}
      {loading ? <div className="dashboard-muted">Loading operator shell…</div> : null}

      {page === "overview" ? (
        <>
          <section className="status-grid">
            <StatusCard title="Service" accent="#1db6b2">
              <dl>
                <dt>Phase</dt>
                <dd>{controlStatus?.service.phase ?? "n/a"}</dd>
                <dt>Mode</dt>
                <dd>{controlStatus?.service.mode ?? "n/a"}</dd>
                <dt>Action catalog</dt>
                <dd>{controlStatus?.catalog.action_count ?? 0}</dd>
                <dt>Capabilities</dt>
                <dd>{controlStatus?.catalog.capability_count ?? 0}</dd>
              </dl>
            </StatusCard>

            <StatusCard title="Session" accent="#f3b24f">
              <dl>
                <dt>Status</dt>
                <dd>{session?.status ?? "n/a"}</dd>
                <dt>Mode</dt>
                <dd>{session?.mode ?? "n/a"}</dd>
                <dt>Started</dt>
                <dd>{isoToDate(session?.started_at)}</dd>
                <dt>Active run</dt>
                <dd>{activeRun?.name ?? "none"}</dd>
              </dl>
            </StatusCard>

            <StatusCard title="Vehicle" accent="#ff8b5d">
              <dl>
                <dt>Connected</dt>
                <dd>{boolLabel(vehicleState.connected)}</dd>
                <dt>Armed</dt>
                <dd>{boolLabel(vehicleState.armed)}</dd>
                <dt>Flight mode</dt>
                <dd>{vehicleState.nav_state ?? "n/a"}</dd>
                <dt>Altitude</dt>
                <dd>{typeof vehicleState.relative_altitude_m === "number" ? `${vehicleState.relative_altitude_m.toFixed(2)} m` : "n/a"}</dd>
              </dl>
            </StatusCard>

            <StatusCard title="Mission" accent="#58c5ff">
              <dl>
                <dt>Status</dt>
                <dd>{missionStatus?.status ?? "n/a"}</dd>
                <dt>Detail</dt>
                <dd>{String(missionStatus?.constraints.detail ?? missionReadModel.detail ?? "n/a")}</dd>
                <dt>Waypoint</dt>
                <dd>
                  {String(missionStatus?.constraints.current_waypoint_index ?? missionReadModel.current_waypoint_index ?? 0)}/
                  {String(missionStatus?.constraints.total_waypoints ?? missionReadModel.total_waypoints ?? 0)}
                </dd>
                <dt>Last command</dt>
                <dd>{String(missionStatus?.constraints.last_command ?? missionReadModel.last_command ?? "n/a")}</dd>
              </dl>
            </StatusCard>

            <StatusCard title="Safety" accent="#ff6f91">
              <dl>
                <dt>State</dt>
                <dd>{safetyStatus?.state ?? "n/a"}</dd>
                <dt>Faults</dt>
                <dd>{safetyStatus?.active_faults.length ?? 0}</dd>
                <dt>Rule</dt>
                <dd>{String((snapshot?.safety_status.rule as string | undefined) ?? "n/a")}</dd>
                <dt>Summary</dt>
                <dd>{safetyStatus?.summary ?? "n/a"}</dd>
              </dl>
            </StatusCard>

            <StatusCard title="Perception" accent="#7fd36b">
              <dl>
                <dt>Tracked</dt>
                <dd>{boolLabel(trackedObject.tracked)}</dd>
                <dt>Label</dt>
                <dd>{trackedObject.label ?? "n/a"}</dd>
                <dt>Healthy</dt>
                <dd>{boolLabel(perceptionHeartbeat.healthy)}</dd>
                <dt>Latency</dt>
                <dd>
                  {typeof perceptionHeartbeat.pipeline_latency_s === "number"
                    ? `${perceptionHeartbeat.pipeline_latency_s.toFixed(3)} s`
                    : "n/a"}
                </dd>
              </dl>
            </StatusCard>
          </section>

          <section className="overview-grid">
            <section className="panel-card">
              <div className="panel-card__header">
                <h2>Capability surface</h2>
                <span>{capabilitySummary.total} total</span>
              </div>
              <div className="pill-row">
                <span className="surface-pill surface-pill--ok">{capabilitySummary.available} available</span>
                <span className="surface-pill surface-pill--warn">{capabilitySummary.experimental} experimental</span>
                <span className="surface-pill">{capabilitySummary.unavailable} unavailable</span>
              </div>
              <ul className="summary-list">
                {capabilities.slice(0, 6).map((capability) => (
                  <li key={capability.capability_name}>
                    <strong>{capability.capability_name}</strong>
                    <span>{capability.status}</span>
                  </li>
                ))}
              </ul>
            </section>

            <section className="panel-card">
              <div className="panel-card__header">
                <h2>Scenario surface</h2>
                <span>{scenarios.length} registered</span>
              </div>
              <ul className="summary-list">
                {scenarios.map((scenario) => (
                  <li key={scenario.scenario_name}>
                    <strong>{scenario.scenario_name}</strong>
                    <span>{scenario.control_plane_status}</span>
                    <code>{scenario.phase_hint}</code>
                  </li>
                ))}
              </ul>
            </section>
          </section>
        </>
      ) : null}

      {page === "control" ? (
        <section className="console-section-grid">
          <section className="panel-card panel-card--strong">
            <div className="panel-card__header">
              <h2>Session control</h2>
              <span>{session?.environment.environment_name ?? "environment pending"}</span>
            </div>
            <p className="panel-card__summary">
              The UI emits product actions only. Runtime ownership stays inside the Control API and its adapters.
            </p>
            <label className="field">
              <span>Simulation mode</span>
              <select value={actionMode} onChange={(event) => setActionMode(event.target.value as SimulationMode)}>
                <option value="headless">headless</option>
                <option value="visual">visual</option>
              </select>
            </label>
            <div className="action-row">
              <button
                type="button"
                className="action-button"
                disabled={busyAction !== null || session?.status === "active"}
                onClick={() => void executeAction("simulation.start", () => invokeSimulationStart(actionMode))}
              >
                {busyAction === "simulation.start" ? "Starting…" : "Start simulation"}
              </button>
              <button
                type="button"
                className="action-button action-button--secondary"
                disabled={busyAction !== null || !session || session.status === "idle" || session.status === "stopped"}
                onClick={() =>
                  void executeAction(
                    "simulation.restart",
                    () => invokeSimulationRestart(actionMode),
                    "Restart the simulation session with the selected mode?",
                  )
                }
              >
                {busyAction === "simulation.restart" ? "Restarting…" : "Restart simulation"}
              </button>
              <button
                type="button"
                className="action-button action-button--danger"
                disabled={busyAction !== null || !session || session.status === "idle" || session.status === "stopped"}
                onClick={() =>
                  void executeAction("simulation.stop", () => invokeSimulationStop(), "Stop the current simulation session?")
                }
              >
                {busyAction === "simulation.stop" ? "Stopping…" : "Stop simulation"}
              </button>
            </div>
            <dl className="detail-grid">
              <dt>Session id</dt>
              <dd>{session?.session_id ?? "n/a"}</dd>
              <dt>Simulator</dt>
              <dd>{session?.environment.simulator_family ?? "n/a"}</dd>
              <dt>Vehicle profile</dt>
              <dd>{session?.environment.vehicle_profile ?? "n/a"}</dd>
              <dt>Baseline</dt>
              <dd>{session?.environment.baseline ?? "n/a"}</dd>
            </dl>
          </section>

          <section className="panel-card">
            <div className="panel-card__header">
              <h2>Scenario console</h2>
              <span>{selectedScenario}</span>
            </div>
            <label className="field">
              <span>Scenario</span>
              <select value={selectedScenario} onChange={(event) => setSelectedScenario(event.target.value)}>
                {scenarios.map((scenario) => (
                  <option key={scenario.scenario_name} value={scenario.scenario_name}>
                    {scenario.scenario_name} • {scenario.control_plane_status}
                  </option>
                ))}
              </select>
            </label>
            <div className="action-row">
              <button
                type="button"
                className="action-button"
                disabled={
                  busyAction !== null ||
                  actionDisabledBySession(session?.status) ||
                  !scenarioStatus ||
                  scenarios.find((scenario) => scenario.scenario_name === selectedScenario)?.control_plane_status !== "available"
                }
                onClick={() => void executeAction(`scenario.run:${selectedScenario}`, () => invokeScenarioRun(selectedScenario))}
              >
                {busyAction === `scenario.run:${selectedScenario}` ? "Launching…" : "Run scenario"}
              </button>
              <button
                type="button"
                className="action-button action-button--danger"
                disabled={busyAction !== null || !scenarioStatus?.active_run_id}
                onClick={() =>
                  void executeAction(
                    `scenario.cancel:${selectedScenario}`,
                    () => invokeScenarioCancel(selectedScenario),
                    `Cancel the active ${selectedScenario} run?`,
                  )
                }
              >
                {busyAction === `scenario.cancel:${selectedScenario}` ? "Cancelling…" : "Cancel scenario"}
              </button>
            </div>
            <dl className="detail-grid">
              <dt>Status</dt>
              <dd>{scenarioStatus?.status ?? "n/a"}</dd>
              <dt>Active run</dt>
              <dd>{scenarioStatus?.active_run_id ?? "none"}</dd>
              <dt>Last run</dt>
              <dd>{scenarioStatus?.last_run_id ?? "none"}</dd>
              <dt>Summary</dt>
              <dd>{scenarioStatus?.summary ?? "n/a"}</dd>
            </dl>
          </section>

          <section className="panel-card">
            <div className="panel-card__header">
              <h2>Vehicle console</h2>
              <span>{vehicleState.nav_state ?? "n/a"}</span>
            </div>
            <div className="action-row">
              <button
                type="button"
                className="action-button"
                disabled={busyAction !== null || actionDisabledBySession(session?.status)}
                onClick={() => void executeAction("vehicle.arm", () => invokeVehicleCommand("arm"))}
              >
                Arm
              </button>
              <button
                type="button"
                className="action-button action-button--secondary"
                disabled={busyAction !== null || actionDisabledBySession(session?.status)}
                onClick={() => void executeAction("vehicle.disarm", () => invokeVehicleCommand("disarm"))}
              >
                Disarm
              </button>
              <button
                type="button"
                className="action-button"
                disabled={busyAction !== null || actionDisabledBySession(session?.status)}
                onClick={() => void executeAction("vehicle.takeoff", () => invokeVehicleCommand("takeoff"))}
              >
                Takeoff
              </button>
              <button
                type="button"
                className="action-button action-button--danger"
                disabled={busyAction !== null || actionDisabledBySession(session?.status)}
                onClick={() =>
                  void executeAction("vehicle.land", () => invokeVehicleCommand("land"), "Send a land command through the control plane?")
                }
              >
                Land
              </button>
              <button
                type="button"
                className="action-button action-button--danger"
                disabled={busyAction !== null || actionDisabledBySession(session?.status)}
                onClick={() =>
                  void executeAction(
                    "vehicle.return_to_home",
                    () => invokeVehicleCommand("return_to_home"),
                    "Command the vehicle to return to home?",
                  )
                }
              >
                Return to home
              </button>
            </div>
            <div className="field-grid">
              <label className="field">
                <span>Latitude</span>
                <input value={gotoLatitude} onChange={(event) => setGotoLatitude(event.target.value)} placeholder="-23.5505" />
              </label>
              <label className="field">
                <span>Longitude</span>
                <input value={gotoLongitude} onChange={(event) => setGotoLongitude(event.target.value)} placeholder="-46.6333" />
              </label>
              <label className="field">
                <span>Relative altitude m</span>
                <input
                  value={gotoRelativeAltitude}
                  onChange={(event) => setGotoRelativeAltitude(event.target.value)}
                  placeholder="5"
                />
              </label>
            </div>
            <button
              type="button"
              className="action-button action-button--secondary"
              disabled={busyAction !== null || actionDisabledBySession(session?.status) || !gotoLatitude || !gotoLongitude}
              onClick={() =>
                void executeAction("vehicle.goto", () =>
                  invokeVehicleCommand("goto", {
                    latitude_deg: Number(gotoLatitude),
                    longitude_deg: Number(gotoLongitude),
                    relative_altitude_m: Number(gotoRelativeAltitude),
                  }),
                )
              }
            >
              Send goto
            </button>
          </section>
        </section>
      ) : null}

      {page === "mission" ? (
        <section className="console-section-grid">
          <section className="panel-card panel-card--strong">
            <div className="panel-card__header">
              <h2>Mission surface</h2>
              <span>{missionStatus?.mission_id ?? DEFAULT_MISSION}</span>
            </div>
            <div className="action-row">
              <button
                type="button"
                className="action-button"
                disabled={busyAction !== null || actionDisabledBySession(session?.status) || missionStatus?.status !== "idle"}
                onClick={() => void executeAction("mission.start", () => invokeMissionStart(DEFAULT_MISSION))}
              >
                Start mission
              </button>
              <button
                type="button"
                className="action-button action-button--danger"
                disabled={busyAction !== null || missionStatus?.status === "idle" || missionIsTerminal}
                onClick={() =>
                  void executeAction(
                    "mission.abort",
                    () => invokeMissionAbort(DEFAULT_MISSION, missionReason),
                    "Abort the current mission through the control plane?",
                  )
                }
              >
                Abort mission
              </button>
              <button
                type="button"
                className="action-button action-button--secondary"
                disabled={busyAction !== null || !missionIsTerminal}
                onClick={() =>
                  void executeAction("mission.reset", () => invokeMissionReset(DEFAULT_MISSION, missionReason))
                }
              >
                Reset mission
              </button>
            </div>
            <label className="field">
              <span>Mission reason / operator note</span>
              <textarea value={missionReason} onChange={(event) => setMissionReason(event.target.value)} rows={3} />
            </label>
            <dl className="detail-grid">
              <dt>Status</dt>
              <dd>{missionStatus?.status ?? "n/a"}</dd>
              <dt>Plan ref</dt>
              <dd>{missionStatus?.plan_ref ?? "n/a"}</dd>
              <dt>Fallback</dt>
              <dd>{missionStatus?.fallback_policy ?? "n/a"}</dd>
              <dt>Last command</dt>
              <dd>{String(missionStatus?.constraints.last_command ?? "n/a")}</dd>
              <dt>Progress</dt>
              <dd>
                {String(missionStatus?.constraints.current_waypoint_index ?? 0)}/
                {String(missionStatus?.constraints.total_waypoints ?? 0)}
              </dd>
              <dt>Terminal</dt>
              <dd>{String(missionStatus?.constraints.terminal ?? false)}</dd>
            </dl>
          </section>

          <section className="panel-card">
            <div className="panel-card__header">
              <h2>Mission constraints</h2>
              <span>derived from control plane</span>
            </div>
            <pre className="json-panel">{JSON.stringify(missionStatus?.constraints ?? {}, null, 2)}</pre>
          </section>

          <section className="panel-card">
            <div className="panel-card__header">
              <h2>Mission capability mapping</h2>
              <span>{boolLabel(capabilityAvailable(capabilities, "mission.control"))}</span>
            </div>
            <ul className="summary-list">
              {(missionStatus?.required_capabilities ?? []).map((capabilityName) => (
                <li key={capabilityName}>
                  <strong>{capabilityName}</strong>
                  <span>{capabilityAvailable(capabilities, capabilityName) ? "available" : "unavailable"}</span>
                </li>
              ))}
            </ul>
          </section>
        </section>
      ) : null}

      {page === "safety" ? (
        <section className="console-section-grid">
          <section className="panel-card panel-card--strong">
            <div className="panel-card__header">
              <h2>Safety state</h2>
              <span>{safetyStatus?.state ?? "n/a"}</span>
            </div>
            <p className="panel-card__summary">{safetyStatus?.summary ?? "No safety summary available."}</p>
            <div className="field-grid">
              <label className="field">
                <span>Fault type</span>
                <input value={faultType} onChange={(event) => setFaultType(event.target.value)} placeholder="gps_loss" />
              </label>
              <label className="field">
                <span>Fault value</span>
                <input value={faultValue} onChange={(event) => setFaultValue(event.target.value)} placeholder="1.0" />
              </label>
            </div>
            <label className="field">
              <span>Fault detail</span>
              <textarea value={faultDetail} onChange={(event) => setFaultDetail(event.target.value)} rows={3} />
            </label>
            <div className="action-row">
              <button
                type="button"
                className="action-button action-button--danger"
                disabled={busyAction !== null || actionDisabledBySession(session?.status) || !faultType}
                onClick={() =>
                  void executeAction(
                    "safety.inject_fault",
                    () => invokeSafetyInjectFault(faultType, Number(faultValue), faultDetail),
                    `Inject safety fault ${faultType}?`,
                  )
                }
              >
                Inject fault
              </button>
              <button
                type="button"
                className="action-button action-button--secondary"
                disabled={busyAction !== null || actionDisabledBySession(session?.status) || !faultType}
                onClick={() =>
                  void executeAction(
                    "safety.clear_fault",
                    () => invokeSafetyClearFault(faultType),
                    `Clear safety fault ${faultType}?`,
                  )
                }
              >
                Clear fault
              </button>
            </div>
          </section>

          <section className="panel-card">
            <div className="panel-card__header">
              <h2>Active faults</h2>
              <span>{safetyStatus?.active_faults.length ?? 0}</span>
            </div>
            <ul className="summary-list">
              {(safetyStatus?.active_faults ?? []).length === 0 ? (
                <li>
                  <strong>No active faults</strong>
                  <span>clear</span>
                </li>
              ) : (
                safetyStatus?.active_faults.map((fault) => (
                  <li key={fault.fault_type}>
                    <strong>{fault.fault_type}</strong>
                    <span>{fault.detail || fault.source || "operator"}</span>
                    <code>{fault.raised_at ?? "n/a"}</code>
                  </li>
                ))
              )}
            </ul>
          </section>

          <section className="panel-card">
            <div className="panel-card__header">
              <h2>Recent audit events</h2>
              <span>read model</span>
            </div>
            <EventsTable events={recentEvents} />
          </section>
        </section>
      ) : null}

      {page === "perception" ? (
        <section className="console-section-grid">
          <section className="panel-card panel-card--strong">
            <div className="panel-card__header">
              <h2>Perception pipeline</h2>
              <span>{perceptionStatus?.healthy ? "healthy" : "degraded"}</span>
            </div>
            <p className="panel-card__summary">{perceptionStatus?.detail ?? "No perception summary available."}</p>
            <dl className="detail-grid">
              <dt>Healthy</dt>
              <dd>{boolLabel(perceptionStatus?.healthy)}</dd>
              <dt>Tracked</dt>
              <dd>{boolLabel(trackedObject.tracked)}</dd>
              <dt>Detections available</dt>
              <dd>{boolLabel(perceptionStatus?.detections_available)}</dd>
              <dt>Last heartbeat age</dt>
              <dd>
                {typeof perceptionStatus?.last_heartbeat_age_ms === "number"
                  ? `${perceptionStatus.last_heartbeat_age_ms} ms`
                  : "n/a"}
              </dd>
              <dt>Latency</dt>
              <dd>
                {typeof perceptionHeartbeat.pipeline_latency_s === "number"
                  ? `${perceptionHeartbeat.pipeline_latency_s.toFixed(3)} s`
                  : "n/a"}
              </dd>
              <dt>Frame age</dt>
              <dd>{typeof perceptionHeartbeat.frame_age_s === "number" ? `${perceptionHeartbeat.frame_age_s.toFixed(3)} s` : "n/a"}</dd>
            </dl>
          </section>

          <section className="panel-card">
            <div className="panel-card__header">
              <h2>Tracked object</h2>
              <span>{trackedObject.state ?? "snapshot"}</span>
            </div>
            <pre className="json-panel">{JSON.stringify(trackedObject, null, 2)}</pre>
          </section>

          <section className="panel-card">
            <div className="panel-card__header">
              <h2>Camera / stream proxy</h2>
              <span>{perceptionStreamStatus?.stream_available ? "available" : "unavailable"}</span>
            </div>
            <p className="panel-card__summary">{perceptionStreamStatus?.detail ?? "No stream status available."}</p>
            {perceptionStreamStatus?.stream_available && perceptionStreamStatus.stream_url ? (
              <a className="stream-link" href={perceptionStreamStatus.stream_url} target="_blank" rel="noreferrer">
                Open stream proxy
              </a>
            ) : perceptionStreamStatus?.source ? (
              <div className="dashboard-muted">Source: {perceptionStreamStatus.source}</div>
            ) : (
              <div className="dashboard-muted">No live stream configured in the current environment.</div>
            )}
          </section>

          <section className="panel-card">
            <div className="panel-card__header">
              <h2>Latest perception event</h2>
              <span>{snapshot?.latest_by_kind?.perception_event?.kind ?? "n/a"}</span>
            </div>
            <pre className="json-panel">{JSON.stringify(perceptionEvent, null, 2)}</pre>
          </section>
        </section>
      ) : null}

      {page === "runs" ? (
        <>
          <section className="runs-toolbar">
            <div>
              <h2>Run timeline</h2>
              <p>{currentRunLabel}</p>
            </div>
            <label className="field">
              <span>Selected run</span>
              <select value={selectedRunId} onChange={(event) => setSelectedRunId(event.target.value)}>
                {runs?.runs.length ? null : <option value="">No runs available</option>}
                {runs?.runs.map((run) => (
                  <option key={run.run_id} value={run.run_id}>
                    {run.run_id} • {run.run_kind}
                  </option>
                ))}
              </select>
            </label>
          </section>

          <section className="overview-grid">
            <section className="panel-card panel-card--strong">
              <div className="panel-card__header">
                <h2>Run details</h2>
                <span>{selectedRun?.status ?? "n/a"}</span>
              </div>
              <dl className="detail-grid">
                <dt>Name</dt>
                <dd>{selectedRun?.name ?? "n/a"}</dd>
                <dt>Run id</dt>
                <dd>{selectedRun?.run_id ?? "n/a"}</dd>
                <dt>Session</dt>
                <dd>{selectedRun?.session_id ?? "n/a"}</dd>
                <dt>Started</dt>
                <dd>{isoToDate(selectedRun?.started_at)}</dd>
                <dt>Ended</dt>
                <dd>{isoToDate(selectedRun?.ended_at)}</dd>
                <dt>Summary</dt>
                <dd>{selectedRun?.summary ?? "n/a"}</dd>
              </dl>
              <div className="artifact-list">
                {(lastAction?.run_id === selectedRunId ? lastAction.artifacts : []).map((artifact) => (
                  <a key={`${artifact.artifact_type}:${artifact.uri}`} className="artifact-link" href={artifact.uri}>
                    {artifact.artifact_type}: {artifact.uri}
                  </a>
                ))}
              </div>
            </section>

            <section className="panel-card">
              <div className="panel-card__header">
                <h2>Action correlation</h2>
                <span>{lastAction?.run_id === selectedRunId ? "linked" : "waiting"}</span>
              </div>
              {lastAction ? (
                <dl className="detail-grid">
                  <dt>Request id</dt>
                  <dd>{lastAction.request_id}</dd>
                  <dt>Message</dt>
                  <dd>{lastAction.message}</dd>
                  <dt>Run id</dt>
                  <dd>{lastAction.run_id ?? "n/a"}</dd>
                  <dt>Linked</dt>
                  <dd>{boolLabel(lastAction.run_id === selectedRunId)}</dd>
                </dl>
              ) : (
                <div className="dashboard-muted">Trigger an action to inspect request-to-run correlation.</div>
              )}
            </section>
          </section>

          <section className="lower-grid">
            <EventsTable events={recentEvents} />
            <ReplayPanel
              events={replay?.events ?? []}
              selectedIndex={selectedReplayIndex}
              onSelectedIndexChange={setSelectedReplayIndex}
            />
          </section>

          <section className="lower-grid">
            <MetricsPanel metrics={metrics} />

            <section className="panel-card">
              <div className="panel-card__header">
                <h2>Run inventory</h2>
                <span>{runs?.runs.length ?? 0} merged runs</span>
              </div>
              <ul className="summary-list">
                {(runs?.runs ?? []).map((run) => (
                  <li key={run.run_id}>
                    <button type="button" className="summary-action" onClick={() => setSelectedRunId(run.run_id)}>
                      <strong>{run.name}</strong>
                      <span>{run.status}</span>
                      <code>{run.session_id ?? "no session id"}</code>
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          </section>
        </>
      ) : null}

      {page === "settings" ? (
        <section className="console-section-grid">
          <section className="panel-card panel-card--strong">
            <div className="panel-card__header">
              <h2>Environment</h2>
              <span>{session?.environment.environment_name ?? "n/a"}</span>
            </div>
            <dl className="detail-grid">
              <dt>Simulator family</dt>
              <dd>{session?.environment.simulator_family ?? "n/a"}</dd>
              <dt>Vehicle profile</dt>
              <dd>{session?.environment.vehicle_profile ?? "n/a"}</dd>
              <dt>Baseline</dt>
              <dd>{session?.environment.baseline ?? "n/a"}</dd>
              <dt>Mode</dt>
              <dd>{session?.mode ?? "n/a"}</dd>
              <dt>Started</dt>
              <dd>{isoToDate(session?.started_at)}</dd>
            </dl>
          </section>

          <section className="panel-card">
            <div className="panel-card__header">
              <h2>API boundaries</h2>
              <span>control vs read model</span>
            </div>
            <dl className="detail-grid">
              <dt>Control API</dt>
              <dd>{import.meta.env.VITE_CONTROL_API_BASE_URL ?? "http://127.0.0.1:8090"}</dd>
              <dt>Read API</dt>
              <dd>
                {import.meta.env.VITE_READ_API_BASE_URL ??
                  import.meta.env.VITE_CONTROL_API_BASE_URL ??
                  "http://127.0.0.1:8090"}
              </dd>
              <dt>Capabilities</dt>
              <dd>{capabilitySummary.total}</dd>
              <dt>Telemetry run</dt>
              <dd>{currentTelemetryRunId ?? "n/a"}</dd>
            </dl>
          </section>
        </section>
      ) : null}
    </main>
  );
}

export default App;
