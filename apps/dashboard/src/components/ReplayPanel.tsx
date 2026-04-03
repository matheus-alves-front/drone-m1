import type { StoredEnvelope } from "../types";

interface ReplayPanelProps {
  events: StoredEnvelope[];
  selectedIndex: number;
  onSelectedIndexChange: (index: number) => void;
}

export function ReplayPanel({ events, selectedIndex, onSelectedIndexChange }: ReplayPanelProps) {
  const selectedEvent = events[selectedIndex] ?? null;

  return (
    <section className="replay-panel">
      <div className="replay-panel__header">
        <div>
          <h2>Replay</h2>
          <p>Scrub through the persisted telemetry timeline for the current session.</p>
        </div>
        <div className="replay-panel__meta">{events.length} events</div>
      </div>
      <input
        aria-label="Replay event index"
        className="replay-panel__slider"
        type="range"
        min={0}
        max={Math.max(events.length - 1, 0)}
        value={Math.min(selectedIndex, Math.max(events.length - 1, 0))}
        onChange={(event) => onSelectedIndexChange(Number(event.target.value))}
        disabled={events.length === 0}
      />
      {selectedEvent ? (
        <div className="replay-panel__event">
          <div className="replay-panel__event-meta">
            <strong>{selectedEvent.kind}</strong>
            <span>{selectedEvent.topic}</span>
            <span>seq {selectedEvent.sequence}</span>
          </div>
          <pre>{JSON.stringify(selectedEvent.payload, null, 2)}</pre>
        </div>
      ) : (
        <div className="replay-panel__empty">No replay data captured yet.</div>
      )}
    </section>
  );
}
