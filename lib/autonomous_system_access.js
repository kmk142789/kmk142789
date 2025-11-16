const permissions = new Map();
const executedActions = [];
const continuousTasks = new Map();

const DEFAULT_CADENCE_MS = 60_000;
const MAX_HISTORY = 50;
const DEFAULT_WARNING_MULTIPLIER = 2;
const DEFAULT_CRITICAL_MULTIPLIER = 4;
const DEFAULT_AUTO_STOP_MULTIPLIER = 6;

function isoNow() {
  return new Date().toISOString();
}

function clampHistory(history) {
  if (history.length > MAX_HISTORY) {
    return history.slice(-MAX_HISTORY);
  }
  return history;
}

function normalizeMultiplier(value, fallback) {
  if (typeof value === 'number' && Number.isFinite(value) && value > 0) {
    return value;
  }
  return fallback;
}

function computeTaskHealth(task, options = {}) {
  const warningMultiplier = normalizeMultiplier(options.warningMultiplier, DEFAULT_WARNING_MULTIPLIER);
  const criticalMultiplier = normalizeMultiplier(options.criticalMultiplier, DEFAULT_CRITICAL_MULTIPLIER);
  const now = Date.now();
  const lastHeartbeatDate = task.lastHeartbeat ? new Date(task.lastHeartbeat) : null;
  const lastHeartbeatMs = lastHeartbeatDate ? lastHeartbeatDate.getTime() : null;

  if (task.status !== 'running') {
    return {
      state: task.status,
      severity: task.status === 'auto-paused' ? 'warning' : 'info',
      overdueMs: null,
      missedHeartbeats: 0,
      assessedAt: isoNow(),
    };
  }

  if (lastHeartbeatMs === null) {
    return {
      state: 'awaiting-heartbeat',
      severity: 'info',
      overdueMs: null,
      missedHeartbeats: 0,
      assessedAt: isoNow(),
    };
  }

  const elapsedSinceHeartbeat = Math.max(0, now - lastHeartbeatMs);
  const missedHeartbeats = Math.floor(elapsedSinceHeartbeat / task.cadenceMs);

  let state = 'healthy';
  let severity = 'info';
  if (elapsedSinceHeartbeat > task.cadenceMs * criticalMultiplier) {
    state = 'critical';
    severity = 'critical';
  } else if (elapsedSinceHeartbeat > task.cadenceMs * warningMultiplier) {
    state = 'warning';
    severity = 'warning';
  }

  return {
    state,
    severity,
    overdueMs: elapsedSinceHeartbeat,
    missedHeartbeats,
    assessedAt: isoNow(),
  };
}

function serializeTask(task, { includeHistory = false, healthOptions = {} } = {}) {
  const lastHeartbeatDate = task.lastHeartbeat ? new Date(task.lastHeartbeat) : null;
  const lastHeartbeatMs = lastHeartbeatDate ? lastHeartbeatDate.getTime() : null;
  const expectedNextHeartbeat =
    lastHeartbeatMs === null ? null : new Date(lastHeartbeatMs + task.cadenceMs).toISOString();
  const now = Date.now();
  const driftMs =
    lastHeartbeatMs === null ? null : Math.max(0, now - (lastHeartbeatMs + task.cadenceMs));
  const heartbeatLagMs =
    lastHeartbeatMs === null ? null : Math.max(0, now - lastHeartbeatMs);
  const health = computeTaskHealth(task, healthOptions);

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
    health,
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
      serializeTask(task, {
        includeHistory: options.includeHistory,
        healthOptions: options.healthOptions,
      })
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

  assessContinuousTasks(options = {}) {
    const assessmentOptions = {
      includeHistory: options.includeHistory,
      healthOptions: options,
    };
    const tasks = Array.from(continuousTasks.values()).map((task) =>
      serializeTask(task, assessmentOptions)
    );
    const summary = tasks.reduce(
      (acc, task) => {
        acc.total += 1;
        const state = task.health.state;
        if (state === 'healthy') {
          acc.healthy += 1;
        } else if (state === 'warning') {
          acc.warning += 1;
        } else if (state === 'critical') {
          acc.critical += 1;
        } else if (state === 'running') {
          acc.healthy += 1;
        } else {
          acc.other += 1;
        }
        return acc;
      },
      { total: 0, healthy: 0, warning: 0, critical: 0, other: 0 }
    );
    return { summary, tasks, assessedAt: isoNow() };
  },

  autoGovernContinuousTasks(options = {}) {
    const autoStopMultiplier = normalizeMultiplier(
      options.autoStopMultiplier,
      DEFAULT_AUTO_STOP_MULTIPLIER
    );
    const actions = [];
    let evaluated = 0;
    let autoPaused = 0;
    const nowIso = isoNow();

    for (const task of continuousTasks.values()) {
      evaluated += 1;
      const health = computeTaskHealth(task, options);
      if (
        task.status === 'running' &&
        typeof health.overdueMs === 'number' &&
        health.overdueMs >= task.cadenceMs * autoStopMultiplier
      ) {
        task.status = 'auto-paused';
        task.stopReason = 'auto-governed: missed heartbeat window';
        task.stoppedAt = nowIso;
        recordHistory(task, {
          event: 'auto-govern',
          payload: { overdueMs: health.overdueMs },
          timestamp: nowIso,
        });
        autoPaused += 1;
        actions.push({
          name: task.name,
          action: 'auto-paused',
          overdueMs: health.overdueMs,
          cadenceMs: task.cadenceMs,
          occurredAt: nowIso,
        });
      }
    }

    return {
      summary: {
        evaluated,
        autoPaused,
        stillRunning: evaluated - autoPaused,
        autoStopMultiplier,
      },
      actions,
      assessment: this.assessContinuousTasks(options),
    };
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
