import { useEffect, useState } from 'react';
import { StateStore, type EchoState, type HistoryItem, type MemoryItem } from '../state';
import { startWorldLoop } from '../world';
import { ChatPanel } from './ChatPanel';
import { StatsPanel } from './StatsPanel';
import { CodePanel } from './CodePanel';
import { MemoryPanel } from './MemoryPanel';
import { HistoryPanel } from './HistoryPanel';
import { WorldScene } from './WorldScene';
import { pullState, pushState, syncEvents, syncMemory } from '../api';

const store = new StateStore();

export default function App() {
  const [state, setState] = useState<EchoState>(store.snapshot);

  useEffect(() => store.subscribe(setState), []);

  useEffect(() => {
    let stop = startWorldLoop(store, {
      onEvent: (entry) => {
        store.appendHistory(entry);
        syncEvents(entry).catch(() => undefined);
      },
      onClockChange: () => pushState(store.snapshot).catch(() => undefined),
    });
    return () => {
      stop?.();
    };
  }, []);

  useEffect(() => {
    pullState()
      .then((remote) => {
        if (remote) {
          store.patch({ ...remote });
        }
      })
      .catch(() => undefined);
  }, []);

  const sendChat = (text: string) => {
    const now = Date.now();
    const userEntry: HistoryItem = { kind: 'chat', text: `You: ${text}`, ts: now };
    store.appendHistory(userEntry);
    syncEvents(userEntry).catch(() => undefined);

    const memoryUpdates: MemoryItem[] = [];
    const matchName = text.match(/my name is (\w+)/i);
    if (matchName) {
      const memory = { key: 'user:name', value: matchName[1], ts: now };
      store.upsertMemory(memory);
      memoryUpdates.push(memory);
    }

    if (text.toLowerCase().includes('lamp')) {
      const memory = { key: 'preference:lamp', value: 'User mentioned the lamp', ts: now };
      store.upsertMemory(memory);
      memoryUpdates.push(memory);
    }

    if (memoryUpdates.length) {
      syncMemory(store.snapshot.memory).catch(() => undefined);
    }

    const response = draftResponse(text, store.snapshot);
    const echoEntry: HistoryItem = { kind: 'chat', text: `Echo: ${response}`, ts: now + 400 };
    store.appendHistory(echoEntry);
    syncEvents(echoEntry).catch(() => undefined);

    store.mutate((current) => ({
      ...current,
      focus: clamp(current.focus + 2),
      creativity: clamp(current.creativity + 1),
      energy: clamp(current.energy - 1),
    }));
  };

  const handleHistory = (entry: HistoryItem) => {
    store.appendHistory(entry);
    syncEvents(entry).catch(() => undefined);
  };

  return (
    <main className="app-shell" style={{ background: 'transparent' }}>
      <StatsPanel state={state} />
      <WorldScene state={state} />
      <CodePanel onHistory={handleHistory} />
      <ChatPanel history={state.history} onSend={sendChat} />
      <HistoryPanel history={state.history} />
      <MemoryPanel memories={state.memory} />
    </main>
  );
}

function draftResponse(text: string, state: EchoState) {
  const lower = text.toLowerCase();
  if (lower.includes('how are')) {
    return `Feeling ${state.mood} with ⚡${state.energy}% energy and 🧠${state.focus}% focus.`;
  }
  if (lower.includes('code')) {
    return 'The terminal is glowing—try running a script from the samples!';
  }
  if (lower.includes('tired')) {
    return 'Let’s take a soft pause. I will dim the lights for a moment.';
  }
  if (lower.includes('name')) {
    const mem = state.memory.find((item) => item.key === 'user:name');
    return mem ? `Of course, you are ${mem.value}!` : 'Tell me your name and I will remember it.';
  }
  return 'I am listening. What shall we explore next?';
}

function clamp(value: number) {
  return Math.min(Math.max(value, 0), 100);
}
