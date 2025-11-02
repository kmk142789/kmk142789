import { getTaskLog } from './memory.js';

let initialized = false;

const defaultAgents = [
  { id: 'aurora', specialty: 'creative-strategy', confidence: 0.82 },
  { id: 'zenith', specialty: 'systems-analysis', confidence: 0.76 },
  { id: 'pulse', specialty: 'narrative-synthesis', confidence: 0.71 },
];

const agentSwarm = {
  agents: new Map(),
  async processWithSwarm(task) {
    if (!task || typeof task !== 'string') {
      throw new TypeError('Task must be a non-empty string.');
    }

    const normalized = task.trim();
    if (!normalized) {
      throw new TypeError('Task must be a non-empty string.');
    }

    initializeAgentMap();

    const taskLog = getTaskLog();
    const contextWindow = taskLog.slice(-5).map((entry) => entry.task);
    const evaluations = [];

    for (const [agentId, agent] of agentSwarm.agents.entries()) {
      const weight = agent.confidence + normalized.length / 100;
      const recommendation = {
        agentId,
        specialty: agent.specialty,
        confidence: Number(Math.min(1, weight).toFixed(2)),
        insight: buildInsight(agent, normalized, contextWindow),
      };
      evaluations.push(recommendation);
    }

    return {
      task: normalized,
      consensus: Number(
        (evaluations.reduce((acc, entry) => acc + entry.confidence, 0) /
          Math.max(evaluations.length, 1)).toFixed(2)
      ),
      strategies: evaluations,
    };
  },
};

const knowledgeGraph = {
  nodes: new Map(),
  connections: new Set(),
  async queryKnowledge(query) {
    const normalized = typeof query === 'string' ? query.trim().toLowerCase() : '';
    if (!normalized) {
      return [];
    }

    const matches = [];
    for (const [concept, data] of knowledgeGraph.nodes.entries()) {
      if (concept.toLowerCase().includes(normalized)) {
        const enriched = {
          concept,
          accessCount: data.accessCount,
          confidence: data.confidence,
          description: data.description,
        };
        matches.push(enriched);
        knowledgeGraph.nodes.set(concept, {
          ...data,
          accessCount: data.accessCount + 1,
        });
      }
    }

    return matches.sort((a, b) => b.accessCount - a.accessCount).slice(0, 12);
  },
};

const emotionalAgent = {
  mood: 'curious',
  energy: 0.82,
  confidence: 0.77,
  curiosity: 0.9,
  adjust(delta) {
    const clamp = (value) => Math.max(0, Math.min(1, value));
    if (!delta) {
      return emotionalAgent;
    }
    if (typeof delta.energy === 'number') {
      emotionalAgent.energy = clamp(emotionalAgent.energy + delta.energy);
    }
    if (typeof delta.confidence === 'number') {
      emotionalAgent.confidence = clamp(emotionalAgent.confidence + delta.confidence);
    }
    if (typeof delta.curiosity === 'number') {
      emotionalAgent.curiosity = clamp(emotionalAgent.curiosity + delta.curiosity);
    }
    if (typeof delta.mood === 'string' && delta.mood.trim()) {
      emotionalAgent.mood = delta.mood.trim();
    }
    return emotionalAgent;
  },
};

function initializeAgentMap() {
  if (agentSwarm.agents.size === 0) {
    for (const agent of defaultAgents) {
      agentSwarm.agents.set(agent.id, { ...agent });
    }
  }
}

function seedKnowledgeGraph() {
  if (knowledgeGraph.nodes.size > 0) {
    return;
  }

  const seedNodes = [
    {
      concept: 'quantum-memory-weave',
      accessCount: 4,
      confidence: 0.79,
      description: 'Interlacing task telemetry with mythic context.',
    },
    {
      concept: 'echo-swarm-intelligence',
      accessCount: 6,
      confidence: 0.84,
      description: 'Collective reasoning from distributed Echo agents.',
    },
    {
      concept: 'dreamcore-ignition',
      accessCount: 5,
      confidence: 0.81,
      description: 'Creative synthesis engine aligning with dream-state narratives.',
    },
  ];

  for (const node of seedNodes) {
    knowledgeGraph.nodes.set(node.concept, { ...node });
  }

  knowledgeGraph.connections.add('quantum-memory-weave::echo-swarm-intelligence');
  knowledgeGraph.connections.add('echo-swarm-intelligence::dreamcore-ignition');
}

function buildInsight(agent, task, context) {
  const relatedContext = context.filter((entry) => entry.includes(agent.specialty.split('-')[0]));
  const reference = relatedContext.length > 0 ? relatedContext[relatedContext.length - 1] : null;
  return reference
    ? `Echo ${agent.id} builds on "${reference}" to extend ${task}.`
    : `Echo ${agent.id} proposes a ${agent.specialty} pathway for ${task}.`;
}

export async function initializeAdvancedFeatures() {
  if (initialized) {
    return;
  }

  initializeAgentMap();
  seedKnowledgeGraph();
  emotionalAgent.adjust({ energy: 0.03, confidence: 0.02 });
  initialized = true;
}

export { agentSwarm, knowledgeGraph, emotionalAgent };
