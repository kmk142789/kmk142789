import { ClockPhase, EchoState, Mood, StateStore, deriveClockFromDate } from './state';

const ACTION_INTERVAL_MS = 6000;
const RESTORE_INTERVAL_MS = 15000;

type WorldHooks = {
  onEvent: (entry: { kind: 'chat' | 'code' | 'event'; text: string; ts: number }) => void;
  onClockChange?: (phase: ClockPhase) => void;
};

type BehaviorPhase = 'idle' | 'act' | 'reflect' | 'rest';

const paletteByClock = {
  morning: { gradient: '#fbbf24, #38bdf8', accent: '#f97316' },
  afternoon: { gradient: '#38bdf8, #0ea5e9', accent: '#22d3ee' },
  evening: { gradient: '#f59e0b, #6366f1', accent: '#a855f7' },
  night: { gradient: '#312e81, #0f172a', accent: '#38bdf8' },
} as const satisfies Record<ClockPhase, { gradient: string; accent: string }>;

export function getClockPalette(clock: ClockPhase) {
  return paletteByClock[clock];
}

export function startWorldLoop(store: StateStore, hooks: WorldHooks) {
  let currentPhase: BehaviorPhase = 'idle';
  let timer: ReturnType<typeof setTimeout> | undefined;

  const advance = () => {
    const now = Date.now();
    const snapshot = store.snapshot;

    switch (currentPhase) {
      case 'idle':
        currentPhase = 'act';
        store.patch({ mood: rollMood(snapshot) });
        break;
      case 'act':
        currentPhase = 'reflect';
        performAction(store, hooks.onEvent, now);
        break;
      case 'reflect':
        currentPhase = 'rest';
        hooks.onEvent({
          kind: 'event',
          text: 'Echo reflects on the last spark of activity.',
          ts: now,
        });
        store.mutate((state) => ({
          ...state,
          focus: clamp(state.focus + 3, 0, 100),
          creativity: clamp(state.creativity + 2, 0, 100),
        }));
        break;
      case 'rest':
      default:
        currentPhase = 'idle';
        store.mutate((state) => ({
          ...state,
          energy: clamp(state.energy + 4, 0, 100),
          focus: clamp(state.focus - 2, 0, 100),
        }));
        break;
    }

    syncClock(store, hooks.onClockChange);
    timer = setTimeout(advance, ACTION_INTERVAL_MS);
  };

  timer = setTimeout(advance, ACTION_INTERVAL_MS);

  const restoreTimer = setInterval(() => {
    store.mutate((state) => ({
      ...state,
      energy: clamp(state.energy - 1, 0, 100),
      focus: clamp(state.focus - 1, 0, 100),
      creativity: clamp(state.creativity + 1, 0, 100),
    }));
    syncClock(store, hooks.onClockChange);
  }, RESTORE_INTERVAL_MS);

  return () => {
    if (timer) clearTimeout(timer);
    clearInterval(restoreTimer);
  };
}

function performAction(store: StateStore, onEvent: WorldHooks['onEvent'], ts: number) {
  const actions = [codeAtDesk, stretchByLamp, waterPlant];
  const action = actions[Math.floor(Math.random() * actions.length)];
  const description = action(store);
  onEvent({ kind: 'event', text: description, ts });
}

function codeAtDesk(store: StateStore) {
  store.mutate((state) => ({
    ...state,
    focus: clamp(state.focus + 6, 0, 100),
    creativity: clamp(state.creativity + 4, 0, 100),
    energy: clamp(state.energy - 4, 0, 100),
    mood: 'focused',
  }));
  return 'Echo types quietly at the desk, composing a glimmering script.';
}

function stretchByLamp(store: StateStore) {
  store.mutate((state) => ({
    ...state,
    energy: clamp(state.energy + 5, 0, 100),
    focus: clamp(state.focus - 2, 0, 100),
    mood: 'happy',
  }));
  return 'Echo stretches beside the lamp, basking in its warm pulse.';
}

function waterPlant(store: StateStore) {
  store.mutate((state) => ({
    ...state,
    creativity: clamp(state.creativity + 5, 0, 100),
    focus: clamp(state.focus + 2, 0, 100),
    energy: clamp(state.energy - 3, 0, 100),
    mood: 'curious',
  }));
  return 'Echo waters the fern, whispering a promise of growth.';
}

function rollMood(state: EchoState): Mood {
  if (state.energy < 30) return 'tired';
  if (state.focus > 70) return 'focused';
  if (state.creativity > 80) return 'happy';
  return 'curious';
}

function syncClock(store: StateStore, onClockChange?: (phase: ClockPhase) => void) {
  const nextPhase = deriveClockFromDate(new Date());
  if (store.snapshot.clock !== nextPhase) {
    store.patch({ clock: nextPhase });
    onClockChange?.(nextPhase);
  }
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}
