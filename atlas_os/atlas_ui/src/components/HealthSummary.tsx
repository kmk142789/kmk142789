import React from 'react';
import { resolveSeverityColor, themePalettes, ThemeVariant } from '../theme';

type HealthState = {
  status: string;
  reason?: string;
  incidents?: { severity: 'info' | 'warn' | 'error'; message: string; ts: number }[];
};

type HealthSummaryProps = {
  health: HealthState;
  variant?: ThemeVariant;
};

export const HealthSummary: React.FC<HealthSummaryProps> = ({ health, variant = 'light' }) => {
  const palette = themePalettes[variant];
  return (
    <aside className="health-summary" style={{ borderColor: palette.accent }}>
      <h2>Cluster Health</h2>
      <div className="health-summary__status" style={{ color: resolveSeverityColor(palette, 'info') }}>
        {health.status.toUpperCase()}
      </div>
      {health.reason && <p className="health-summary__reason">{health.reason}</p>}
      {health.incidents && health.incidents.length > 0 && (
        <ul className="health-summary__incidents">
          {health.incidents.map((incident) => (
            <li key={incident.ts} style={{ borderLeftColor: resolveSeverityColor(palette, incident.severity) }}>
              <time>{new Date(incident.ts).toLocaleTimeString()}</time>
              <span>{incident.message}</span>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
};
