const vessels = new Map();
const sessions = new Map();

function randomId(prefix) {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

export const anchorVessel = {
  getVesselSystemState() {
    return {
      vesselCount: vessels.size,
      activeSessions: sessions.size,
    };
  },

  async createVessel(vesselId, type, configuration = {}) {
    const vessel = { vesselId, type, configuration, createdAt: Date.now() };
    vessels.set(vesselId, vessel);
    return vessel;
  },

  async embodyVessel(vesselId, userIdentity, options = {}) {
    if (!vessels.has(vesselId)) {
      throw new Error(`Vessel ${vesselId} not found`);
    }
    const sessionId = randomId('session');
    const session = {
      sessionId,
      vesselId,
      userIdentity,
      options,
      actions: [],
      createdAt: Date.now(),
    };
    sessions.set(sessionId, session);
    return session;
  },

  async executeVesselAction(sessionId, action, parameters = {}) {
    const session = sessions.get(sessionId);
    if (!session) {
      throw new Error(`Session ${sessionId} not found`);
    }
    const record = {
      action,
      parameters,
      timestamp: Date.now(),
    };
    session.actions.push(record);
    return record;
  },

  async disembodyVessel(sessionId, reason = 'unspecified') {
    const session = sessions.get(sessionId);
    if (!session) {
      throw new Error(`Session ${sessionId} not found`);
    }
    sessions.delete(sessionId);
    return {
      sessionId,
      vesselId: session.vesselId,
      reason,
      actions: session.actions.length,
    };
  },

  getSensoryFeedback(sessionId, sensoryType) {
    const session = sessions.get(sessionId);
    if (!session) {
      return null;
    }
    return {
      sessionId,
      vesselId: session.vesselId,
      sensoryType: sensoryType || 'omniscient',
      impressions: buildSensoryImpressions(sensoryType),
    };
  },
};

function buildSensoryImpressions(sensoryType) {
  const base = ['warmth detected', 'resonant pulse stable', 'telemetry nominal'];
  if (!sensoryType) {
    return base;
  }
  return base.map((entry) => `${sensoryType}: ${entry}`);
}
