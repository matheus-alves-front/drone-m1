import type { MetricRecord } from "../types";

type MetricsPanelProps = {
  metrics: MetricRecord[];
};

function metricValue(value: number | string | boolean | null | undefined, suffix = ""): string {
  if (value === null || value === undefined || value === "") {
    return "n/a";
  }
  if (typeof value === "number") {
    return `${value.toFixed(2)}${suffix}`;
  }
  return `${String(value)}${suffix}`;
}

export function MetricsPanel({ metrics }: MetricsPanelProps) {
  const latest = metrics[metrics.length - 1] ?? null;

  return (
    <section className="event-feed">
      <div className="event-feed__header">
        <h2>Metric samples</h2>
        <span>{metrics.length} samples in view</span>
      </div>
      {latest ? (
        <ul>
          <li>
            <strong>Mission phase</strong>
            <span>{latest.mission_phase || "n/a"}</span>
          </li>
          <li>
            <strong>Altitude</strong>
            <span>{metricValue(latest.altitude_m, " m")}</span>
          </li>
          <li>
            <strong>Relative altitude</strong>
            <span>{metricValue(latest.relative_altitude_m, " m")}</span>
          </li>
          <li>
            <strong>Perception latency</strong>
            <span>{metricValue(latest.perception_latency_s, " s")}</span>
          </li>
          <li>
            <strong>Safety action</strong>
            <span>{latest.safety_action || "n/a"}</span>
          </li>
        </ul>
      ) : (
        <div className="replay-panel__empty">No metric samples captured for the selected run.</div>
      )}
    </section>
  );
}
