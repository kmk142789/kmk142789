const state = {
  phase: 'IDLE',
  visions: [],
  iterations: 0,
};

export const dreamcoreEngine = {
  getState() {
    return {
      phase: state.phase,
      iterations: state.iterations,
      activeVisions: state.visions.slice(-5),
    };
  },

  async imagine(prompt) {
    const normalized = typeof prompt === 'string' && prompt.trim() ? prompt.trim() : 'Unnamed dream';
    const vision = {
      prompt: normalized,
      signature: `vision-${state.iterations + 1}`,
      createdAt: Date.now(),
    };
    state.visions.push(vision);
    state.phase = 'IMAGINING';
    state.iterations += 1;
    return vision;
  },

  async evolve() {
    state.phase = 'EVOLVING';
    state.iterations += 1;
    const resonance = Number(Math.min(1, 0.6 + state.iterations * 0.02).toFixed(2));
    return {
      message: 'Dreamcore engine evolved to a new resonance pattern.',
      resonance,
      iterations: state.iterations,
    };
  },
};
