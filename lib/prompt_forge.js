const prompts = new Map();
let counter = 0;

export const promptForge = {
  getForgeState() {
    return {
      totalPrompts: prompts.size,
      recentPrompts: Array.from(prompts.values()).slice(-5),
    };
  },

  async forgePrompt(content, metadata = {}) {
    const id = `prompt-${++counter}`;
    const entry = {
      id,
      content,
      metadata,
      createdAt: Date.now(),
      revisions: [],
    };
    prompts.set(id, entry);
    return entry;
  },

  async refinePrompt(promptId, refinementType = 'general', customInstructions) {
    const prompt = prompts.get(promptId);
    if (!prompt) {
      throw new Error(`Prompt ${promptId} not found`);
    }
    const revision = {
      refinementType,
      customInstructions: customInstructions || null,
      timestamp: Date.now(),
    };
    prompt.revisions.push(revision);
    return { ...prompt, lastRevision: revision };
  },

  async rewritePrompt(promptId, newTone, newIntent) {
    const prompt = prompts.get(promptId);
    if (!prompt) {
      throw new Error(`Prompt ${promptId} not found`);
    }
    const rewritten = {
      tone: newTone,
      intent: newIntent,
      timestamp: Date.now(),
    };
    prompt.revisions.push({ type: 'rewrite', ...rewritten });
    prompt.metadata = { ...prompt.metadata, tone: newTone, intent: newIntent };
    return { ...prompt, rewrite: rewritten };
  },

  searchPrompts(query) {
    const normalized = typeof query === 'string' ? query.trim().toLowerCase() : '';
    if (!normalized) {
      return [];
    }
    const results = [];
    for (const prompt of prompts.values()) {
      if (prompt.content.toLowerCase().includes(normalized)) {
        results.push(prompt);
      }
    }
    return results.slice(0, 10);
  },
};
