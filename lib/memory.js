let taskQueue = [];
let taskLog = [];

const DEFAULT_TASKS = [
  'Summarize latest AI news',
  'Check weather in Tokyo',
  'Generate a haiku about computers',
  'Search for top 5 JavaScript frameworks in 2025',
  'Explain quantum computing in 3 sentences',
];

export async function initializeMemory() {
  taskQueue = [...DEFAULT_TASKS];
  taskLog = [];
}

export async function enqueueTask(task) {
  if (typeof task === 'string' && task.trim().length > 0) {
    taskQueue.push(task.trim());
    return true;
  }
  return false;
}

export async function readNextTask() {
  return taskQueue.shift() || null;
}

export async function storeResult(task, result) {
  const entry = { task, result, timestamp: Date.now() };
  taskLog.push(entry);
  console.log(`[RESULT] ${task} => ${result}`);
  return entry;
}

export function getTaskLog() {
  return [...taskLog];
}
