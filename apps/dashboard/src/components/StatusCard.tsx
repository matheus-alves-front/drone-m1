import type { ReactNode } from "react";

interface StatusCardProps {
  title: string;
  accent: string;
  children: ReactNode;
}

export function StatusCard({ title, accent, children }: StatusCardProps) {
  return (
    <section className="status-card" style={{ ["--card-accent" as string]: accent }}>
      <header className="status-card__header">
        <span className="status-card__accent" />
        <h2>{title}</h2>
      </header>
      <div className="status-card__body">{children}</div>
    </section>
  );
}
