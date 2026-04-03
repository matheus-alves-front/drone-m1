import type { StoredEnvelope } from "../types";

type EventsTableProps = {
  events: StoredEnvelope[];
};

export function EventsTable({ events }: EventsTableProps) {
  return (
    <section className="event-feed">
      <div className="event-feed__header">
        <h2>Recent events</h2>
        <span>{events.length} retained for audit</span>
      </div>
      <ul>
        {events.map((event) => (
          <li key={`${event.run_id}-${event.sequence}`}>
            <strong>{event.kind}</strong>
            <span>{event.topic}</span>
            <code>
              run={event.run_id} seq={event.sequence}
            </code>
          </li>
        ))}
      </ul>
    </section>
  );
}
