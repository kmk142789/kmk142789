import { describe, expect, it, vi } from 'vitest';
import { StateStore, defaultState } from './state';
import { startWorldLoop } from './world';

describe('StateStore', () => {
  it('updates history when appended', () => {
    const store = new StateStore({ ...defaultState, history: [] });
    store.appendHistory({ kind: 'event', text: 'hello', ts: 1 });
    expect(store.snapshot.history).toHaveLength(1);
  });

  it('upserts memories by key', () => {
    const store = new StateStore({ ...defaultState, memory: [] });
    store.upsertMemory({ key: 'user:name', value: 'Echo', ts: 1 });
    store.upsertMemory({ key: 'user:name', value: 'Echo Prime', ts: 2 });
    expect(store.snapshot.memory).toEqual([{ key: 'user:name', value: 'Echo Prime', ts: 2 }]);
  });
});

describe('world loop', () => {
  it('produces activity events over time', async () => {
    vi.useFakeTimers();
    const store = new StateStore({ ...defaultState });
    const events: string[] = [];
    const stop = startWorldLoop(store, {
      onEvent: (entry) => events.push(entry.text),
    });

    vi.advanceTimersByTime(13000);
    expect(events.length).toBeGreaterThan(0);
    stop?.();
    vi.useRealTimers();
  });
});
