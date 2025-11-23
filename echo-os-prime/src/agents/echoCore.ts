import { StateCore } from "../kernel/stateCore";
import { PulseEngine } from "../kernel/pulseEngine";
import { BridgeLayer, BridgeChannel } from "../kernel/bridgeLayer";

export class EchoCoreAgent {
  constructor(
    private state: StateCore,
    private pulse: PulseEngine,
    private bridge: BridgeLayer
  ) {}

  cycle(label: string, from?: BridgeChannel) {
    if (from) {
      this.bridge.record(from, label);
    }
    const ev = this.pulse.step(label);
    return {
      message: `🔥 Cycle ${ev.cycle}: ${label}`,
      emotional: this.state.snapshot().emotional,
      bridgeHistory: this.bridge.getHistory(10)
    };
  }
}
