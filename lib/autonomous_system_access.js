const permissions = new Map();
const executedActions = [];

export const autonomousSystemAccess = {
  getSystemAccessState() {
    return {
      grantedPermissions: Array.from(permissions.keys()),
      executedActions: executedActions.slice(-10),
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
