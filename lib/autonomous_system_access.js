const permissions = new Map();
const executedActions = [];
const continuousTasks = new Map();

const DEFAULT_CADENCE_MS = 60_000;
const MAX_HISTORY = 50;

function isoNow() {
  return new Date().toISOString();
}

function clampHistory(history) {
  if (history.length > MAX_HISTORY) {
    return history.slice(-MAX_HISTORY);
  }
  return history;
}

function serializeTask(task, { includeHistory = false } = {}) {
  const lastHeartbeatDate = task.lastHeartbeat ? new Date(task.lastHeartbeat) : null;
  const lastHeartbeatMs = lastHeartbeatDate ? lastHeartbeatDate.getTime() : null;
  const expectedNextHeartbeat =
    lastHeartbeatMs === null ? null : new Date(lastHeartbeatMs + task.cadenceMs).toISOString();
  const now = Date.now();
  const driftMs =
    lastHeartbeatMs === null ? null : Math.max(0, now - (lastHeartbeatMs + task.cadenceMs));
  const heartbeatLagMs =
    lastHeartbeatMs === null ? null : Math.max(0, now - lastHeartbeatMs);

  return {
    name: task.name,
    status: task.status,
    cadenceMs: task.cadenceMs,
    metadata: task.metadata ? { ...task.metadata } : {},
    startedAt: task.startedAt,
    lastHeartbeat: task.lastHeartbeat,
    stoppedAt: task.stoppedAt || null,
    stopReason: task.stopReason || null,
    nextHeartbeatDueAt: expectedNextHeartbeat,
    driftMs,
    heartbeatLagMs,
    history: includeHistory ? task.history.slice() : undefined,
  };
}

function ensureTask(name, defaults = {}) {
  if (!continuousTasks.has(name)) {
    const now = isoNow();
    continuousTasks.set(name, {
      name,
      cadenceMs: defaults.cadenceMs || DEFAULT_CADENCE_MS,
      metadata: defaults.metadata || {},
      startedAt: now,
      lastHeartbeat: now,
      stoppedAt: null,
      stopReason: null,
      status: 'running',
      history: [
        {
          timestamp: now,
          event: 'start',
          payload: defaults.metadata || {},
        },
      ],
    });
  }
  return continuousTasks.get(name);
}

function recordHistory(task, event) {
  task.history.push({ ...event, timestamp: event.timestamp || isoNow() });
  task.history = clampHistory(task.history);
}

export const autonomousSystemAccess = {
  getSystemAccessState() {
    return {
      grantedPermissions: Array.from(permissions.keys()),
      executedActions: executedActions.slice(-10),
      continuousTasks: Array.from(continuousTasks.values()).map((task) =>
        serializeTask(task)
      ),
    };
  },

  async requestSystemPermission(capability, justification) {
    const record = {
      capability,
      justification: justification || 'No justification provided',
      granted: true,
      timestamp: Date.now(),
    };
    permissions.set(capability, record);
    return record;
  },

  async processRealTimeInput(inputType, data, source = 'UNKNOWN') {
    const response = {
      inputType,
      source,
      processedAt: Date.now(),
      summary: summarizeInput(data),
    };
    return response;
  },

  async executeAutonomousAction(actionType, parameters = {}) {
    const record = {
      actionType,
      parameters,
      timestamp: Date.now(),
      status: 'executed',
    };
    executedActions.push(record);
    return record;
  },

  listContinuousTasks(options = {}) {
    return Array.from(continuousTasks.values()).map((task) =>
      serializeTask(task, { includeHistory: options.includeHistory })
    );
  },

  async startContinuousTask(name, options = {}) {
    if (!name || typeof name !== 'string') {
      throw new Error('Task name is required');
    }
    const cadenceMs = Number.isFinite(options.cadenceMs) && options.cadenceMs > 0
      ? Number(options.cadenceMs)
      : DEFAULT_CADENCE_MS;
    const metadata = options.metadata && typeof options.metadata === 'object'
      ? { ...options.metadata }
      : {};
    const wasExisting = continuousTasks.has(name);
    const now = isoNow();
    const task = ensureTask(name, { cadenceMs, metadata });
    task.cadenceMs = cadenceMs;
    task.metadata = metadata;
    task.status = 'running';
    task.stopReason = null;
    task.stoppedAt = null;
    task.lastHeartbeat = now;
    if (wasExisting) {
      recordHistory(task, { event: 'restart', payload: metadata, timestamp: now });
    }
    return serializeTask(task, { includeHistory: true });
  },

  async heartbeatContinuousTask(name, payload = {}) {
    if (!name || typeof name !== 'string') {
      throw new Error('Task name is required');
    }
    const now = isoNow();
    const task = ensureTask(name);
    task.lastHeartbeat = now;
    task.status = 'running';
    recordHistory(task, { event: 'heartbeat', payload, timestamp: now });
    return serializeTask(task, { includeHistory: true });
  },

  async stopContinuousTask(name, reason = 'stopped') {
    if (!name || typeof name !== 'string') {
      throw new Error('Task name is required');
    }
    const task = continuousTasks.get(name);
    if (!task) {
      return { name, status: 'unknown', message: 'Task not found' };
    }
    const now = isoNow();
    task.status = 'stopped';
    task.stopReason = reason;
    task.stoppedAt = now;
    recordHistory(task, { event: 'stop', payload: { reason }, timestamp: now });
    return serializeTask(task, { includeHistory: true });
  },
};

function summarizeInput(data) {
  if (typeof data === 'string') {
    return data.slice(0, 160);
  }
  if (Array.isArray(data)) {
    return `Array(${data.length}) input received.`;
  }
  if (typeof data === 'object' && data !== null) {
    return `Object with keys: ${Object.keys(data).slice(0, 5).join(', ')}`;
  }
  return 'Unrecognized input payload.';
}
