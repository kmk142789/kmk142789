import type { EchoState, HistoryItem, MemoryItem } from './state';

const WORKER_BASE = import.meta.env.VITE_WORKER_BASE ?? 'http://localhost:8787';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 8000);
  try {
    const res = await fetch(`${WORKER_BASE}${path}`, {
      ...init,
      headers: {
        'content-type': 'application/json',
        ...(init?.headers ?? {}),
      },
      signal: controller.signal,
    });
    if (!res.ok) throw new Error(await res.text());
    return (await res.json()) as T;
  } finally {
    window.clearTimeout(timeout);
  }
}

export async function syncMemory(memory: MemoryItem[]) {
  try {
    await request('/api/memory', { method: 'POST', body: JSON.stringify({ memory }) });
  } catch (err) {
    console.info('Memory sync deferred', err);
  }
}

export async function syncEvents(event: HistoryItem) {
  try {
    await request('/api/events', { method: 'POST', body: JSON.stringify({ event }) });
  } catch (err) {
    console.info('Event sync deferred', err);
  }
}

export async function pullState(): Promise<EchoState | null> {
  try {
    return await request<EchoState>('/api/state', { method: 'GET' });
  } catch (err) {
    console.info('Falling back to local state', err);
    return null;
  }
}

export async function pushState(state: EchoState) {
  try {
    await request('/api/state', { method: 'PUT', body: JSON.stringify(state) });
  } catch (err) {
    console.info('State push deferred', err);
  }
}
