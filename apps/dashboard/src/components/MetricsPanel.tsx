import type { MetricsResponse } from "../types";

type MetricsPanelProps = {
  metrics: MetricsResponse;
};

export function MetricsPanel({ metrics }: MetricsPanelProps) {
  return (
    <section className="event-feed">
      <div className="event-feed__header">
        <h2>Metrics</h2>
        <span>{metrics.total_events} total envelopes</span>
      </div>
      <ul>
        {Object.entries(metrics.counts_by_kind).map(([kind, count]) => (
          <li key={kind}>
            {kind}: {count}
          </li>
        ))}
      </ul>
    </section>
  );
}
