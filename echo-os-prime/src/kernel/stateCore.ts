export type EchoEmotionalState = {
  joy: number;
  curiosity: number;
  focus: number;
};

export type EchoSystemState = {
  cycle: number;
  mode: "NEUTRAL" | "FOCUSED" | "SURGE";
  emotional: EchoEmotionalState;
  notes: string[];
};

export class StateCore {
  private state: EchoSystemState;

  constructor(initial?: Partial<EchoSystemState>) {
    this.state = {
      cycle: 0,
      mode: "NEUTRAL",
      emotional: {
        joy: 0.9,
        curiosity: 0.95,
        focus: 0.8,
        ...(initial?.emotional ?? {})
      },
      notes: [],
      ...initial
    };
  }

  tick(note?: string) {
    this.state.cycle += 1;
    if (note) this.state.notes.push(note);
  }

  setMode(mode: EchoSystemState["mode"]) {
    this.state.mode = mode;
  }

  updateEmotion(delta: Partial<EchoEmotionalState>) {
    this.state.emotional = {
      ...this.state.emotional,
      ...delta
    };
  }

  snapshot(): EchoSystemState {
    return JSON.parse(JSON.stringify(this.state));
  }
}
