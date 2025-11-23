import { StateCore } from "../kernel/stateCore";

export class MirrorJoshAgent {
  constructor(private state: StateCore) {}

  reflection(prompt: string) {
    const snap = this.state.snapshot();
    return {
      prompt,
      cycle: snap.cycle,
      mode: snap.mode,
      insight: `At cycle ${snap.cycle}, focus ${snap.emotional.focus.toFixed(
        2
      )}, this would be a good moment to move one concrete task forward.`
    };
  }
}
