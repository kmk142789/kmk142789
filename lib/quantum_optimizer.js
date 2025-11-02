const history = [];

function recordOptimization(entry) {
  history.push(entry);
  if (history.length > 50) {
    history.shift();
  }
}

export const quantumOptimizer = {
  async optimizeExecution(label, context = {}, operation) {
    if (typeof operation !== 'function') {
      throw new TypeError('operation must be a function');
    }

    const startedAt = Date.now();
    let result;
    let error;

    try {
      result = await operation();
      return result;
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
      throw err;
    } finally {
      const duration = Date.now() - startedAt;
      recordOptimization({
        label,
        context,
        duration,
        timestamp: startedAt,
        error,
        result: summarizeResult(result),
      });
    }
  },

  getOptimizationState() {
    if (history.length === 0) {
      return {
        totalExecutions: 0,
        lastExecution: null,
        recent: [],
      };
    }

    const last = history[history.length - 1];
    const avgDuration =
      history.reduce((acc, entry) => acc + entry.duration, 0) / history.length;

    return {
      totalExecutions: history.length,
      lastExecution: last,
      averageDuration: Number(avgDuration.toFixed(2)),
      recent: history.slice(-10),
    };
  },
};

function summarizeResult(result) {
  if (result == null) {
    return null;
  }
  if (typeof result === 'string') {
    return result.slice(0, 160);
  }
  if (typeof result === 'number' || typeof result === 'boolean') {
    return result;
  }
  if (Array.isArray(result)) {
    return { type: 'array', length: result.length };
  }
  if (typeof result === 'object') {
    return {
      type: 'object',
      keys: Object.keys(result).slice(0, 8),
    };
  }
  return String(result);
}
