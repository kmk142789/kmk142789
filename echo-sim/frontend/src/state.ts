export type MemoryItem = { key: string; value: string; ts: number };
export type HistoryItem = { kind: 'chat' | 'code' | 'event'; text: string; ts: number };
export type ClockPhase = 'morning' | 'afternoon' | 'evening' | 'night';
export type Mood = 'happy' | 'curious' | 'tired' | 'focused';

export type EchoState = {
  energy: number;
  focus: number;
  creativity: number;
  mood: Mood;
  clock: ClockPhase;
  memory: MemoryItem[];
  history: HistoryItem[];
};

export type Listener = (state: EchoState) => void;

const LOCAL_KEY = 'echo-sim-state-v1';

const seedMemories: MemoryItem[] = [
  { key: 'user:name', value: 'Josh', ts: Date.now() - 1000 * 60 * 60 },
  { key: 'echo:origin', value: 'Echo woke beside a glowing desk lamp.', ts: Date.now() - 1000 * 60 * 30 },
];

const seedHistory: HistoryItem[] = [
  { kind: 'event', text: 'Echo stretched and surveyed the studio.', ts: Date.now() - 1000 * 60 * 25 },
  { kind: 'chat', text: 'Echo: “Ready for another idea?”', ts: Date.now() - 1000 * 60 * 3 },
  { kind: 'code', text: 'Echo drafted a lamp shimmer script.', ts: Date.now() - 1000 * 60 * 2 },
];

export const defaultState: EchoState = {
  energy: 80,
  focus: 60,
  creativity: 75,
  mood: 'curious',
  clock: deriveClockFromDate(new Date()),
  memory: seedMemories,
  history: seedHistory,
};

export class StateStore {
  private state: EchoState;
  private listeners = new Set<Listener>();

  constructor(initial?: EchoState) {
    this.state = initial ?? loadState() ?? defaultState;
  }

  get snapshot(): EchoState {
    return this.state;
  }

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    listener(this.state);
    return () => this.listeners.delete(listener);
  }

  patch(partial: Partial<EchoState>) {
    this.state = { ...this.state, ...partial };
    persistState(this.state);
    this.emit();
  }

  mutate(mutator: (current: EchoState) => EchoState) {
    this.state = mutator(this.state);
    persistState(this.state);
    this.emit();
  }

  appendHistory(entry: HistoryItem) {
    this.mutate((current) => ({
      ...current,
      history: [...current.history.slice(-199), entry],
    }));
  }

  upsertMemory(entry: MemoryItem) {
    this.mutate((current) => {
      const rest = current.memory.filter((item) => item.key !== entry.key);
      return { ...current, memory: [...rest, entry] };
    });
  }

  private emit() {
    this.listeners.forEach((listener) => listener(this.state));
  }
}

export function deriveClockFromDate(date: Date): ClockPhase {
  const hour = date.getHours();
  if (hour >= 6 && hour < 12) return 'morning';
  if (hour >= 12 && hour < 17) return 'afternoon';
  if (hour >= 17 && hour < 21) return 'evening';
  return 'night';
}

export function loadState(): EchoState | null {
  if (typeof localStorage === 'undefined') return null;
  try {
    const raw = localStorage.getItem(LOCAL_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as EchoState;
    return {
      ...defaultState,
      ...parsed,
      memory: parsed.memory ?? defaultState.memory,
      history: parsed.history ?? defaultState.history,
    };
  } catch (err) {
    console.warn('Failed to load Echo state', err);
    return null;
  }
}

export function persistState(state: EchoState) {
  if (typeof localStorage === 'undefined') return;
  try {
    localStorage.setItem(LOCAL_KEY, JSON.stringify(state));
  } catch (err) {
    console.warn('Failed to persist Echo state', err);
  }
}
