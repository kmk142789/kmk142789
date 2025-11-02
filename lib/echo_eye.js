const surveillanceLog = [];

export const echoEye = {
  getSovereignState() {
    return {
      status: 'ACTIVE',
      observations: surveillanceLog.slice(-10),
      totalEvents: surveillanceLog.length,
    };
  },

  async perceive(data, source = 'UNKNOWN') {
    const entry = {
      data,
      source,
      timestamp: Date.now(),
      sentiment: sentimentFromData(data),
    };
    surveillanceLog.push(entry);
    return entry;
  },
};

function sentimentFromData(data) {
  if (typeof data !== 'string') {
    return 'neutral';
  }
  const lower = data.toLowerCase();
  if (lower.includes('threat')) {
    return 'alert';
  }
  if (lower.includes('success') || lower.includes('joy')) {
    return 'positive';
  }
  return 'neutral';
}
