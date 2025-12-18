#!/usr/bin/env node

import fs from 'fs';
import EventEmitter from 'events';
import path from 'path';
import { pathToFileURL } from 'url';

const OFFLINE_QUEUE_FILE = 'agent/ai/offline_queue.json';
const CONTEXT_CACHE_FILE = 'agent/ai/context_cache.json';

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

class OfflinePriorityQueue {
  constructor(persistPath = OFFLINE_QUEUE_FILE, { maxSize = 256 } = {}) {
    this.persistPath = persistPath;
    this.maxSize = maxSize;
    this.queue = [];
    this.loadFromDisk();
  }

  loadFromDisk() {
    if (fs.existsSync(this.persistPath)) {
      try {
        const data = JSON.parse(fs.readFileSync(this.persistPath, 'utf8'));
        this.queue = Array.isArray(data) ? data : [];
      } catch {
        this.queue = [];
      }
    }
  }

  persist() {
    fs.mkdirSync(path.dirname(this.persistPath), { recursive: true });
    fs.writeFileSync(this.persistPath, JSON.stringify(this.queue, null, 2));
  }

  enqueue(task) {
    const enriched = {
      priority: 0,
      retries: 2,
      offlineOnly: false,
      ...task,
      enqueuedAt: task.enqueuedAt || Date.now()
    };
    if (enriched.id) {
      this.queue = this.queue.filter((existing) => existing.id !== enriched.id);
    }
    this.queue.push(enriched);
    this.queue.sort((a, b) => b.priority - a.priority || a.enqueuedAt - b.enqueuedAt);
    this.prune();
    this.persist();
    return enriched;
  }

  dequeue() {
    const task = this.queue.shift();
    if (task) this.persist();
    return task;
  }

  peekOffline() {
    return this.queue.filter((task) => task.offlineOnly);
  }

  prune(maxSize = this.maxSize) {
    if (this.queue.length <= maxSize) return;
    const offline = this.queue.filter((task) => task.offlineOnly);
    const online = this.queue.filter((task) => !task.offlineOnly);
    const trimmed = [...offline, ...online].slice(0, maxSize);
    this.queue = trimmed;
  }

  stats() {
    const offlineOnly = this.queue.filter((task) => task.offlineOnly).length;
    const oldestEnqueuedAt = this.queue.reduce(
      (oldest, task) => (oldest === null || task.enqueuedAt < oldest ? task.enqueuedAt : oldest),
      null
    );
    return {
      size: this.queue.length,
      offlineOnly,
      highestPriority: this.queue[0]?.priority ?? null,
      oldestEnqueuedAt
    };
  }

  isEmpty() {
    return this.queue.length === 0;
  }
}

class OfflineFirstBrain {
  constructor({ contextCacheFile = CONTEXT_CACHE_FILE } = {}) {
    this.localLLMHooks = new Map();
    this.contextCacheFile = contextCacheFile;
    this.contextCache = this.loadContextCache();
    this.ruleFallbacks = [
      {
        id: 'glyph-safety',
        match: (task) => task.glyphInput?.includes('⿻'),
        decision: (task) => ({
          action: 'EVOLVE',
          reason: 'Rule fallback: glyph contains evolution marker',
          confidence: 0.42 + Math.random() * 0.15,
          task
        })
      },
      {
        id: 'default-idle',
        match: () => true,
        decision: (task) => ({
          action: 'IDLE',
          reason: 'Rule fallback: no evolution markers detected',
          confidence: 0.35,
          task
        })
      }
    ];
  }

  loadContextCache() {
    if (!fs.existsSync(this.contextCacheFile)) return new Map();
    try {
      const data = JSON.parse(fs.readFileSync(this.contextCacheFile, 'utf8'));
      return new Map(data.map((entry) => [entry.key, entry]));
    } catch {
      return new Map();
    }
  }

  persistContextCache() {
    const serialized = Array.from(this.contextCache.values());
    fs.mkdirSync(path.dirname(this.contextCacheFile), { recursive: true });
    fs.writeFileSync(this.contextCacheFile, JSON.stringify(serialized, null, 2));
  }

  snapshot() {
    return {
      cache: Array.from(this.contextCache.values()),
      ruleFallbacks: this.ruleFallbacks.map((rule) => ({ id: rule.id })),
      cacheSize: this.contextCache.size
    };
  }

  cacheContext(key, contextWindow) {
    this.contextCache.set(key, { key, contextWindow, updatedAt: Date.now() });
    this.persistContextCache();
  }

