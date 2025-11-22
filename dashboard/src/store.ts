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

export interface CredentialEvent {
  id: string;
  subject: string;
  status: string;
  issued_at: string;
}

export interface LedgerAction {
  id: string;
  action: string;
  network: string;
  status: string;
  timestamp: string;
}

export interface ProofRecord {
  id: string;
  type: string;
  anchor: string;
  status: string;
  timestamp: string;
}

export interface AmendmentRecord {
  id: string;
  title: string;
  status: string;
  updated_at: string;
}

export interface PlanRecord {
  id: string;
  name: string;
  stage: string;
  next_step: string;
}

export interface BridgeLog {
  id: string;
  source: string;
  destination: string;
  status: string;
  height: number;
}

interface DashboardState {
  metrics?: MetricsSnapshot;
  nodes: NodeInfo[];
  queue: QueueItem[];
  credentials: CredentialEvent[];
  ledgerActions: LedgerAction[];
  proofs: ProofRecord[];
  amendments: AmendmentRecord[];
  plans: PlanRecord[];
  bridgeLogs: BridgeLog[];
  setMetrics: (metrics: MetricsSnapshot) => void;
  setNodes: (nodes: NodeInfo[]) => void;
  setQueue: (queue: QueueItem[]) => void;
  setCredentials: (credentials: CredentialEvent[]) => void;
  setLedgerActions: (actions: LedgerAction[]) => void;
  setProofs: (proofs: ProofRecord[]) => void;
  setAmendments: (amendments: AmendmentRecord[]) => void;
  setPlans: (plans: PlanRecord[]) => void;
  setBridgeLogs: (logs: BridgeLog[]) => void;
}

export const useDashboard = create<DashboardState>((set) => ({
  nodes: [],
  queue: [],
  credentials: [],
  ledgerActions: [],
  proofs: [],
  amendments: [],
  plans: [],
  bridgeLogs: [],
  setMetrics: (metrics) => set({ metrics }),
  setNodes: (nodes) => set({ nodes }),
  setQueue: (queue) => set({ queue }),
  setCredentials: (credentials) => set({ credentials }),
  setLedgerActions: (ledgerActions) => set({ ledgerActions }),
  setProofs: (proofs) => set({ proofs }),
  setAmendments: (amendments) => set({ amendments }),
  setPlans: (plans) => set({ plans }),
  setBridgeLogs: (bridgeLogs) => set({ bridgeLogs }),
}));
