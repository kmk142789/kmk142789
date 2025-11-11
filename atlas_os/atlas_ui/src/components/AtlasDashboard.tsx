import React, { useEffect, useMemo, useState } from 'react';
import create from 'zustand';
import { MetricsPanel } from './MetricsPanel';
import { NodeGraph } from './NodeGraph';
import { LogPanel } from './LogPanel';
import { HealthSummary } from './HealthSummary';
import { ActivityTimeline } from './ActivityTimeline';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import { themePalettes, ThemeVariant } from '../theme';
import './dashboard.css';

type Metric = { name: string; value: number; timestamp: number };
type LogEntry = { ts: number; message: string };
type Node = { id: string; host: string; port: number; status: 'online' | 'offline' };

type DashboardState = {
  metrics: Metric[];
  logs: LogEntry[];
  nodes: Node[];
  drives: { id: string; capacity: number; used: number }[];
  health: { status: string; reason?: string };
  addMetric: (metric: Metric) => void;
  addLog: (entry: LogEntry) => void;
  setNodes: (nodes: Node[]) => void;
  setDrives: (drives: { id: string; capacity: number; used: number }[]) => void;
  setHealth: (health: { status: string; reason?: string }) => void;
  clearLogs: () => void;
};

const useDashboardStore = create<DashboardState>((set) => ({
  metrics: [],
  logs: [],
  nodes: [],
  drives: [],
  health: { status: 'unknown' },
  addMetric: (metric) => set((state) => ({ metrics: [...state.metrics.slice(-24), metric] })),
  addLog: (entry) => set((state) => ({ logs: [...state.logs.slice(-50), entry] })),
  setNodes: (nodes) => set({ nodes }),
  setDrives: (drives) => set({ drives }),
  setHealth: (health) => set({ health }),
  clearLogs: () => set({ logs: [] }),
}));

const useWebSocket = (url: string) => {
  const addMetric = useDashboardStore((s) => s.addMetric);
  const addLog = useDashboardStore((s) => s.addLog);
  const setNodes = useDashboardStore((s) => s.setNodes);
  const setDrives = useDashboardStore((s) => s.setDrives);
  const setHealth = useDashboardStore((s) => s.setHealth);

  useEffect(() => {
    const ws = new WebSocket(url);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.metric) {
        addMetric(data.metric);
      }
      if (data.log) {
        addLog(data.log);
      }
      if (data.nodes) {
        setNodes(data.nodes);
      }
      if (data.drives) {
        setDrives(data.drives);
      }
      if (data.health) {
        setHealth(data.health);
      }
    };
    return () => ws.close();
  }, [url, addMetric, addLog, setNodes, setDrives, setHealth]);
};

export const AtlasDashboard: React.FC = () => {
  const [theme, setTheme] = useState<ThemeVariant>('light');
  useWebSocket('ws://localhost:9000/metrics');
  const metrics = useDashboardStore((s) => s.metrics);
  const logs = useDashboardStore((s) => s.logs);
  const nodes = useDashboardStore((s) => s.nodes);
  const drives = useDashboardStore((s) => s.drives);
  const health = useDashboardStore((s) => s.health);
  const clearLogs = useDashboardStore((s) => s.clearLogs);
  const palette = themePalettes[theme];

  useKeyboardShortcuts({
    'mod+k': () => setTheme((variant) => (variant === 'light' ? 'dark' : 'light')),
    'mod+shift+l': () => clearLogs(),
  });

  const incidents = useMemo(
    () =>
      logs
        .filter((entry) => entry.message.toLowerCase().includes('error'))
        .map((entry) => ({ severity: 'error' as const, message: entry.message, ts: entry.ts })),
    [logs],
  );

  const timelineEntries = useMemo(() => logs.slice(-30), [logs]);

  return (
    <div
      className="atlas-dashboard"
      style={{ backgroundColor: palette.background, color: palette.foreground }}
    >
      <header>
        <h1>Atlas OS Control Plane</h1>
        <div className={`health health-${health.status}`}>
          <strong>Health:</strong> {health.status}
          {health.reason && <span> – {health.reason}</span>}
        </div>
        <button
          className="theme-toggle"
          onClick={() => setTheme((variant) => (variant === 'light' ? 'dark' : 'light'))}
        >
          Toggle Theme
        </button>
      </header>
      <main>
        <section className="metrics-section">
          <MetricsPanel metrics={metrics} drives={drives} />
        </section>
        <section className="graph-section">
          <NodeGraph nodes={nodes} />
        </section>
        <section className="logs-section">
          <LogPanel logs={logs} />
        </section>
        <aside className="health-section">
          <HealthSummary health={{ ...health, incidents }} variant={theme} />
        </aside>
        <section className="timeline-section">
          <ActivityTimeline entries={timelineEntries} />
        </section>
      </main>
    </div>
  );
};
