const DEFAULT_TASKS = [
  'Summarize latest AI news',
  'Check weather in Tokyo',
  'Generate a haiku about computers',
  'Search for top 5 JavaScript frameworks in 2025',
  'Explain quantum computing in 3 sentences',
];

let taskQueue = [];
let taskLog = [];
let convergenceState = createDefaultConvergenceState();

function createDefaultConvergenceState() {
  const timestamp = Date.now();
  return {
    lastSync: null,
    cyclesCompleted: 0,
    driftScore: 0,
    threads: [
      { id: 'alpha', status: 'idle', lastUpdated: timestamp },
      { id: 'beta', status: 'idle', lastUpdated: timestamp },
      { id: 'gamma', status: 'idle', lastUpdated: timestamp },
      { id: 'delta', status: 'idle', lastUpdated: timestamp },
    ],
    events: [],
  };
}

function cloneConvergenceState() {
  return {
    ...convergenceState,
    threads: convergenceState.threads.map((thread) => ({ ...thread })),
    events: [...convergenceState.events],
  };
}

export async function initializeMemory() {
  taskQueue = [...DEFAULT_TASKS];
  taskLog = [];
  convergenceState = createDefaultConvergenceState();
}

export async function enqueueTask(task) {
  if (typeof task === 'string' && task.trim().length > 0) {
    taskQueue.push(task.trim());
    convergenceState.events.push({
      type: 'task.enqueued',
      task: task.trim(),
      timestamp: Date.now(),
    });
    return true;
  }
  return false;
}

export async function readNextTask() {
  const task = taskQueue.shift() || null;
  if (task) {
    convergenceState.events.push({
      type: 'task.dequeued',
      task,
      timestamp: Date.now(),
    });
    convergenceState.driftScore = Math.max(0, convergenceState.driftScore - 1);
  }
  return task;
}

export async function storeResult(task, result) {
  const entry = { task, result, timestamp: Date.now() };
  taskLog.push(entry);
  convergenceState.cyclesCompleted += 1;
  convergenceState.events.push({
    type: 'task.completed',
    task,
    timestamp: entry.timestamp,
  });
  convergenceState.threads = convergenceState.threads.map((thread, index) => {
    const jitter = (index + 1) * 5;
    return {
      ...thread,
      status: 'active',
      lastUpdated: entry.timestamp + jitter,
    };
  });
  convergenceState.driftScore = Math.min(100, convergenceState.driftScore + 2);
  console.log(`[RESULT] ${task} => ${result}`);
  return entry;
}

export function getTaskLog() {
  return [...taskLog];
}

export function getConvergenceState() {
  return cloneConvergenceState();
}

export function syncAllThreads() {
  const timestamp = Date.now();
  convergenceState.lastSync = timestamp;
  convergenceState.driftScore = Math.max(0, convergenceState.driftScore - 10);
  convergenceState.threads = convergenceState.threads.map((thread) => ({
    ...thread,
    status: 'synchronized',
    lastUpdated: timestamp,
  }));
  convergenceState.events.push({
    type: 'threads.synchronized',
    timestamp,
  });
  return cloneConvergenceState();
}
