import React, { useEffect, useState } from 'react';
import create from 'zustand';
import { MetricsPanel } from './MetricsPanel';
import { NodeGraph } from './NodeGraph';
import { LogPanel } from './LogPanel';
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
  useWebSocket('ws://localhost:9000/metrics');
  const metrics = useDashboardStore((s) => s.metrics);
  const logs = useDashboardStore((s) => s.logs);
  const nodes = useDashboardStore((s) => s.nodes);
  const drives = useDashboardStore((s) => s.drives);
  const health = useDashboardStore((s) => s.health);

  return (
    <div className="atlas-dashboard">
      <header>
        <h1>Atlas OS Control Plane</h1>
        <div className={`health health-${health.status}`}>
          <strong>Health:</strong> {health.status}
          {health.reason && <span> – {health.reason}</span>}
        </div>
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
      </main>
    </div>
  );
};
