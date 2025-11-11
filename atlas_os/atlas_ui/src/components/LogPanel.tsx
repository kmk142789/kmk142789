import React from 'react';

type LogEntry = { ts: number; message: string };

type Props = { logs: LogEntry[] };

const formatTimestamp = (ts: number) => new Date(ts).toLocaleTimeString();

export const LogPanel: React.FC<Props> = ({ logs }) => (
  <div className="log-panel">
    <h2>Event Log</h2>
    {logs.map((entry) => (
      <div key={`${entry.ts}-${entry.message}`} className="log-entry">
        <span>[{formatTimestamp(entry.ts)}]</span> {entry.message}
      </div>
    ))}
  </div>
);
