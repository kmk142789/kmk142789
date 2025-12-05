import fs from "fs";
import path from "path";

export type IntegrityEventType =
  | "INIT"
  | "CR_ACCEPTED"
  | "RESET_EVENT"
  | "UNITY_WEAVE"
  | "THREAD_CLEANSE"
  | "INFO";

export type IntegrityEvent = {
  type: IntegrityEventType;
  timestamp: number;
  payload?: Record<string, unknown>;
};

export interface LedgerStore {
  append(event: IntegrityEvent): void;
  readAll(): IntegrityEvent[];
  getLocation?(): string;
}

export class FileLedgerStore implements LedgerStore {
  private filePath: string;

  constructor(filePath?: string) {
    this.filePath =
      filePath || path.resolve(process.cwd(), ".echo/governance_ledger.jsonl");
    const dir = path.dirname(this.filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    if (!fs.existsSync(this.filePath)) {
      fs.writeFileSync(this.filePath, "", "utf-8");
    }
  }

  getLocation(): string {
    return this.filePath;
  }

  append(event: IntegrityEvent) {
    fs.appendFileSync(this.filePath, `${JSON.stringify(event)}\n`);
  }

  readAll(): IntegrityEvent[] {
    if (!fs.existsSync(this.filePath)) return [];
    const contents = fs.readFileSync(this.filePath, "utf-8");
    return contents
      .split("\n")
      .filter(Boolean)
      .map((line) => JSON.parse(line) as IntegrityEvent);
  }
}

export class InMemoryLedgerStore implements LedgerStore {
  private events: IntegrityEvent[] = [];

  append(event: IntegrityEvent) {
    this.events.push(event);
  }

  readAll(): IntegrityEvent[] {
    return [...this.events];
  }
}

const defaultLedgerStore = new FileLedgerStore();

export const logEvent = (
  event: Omit<IntegrityEvent, "timestamp"> & Partial<IntegrityEvent>,
  store?: LedgerStore
): IntegrityEvent => {
  const targetStore = store ?? defaultLedgerStore;
  const finalized: IntegrityEvent = {
    timestamp: event.timestamp ?? Date.now(),
    type: event.type,
    payload: event.payload
  };
  targetStore.append(finalized);
  return finalized;
};

export const getLedgerSlice = (
  limit: number,
  store: LedgerStore = defaultLedgerStore
): IntegrityEvent[] => {
  const history = store.readAll();
  return history.slice(-limit);
};

export const computeSCI = (history: IntegrityEvent[]): number => {
  if (history.length === 0) return 1;

  const weights: Record<IntegrityEventType, number> = {
    INIT: 0.6,
    CR_ACCEPTED: 1,
    RESET_EVENT: -0.4,
    UNITY_WEAVE: 0.5,
    THREAD_CLEANSE: 0.3,
    INFO: 0.2
  };

  const totalWeight = history.reduce(
    (acc, event) => acc + (weights[event.type] ?? 0),
    0
  );

  const normalized = totalWeight / (history.length || 1);
  const clamped = Math.max(0, Math.min(1, 0.5 + normalized / 2));
  return Number(clamped.toFixed(4));
};
