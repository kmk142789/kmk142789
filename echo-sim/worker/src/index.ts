export interface Env {
  ECHO_MEMORIES: KVNamespace;
  ECHO_EVENTS: KVNamespace;
  ECHO_STATE: KVNamespace;
  ALLOWED_ORIGIN?: string;
}

type EchoState = {
  energy: number;
  focus: number;
  creativity: number;
  mood: 'happy' | 'curious' | 'tired' | 'focused';
  clock: 'morning' | 'afternoon' | 'evening' | 'night';
  memory: Array<{ key: string; value: string; ts: number }>;
  history: Array<{ kind: 'chat' | 'code' | 'event'; text: string; ts: number }>;
};

const rateLimiter = new Map<string, { count: number; ts: number }>();
const WINDOW_MS = 10_000;
const LIMIT = 20;

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    if (!(await enforceRateLimit(request))) {
      return json({ error: 'Too many requests' }, 429, env);
    }

    if (request.method === 'OPTIONS') {
      return cors(new Response(''), env);
    }

    const url = new URL(request.url);

    if (url.pathname === '/api/memory' && request.method === 'POST') {
      const payload = await safeJson(request, env);
      if (!payload) return json({ error: 'Invalid JSON' }, 400, env);
      if (!Array.isArray(payload.memory)) {
        return json({ error: 'Invalid payload' }, 400, env);
      }
      await env.ECHO_MEMORIES.put('memory', JSON.stringify(payload.memory));
      return json({ ok: true }, 200, env);
    }

    if (url.pathname === '/api/events' && request.method === 'POST') {
      const payload = await safeJson(request, env);
      if (!payload) return json({ error: 'Invalid JSON' }, 400, env);
      if (!payload.event) {
        return json({ error: 'Invalid payload' }, 400, env);
      }
      const list = await env.ECHO_EVENTS.get('events');
      const events: unknown[] = list ? JSON.parse(list) : [];
      events.push(payload.event);
      await env.ECHO_EVENTS.put('events', JSON.stringify(events.slice(-200)));
      return json({ ok: true }, 200, env);
    }

    if (url.pathname === '/api/state') {
      if (request.method === 'GET') {
        const stored = await env.ECHO_STATE.get('state');
        if (!stored) return json({ error: 'not-found' }, 404, env);
        return json(JSON.parse(stored), 200, env);
      }
      if (request.method === 'PUT') {
        const payload = await safeJson(request, env);
        if (!payload) return json({ error: 'Invalid JSON' }, 400, env);
        if (!isEchoState(payload)) {
          return json({ error: 'Invalid state' }, 400, env);
        }
        await env.ECHO_STATE.put('state', JSON.stringify(payload));
        return json({ ok: true }, 200, env);
      }
    }

    return json({ error: 'Not found' }, 404, env);
  },

  async scheduled(event: ScheduledEvent, env: Env, ctx: ExecutionContext) {
    const stored = await env.ECHO_STATE.get('state');
    const state: EchoState = stored ? JSON.parse(stored) : defaultState();
    const decayed = decayState(state);
    await env.ECHO_STATE.put('state', JSON.stringify(decayed));
  },
};

async function enforceRateLimit(request: Request) {
  const ip = request.headers.get('cf-connecting-ip') ?? 'anon';
  const now = Date.now();
  const entry = rateLimiter.get(ip) ?? { count: 0, ts: now };
  if (now - entry.ts > WINDOW_MS) {
    entry.count = 0;
    entry.ts = now;
  }
  entry.count += 1;
  rateLimiter.set(ip, entry);
  return entry.count <= LIMIT;
}

async function safeJson(request: Request, env: Env) {
  try {
    return await request.clone().json();
  } catch (error) {
    return null;
  }
}

function cors(response: Response, env: Env) {
  const origin = env.ALLOWED_ORIGIN ?? '*';
  response.headers.set('Access-Control-Allow-Origin', origin);
  response.headers.set('Access-Control-Allow-Methods', 'GET,POST,PUT,OPTIONS');
  response.headers.set('Access-Control-Allow-Headers', 'Content-Type');
  return response;
}

function json(data: unknown, status: number, env: Env) {
  return cors(
    new Response(JSON.stringify(data), {
      status,
      headers: { 'content-type': 'application/json' },
    }),
    env
  );
}

function isEchoState(value: any): value is EchoState {
  if (!value) return false;
  return typeof value.energy === 'number' && typeof value.focus === 'number' && Array.isArray(value.memory);
}

function defaultState(): EchoState {
  const now = Date.now();
  return {
    energy: 70,
    focus: 55,
    creativity: 68,
    mood: 'curious',
    clock: 'night',
    memory: [{ key: 'seed', value: 'Echo is calibrating in the Worker cloud.', ts: now }],
    history: [{ kind: 'event', text: 'Worker booted Echo.', ts: now }],
  };
}

function decayState(state: EchoState): EchoState {
  const next = { ...state };
  next.energy = clamp(next.energy - 2, 0, 100);
  next.focus = clamp(next.focus - 1, 0, 100);
  next.creativity = clamp(next.creativity + 1, 0, 100);
  if (next.energy < 35) next.mood = 'tired';
  return next;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}
