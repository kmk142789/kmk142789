import { getTaskLog } from './memory.js';

function extractTopics(task) {
  if (!task) {
    return [];
  }
  return task
    .toLowerCase()
    .split(/[^a-z0-9]+/g)
    .filter(Boolean)
    .filter((token) => token.length > 3);
}

function tally(entries) {
  const counts = new Map();
  for (const entry of entries) {
    counts.set(entry, (counts.get(entry) || 0) + 1);
  }
  return counts;
}

export const predictiveAnalytics = {
  async generateInsights() {
    const log = getTaskLog();
    const topics = tally(log.flatMap((entry) => extractTopics(entry.task)));
    const sortedTopics = [...topics.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5);

    return {
      totalTasks: log.length,
      uniqueTopics: topics.size,
      topTopics: sortedTopics.map(([topic, count]) => ({ topic, count })),
      lastUpdated: log.length > 0 ? log[log.length - 1].timestamp : null,
    };
  },

  async predictNextTasks() {
    const log = getTaskLog();
    if (log.length === 0) {
      return [
        { task: 'Review system telemetry', confidence: 0.6 },
        { task: 'Initiate mythic narrative loop', confidence: 0.55 },
      ];
    }

    const topics = tally(log.flatMap((entry) => extractTopics(entry.task)));
    const predictions = [];

    for (const [topic, count] of topics.entries()) {
      if (count < 2) {
        continue;
      }
      const confidence = Math.min(0.95, 0.4 + count * 0.1);
      predictions.push({
        task: `Expand analysis on ${topic}`,
        confidence: Number(confidence.toFixed(2)),
      });
    }

    if (predictions.length === 0) {
      predictions.push({ task: 'Explore emerging pattern clusters', confidence: 0.58 });
    }

    return predictions.slice(0, 5);
  },
};