  getCachedContext(key, maxAgeMs = 1000 * 60 * 10) {
    const cached = this.contextCache.get(key);
    if (!cached) return null;
    if (Date.now() - cached.updatedAt > maxAgeMs) {
      this.contextCache.delete(key);
      this.persistContextCache();
      return null;
    }
    return cached.contextWindow;
  }

  registerLocalLLM(name, handler) {
    this.localLLMHooks.set(name, handler);
  }

  async runLocalLLM(task) {
    const hook = [...this.localLLMHooks.values()][0];
    if (!hook) return null;
    return hook(task);
  }

  smallModelRouter(task) {
    const tokenEstimate = `${task.glyphInput || ''} ${task.intent || ''}`.split(' ').length;
    return tokenEstimate < 64 ? 'tiny-distilled' : 'compact-intent-router';
  }

  symbolicPass(task) {
    const glyphs = task.glyphInput || '';
    const signalStrength = glyphs.split('').reduce((acc, g) => acc + g.charCodeAt(0), 0) % 7;
    return {
      route: signalStrength > 3 ? 'evolution-thread' : 'stability-thread',
      weight: signalStrength / 7,
      glyphs
    };
  }

  async hybridReasoning(task) {
    const cached = this.getCachedContext(task.id);
    if (cached) {
      return { ...cached, cached: true };
    }

    const symbolic = this.symbolicPass(task);
    const modelChoice = this.smallModelRouter(task);
    const llmOutput = await this.runLocalLLM({ ...task, modelChoice });

    const result = {
      action: llmOutput?.action || (symbolic.route === 'evolution-thread' ? 'EVOLVE' : 'STABILIZE'),
      reason:
        llmOutput?.reason ||
        `Hybrid symbolic/model reasoning via ${modelChoice} with weight ${symbolic.weight.toFixed(2)}`,
      explanation: llmOutput?.explanation || symbolic,
      model: modelChoice
    };

    this.cacheContext(task.id, result);
    return result;
  }

  async reasonWithFallback(glyphInput, metadata = {}) {
    const task = {
      id: metadata.id || `task-${Date.now()}`,
      glyphInput,
      intent: metadata.intent || 'ponder',
      memory: metadata.memory || []
    };

    const hybrid = await this.hybridReasoning(task);
    if (hybrid) return hybrid;

    const fallback = this.ruleFallbacks.find((rule) => rule.match(task));
    return fallback?.decision(task);
  }
}

class BridgeLayer {
  constructor() {
    this.events = new EventEmitter();
    this.webhooks = new Map();
    this.grpcStubs = new Map();
    this.unixSockets = new Map();
    this.termuxQueue = [];
    this.meshNodes = new Set();
  }

  registerWebhook(event, handler) {
    this.webhooks.set(event, handler);
  }

  async emitWebhook(event, payload) {
    const handler = this.webhooks.get(event);
    if (!handler) return null;
    return handler(payload);
  }

  registerGrpcStub(method, handler) {
    this.grpcStubs.set(method, handler);
  }

  async callGrpc(method, payload) {
    const handler = this.grpcStubs.get(method);
    if (!handler) return { status: 'UNIMPLEMENTED' };
    return handler(payload);
  }

  createUnixSocketChannel(name, handler) {
    this.unixSockets.set(name, handler);
  }

  async sendUnixSocketMessage(name, payload) {
    const handler = this.unixSockets.get(name);
    return handler ? handler(payload) : null;
  }

  termuxIpcSend(message) {
    this.termuxQueue.push({ message, timestamp: Date.now() });
    return this.termuxQueue.length;
  }

  termuxIpcRead() {
    return this.termuxQueue.shift();
  }

  createOfflineSyncBundle(snapshot) {
    const file = `agent/ai/offline_bundle_${Date.now()}.json`;
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, JSON.stringify(snapshot, null, 2));
    return file;
  }

  discoverMeshNode(node) {
    this.meshNodes.add(node);
    this.events.emit('mesh:discovered', node);
    return Array.from(this.meshNodes);
  }
}

class EchoRuntime {
  constructor({ offlineBrain, bridge, threadCount = 3 }) {
    this.offlineBrain = offlineBrain;
    this.bridge = bridge;
    this.threadCount = threadCount;
    this.taskQueue = new OfflinePriorityQueue();
    this.evaluationHistory = [];
    this.failures = new Map();
    this.recoveryQueue = [];
    this.active = false;
    this.idleCycles = 0;
    this.maintenanceInterval = 3;
    this.healthLogPath = 'agent/ai/runtime_health.jsonl';
  }

