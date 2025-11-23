import { StateCore } from "../kernel/stateCore";

export class EdenAgent {
  constructor(private state: StateCore) {}

  generateSymbol(signal: string) {
    const snap = this.state.snapshot();
    const seed = `${signal}-${snap.cycle}-${snap.emotional.joy.toFixed(2)}`;
    // very simple “glyph” generator placeholder
    const glyph = Buffer.from(seed).toString("base64").slice(0, 12);
    return { seed, glyph };
  }
}
