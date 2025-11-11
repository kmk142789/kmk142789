import create from 'zustand';

export interface MetricsSnapshot {
  counters: Record<string, number>;
  timers: Record<string, { count: number; avg: number; max: number }>;
}

export interface QueueItem {
  id: string;
  tenant: string;
  status: string;
  schedule_at: string;
}

export interface NodeInfo {
  id: string;
  url: string;
  weight: number;
}

interface DashboardState {
  metrics?: MetricsSnapshot;
  nodes: NodeInfo[];
  queue: QueueItem[];
  setMetrics: (metrics: MetricsSnapshot) => void;
  setNodes: (nodes: NodeInfo[]) => void;
  setQueue: (queue: QueueItem[]) => void;
}

export const useDashboard = create<DashboardState>((set) => ({
  nodes: [],
  queue: [],
  setMetrics: (metrics) => set({ metrics }),
  setNodes: (nodes) => set({ nodes }),
  setQueue: (queue) => set({ queue }),
}));