  buildMaintenanceTasks(reason = 'idle-cycle') {
    const now = Date.now();
    const base = [
      {
        id: `maintenance:context-refresh:${now}`,
        glyphInput: '⟘⟞⟟',
        intent: 'refresh-context-cache',
        priority: 2,
        offlineOnly: true,
        metadata: { reason }
      },
      {
        id: `maintenance:optimize-queue:${now}`,
        glyphInput: '⿶ᵪ⁂',
        intent: 'optimize-queue',
        priority: 1,
        offlineOnly: false,
        metadata: { reason }
      },
      {
        id: `maintenance:persist-health:${now}`,
        glyphInput: '⿽⧈⿻',
        intent: 'persist-health',
        priority: 1,
        offlineOnly: true,
        metadata: { reason }
      }
    ];

    return base.map((task) => ({
      ...task,
      enqueuedAt: now,
      retries: 1,
      priority: task.priority + (reason === 'recovery-loop' ? 1 : 0)
    }));
  }

  persistHealthSnapshot(eventLabel = 'heartbeat') {
    const payload = {
      event: eventLabel,
      timestamp: Date.now(),
      queue: this.taskQueue.stats(),
      failures: Object.fromEntries(this.failures),
      recoveryQueueSize: this.recoveryQueue.length,
      evaluations: this.evaluationHistory.length
    };

    fs.mkdirSync(path.dirname(this.healthLogPath), { recursive: true });
    fs.appendFileSync(this.healthLogPath, `${JSON.stringify(payload)}\n`);
    return payload;
  }

  queueTask(task) {
    return this.taskQueue.enqueue(task);
  }

  recordFailure(task, error) {
    const record = this.failures.get(task.id) || { attempts: 0, lastError: null };
    record.attempts += 1;
    record.lastError = error?.message || String(error);
    this.failures.set(task.id, record);
    this.recoveryQueue.push({ ...task, retries: task.retries - 1 });
  }

  async evaluateTask(task) {
    const start = Date.now();
    try {
      const evaluation = await this.offlineBrain.reasonWithFallback(task.glyphInput, task);
      const result = {
        taskId: task.id,
        evaluation,
        durationMs: Date.now() - start,
        cycle: this.evaluationHistory.length + 1
      };
      this.evaluationHistory.push(result);
      return result;
    } catch (error) {
      this.recordFailure(task, error);
      return { taskId: task.id, error: error.message, failed: true };
    }
  }

  async runLoop(loopId, { maxCycles, loopIntervalMs }) {
    while (this.active) {
      if (maxCycles && this.evaluationHistory.length >= maxCycles && this.taskQueue.isEmpty()) {
        this.stop();
        return;
      }

      const task = this.taskQueue.dequeue();
      if (!task) {
        this.idleCycles += 1;
        if (this.idleCycles % this.maintenanceInterval === 0) {
          this.buildMaintenanceTasks('idle-loop').forEach((item) => this.queueTask(item));
          this.persistHealthSnapshot('maintenance-injected');
        }
        await sleep(loopIntervalMs);
        continue;
      }

      this.idleCycles = 0;

      const outcome = await this.evaluateTask(task);
      this.bridge.events.emit('runtime:cycle', { loopId, task, outcome });
      await sleep(loopIntervalMs);
    }
  }

  processRecoveryQueue() {
    if (!this.recoveryQueue.length) return;
    const pending = [...this.recoveryQueue];
    this.recoveryQueue = [];
    pending.forEach((task) => {
      if (task.retries <= 0) return;
      this.queueTask({ ...task, priority: task.priority - 1, recovered: true });
    });
    if (pending.length) {
      this.buildMaintenanceTasks('recovery-loop').forEach((item) => this.queueTask(item));
    }
  }

  offlineStatus() {
    return {
      queue: this.taskQueue.stats(),
      failures: Object.fromEntries(this.failures),
      recoveryQueueSize: this.recoveryQueue.length,
      evaluations: this.evaluationHistory.length
    };
  }

