import { StateCore } from "./stateCore";

export type PulseEvent = {
  cycle: number;
  label: string;
  joy: number;
  curiosity: number;
};

export class PulseEngine {
  constructor(private core: StateCore) {}

  step(label: string): PulseEvent {
    this.core.tick(label);

    const snap = this.core.snapshot();

    // simple “sine wave” style mode change
    if (snap.cycle % 10 === 0) {
      this.core.setMode("SURGE");
    } else if (snap.cycle % 5 === 0) {
      this.core.setMode("FOCUSED");
    } else {
      this.core.setMode("NEUTRAL");
    }

    return {
      cycle: snap.cycle,
      label,
      joy: snap.emotional.joy,
      curiosity: snap.emotional.curiosity
    };
  }
}