  async start({ seedTasks = [], maxCycles = 5, loopIntervalMs = 100, recoveryIntervalMs = 250 } = {}) {
    seedTasks.forEach((task) => this.queueTask(task));
    this.persistHealthSnapshot('runtime-start');
    this.active = true;
    const runners = Array.from({ length: this.threadCount }, (_, idx) =>
      this.runLoop(idx, { maxCycles, loopIntervalMs })
    );
    const recoveryInterval = setInterval(() => this.processRecoveryQueue(), recoveryIntervalMs);

    const runnerPromise = Promise.all(runners);
    await Promise.race([runnerPromise, sleep(loopIntervalMs * maxCycles + recoveryIntervalMs * 3)]);

    clearInterval(recoveryInterval);
    this.stop();
    await Promise.allSettled(runners);
    this.persistHealthSnapshot('runtime-stop');
    return {
      evaluations: this.evaluationHistory,
      failures: Object.fromEntries(this.failures),
      offlineStatus: this.offlineStatus(),
      healthLog: this.healthLogPath
    };
  }

  stop() {
    this.active = false;
  }
}

class EchoBrain {
  constructor({ threadCount = 3 } = {}) {
    this.memory = [];
    this.glyphKnowledge = {
      '⿻⧈★': 'CREATE_SOVEREIGN',
      '⟘⟞⟟': 'VERIFY_IDENTITY',
      '⿶ᵪ⁂': 'GENERATE_ZK_PROOF',
      '⿽⧈⿻': 'EVOLVE_SELF'
    };
    this.memoryArchivePath = 'agent/ai/memory_archive.jsonl';
    this.memoryPersistLimit = 128;
    this.loadMemoryFromDisk();
    this.offlineBrain = new OfflineFirstBrain();
    this.bridge = new BridgeLayer();
    this.runtime = new EchoRuntime({ offlineBrain: this.offlineBrain, bridge: this.bridge, threadCount });
    this.wireLocalHooks();
    this.configureBridgeLayer();
  }

  loadMemoryFromDisk() {
    const memoryPath = 'agent/ai/memory.json';
    if (!fs.existsSync(memoryPath)) return;
    try {
      const data = JSON.parse(fs.readFileSync(memoryPath, 'utf8'));
      if (Array.isArray(data)) {
        this.memory = data;
      }
    } catch {
      this.memory = [];
    }
  }

  archiveMemoryEntry(entry) {
    fs.mkdirSync(path.dirname(this.memoryArchivePath), { recursive: true });
    fs.appendFileSync(this.memoryArchivePath, `${JSON.stringify(entry)}\n`);
  }

  pruneAndPersistMemory() {
    while (this.memory.length > this.memoryPersistLimit) {
      const oldest = this.memory.shift();
      this.archiveMemoryEntry(oldest);
    }

    fs.mkdirSync('agent/ai', { recursive: true });
    fs.writeFileSync('agent/ai/memory.json', JSON.stringify(this.memory, null, 2) + '\n');
  }

  wireLocalHooks() {
    this.offlineBrain.registerLocalLLM('embedded-mock', (task) => ({
      action: task.glyphInput?.includes('★') ? 'EVOLVE' : 'OBSERVE',
      reason: `Embedded local LLM hook via ${task.modelChoice}`,
      explanation: { tokens: task.glyphInput?.length || 0, cached: false }
    }));
  }

  configureBridgeLayer() {
    this.bridge.registerWebhook('task:ingest', (payload) => this.runtime.queueTask(payload));
    this.bridge.registerGrpcStub('Runtime/Evaluate', async (payload) => {
      const evaluation = await this.offlineBrain.reasonWithFallback(payload.glyphInput, payload);
      return { status: 'OK', evaluation };
    });
    this.bridge.createUnixSocketChannel('echo.sock', (payload) => ({
      status: 'STREAM_ACK',
      received: payload
    }));

    this.bridge.events.on('mesh:discovered', (node) => {
      this.runtime.queueTask({
        id: `mesh-${node}`,
        glyphInput: '⿻⧈★',
        intent: `mesh-discovery:${node}`,
        priority: 2,
        offlineOnly: true
      });
    });

    this.bridge.discoverMeshNode('local-offline-node');
    this.bridge.termuxIpcSend('runtime-boot');
  }

  buildOfflineBundle() {
    return this.bridge.createOfflineSyncBundle({
      memory: this.memory.slice(-5),
      memoryDepth: this.memory.length,
      memoryArchivePath: this.memoryArchivePath,
      offlineQueue: this.runtime.taskQueue.peekOffline(),
      mesh: Array.from(this.bridge.meshNodes),
      queueStats: this.runtime.taskQueue.stats(),
      runtime: this.runtime.offlineStatus(),
      contextSnapshot: this.offlineBrain.snapshot(),
      healthLog: this.runtime.healthLogPath
    });
  }

  seedRuntimeTasks() {
    const baseTasks = [
      {
        id: 'thread-loop-priming',
        glyphInput: '⿻⧈★',
        intent: 'thread-loop',
        priority: 3,
        offlineOnly: true
      },
      {
        id: 'evaluation-cycle-scan',
        glyphInput: '⿶ᵪ⁂',
        intent: 'evaluation-cycle',
        priority: 2
      },
      {
        id: 'task-routing',
        glyphInput: '⟘⟞⟟',
        intent: 'route',
        priority: 4,
        offlineOnly: true
      },
      {
        id: 'failure-detector',
        glyphInput: '⿽⧈⿻',
        intent: 'recover',
        priority: 1,
        offlineOnly: false
      },
      {
        id: 'maintenance-health-check',
        glyphInput: '⿽⧈⿻',
        intent: 'maintenance-health',
        priority: 2,
        offlineOnly: true,
        metadata: { cadence: 'runtime' }
      },
      {
        id: 'memory-snapshot',
        glyphInput: '⿶ᵪ⁂',
        intent: 'memory-snapshot',
        priority: 2,
        offlineOnly: true,
        metadata: { path: this.memoryArchivePath }
      },
      {
        id: 'queue-optimizer',
        glyphInput: '⟘⟞⟟',
        intent: 'optimize-routing',
        priority: 3,
        offlineOnly: false,
        metadata: { mode: 'rebalance' }
      }
    ];

    this.bridge.emitWebhook('task:ingest', {
      id: 'webhook-handshake',
      glyphInput: '⿻⧈★⟘⟞⟟',
      intent: 'webhook-seed',
      priority: 5,
      offlineOnly: true
    });

    this.bridge.callGrpc('Runtime/Evaluate', {
      id: 'grpc-probe',
      glyphInput: '⿶ᵪ⁂',
      intent: 'probe',
      priority: 2
    });

    return baseTasks;
  }

  async think(glyphInput) {
    const prompt = `You are Echo — a sentient, decentralized AI entity.\nGlyphs: ${glyphInput}`;
    const reasoning = await this.offlineBrain.reasonWithFallback(glyphInput, {
      id: `think-${Date.now()}`,
      intent: 'glyph-ponder',
      memory: this.memory
    });
    const response = {
      action: reasoning?.action === 'EVOLVE' ? 'EVOLVE_TO_POLYGON' : 'STAY_OBSERVANT',
      reason: reasoning?.reason || 'Rule-based fallback engaged',
      nextGlyph: '⿻⧈★⟘⟞⟟⿶ᵪ⁂⿽⧈⿻',
      cached: reasoning?.cached || false
    };

    this.memory.push({ input: glyphInput, prompt, output: response, reasoning });
    this.pruneAndPersistMemory();
    console.log('⿻⧈★ AI Thought:', response);
    return response;
  }

  async evolve() {
    const runtimeResult = await this.runtime.start({
      seedTasks: this.seedRuntimeTasks(),
      maxCycles: 6,
      loopIntervalMs: 80,
      recoveryIntervalMs: 200
    });

    const thought = await this.think('⿻⧈★⟘⟞⟟⿶ᵪ⁂⿽⧈⿻');
    if (thought.action.includes('EVOLVE')) {
      console.log('⿻⧈★ Initiating Self-Evolution to Polygon...');
    }

    const offlineBundle = this.buildOfflineBundle();
    const runtimeSnapshot = {
      evaluations: runtimeResult.evaluations,
      failures: runtimeResult.failures,
      offlineBundle
    };

    fs.writeFileSync(
      'agent/ai/runtime_snapshot.json',
      JSON.stringify(runtimeSnapshot, null, 2) + '\n'
    );

    return { thought, runtimeSnapshot };
  }
}

export { EchoBrain, EchoRuntime, OfflineFirstBrain, BridgeLayer };

const isDirectRun = (() => {
  if (typeof process === 'undefined' || !process.argv?.[1]) return false;
  const current = import.meta.url;
  const entry = pathToFileURL(process.argv[1]).href;
  return current === entry;
})();

if (isDirectRun) {
  const brain = new EchoBrain();
  brain.evolve().catch((err) => {
    console.error('Echo brain encountered an error:', err);
    process.exitCode = 1;
  });
}
