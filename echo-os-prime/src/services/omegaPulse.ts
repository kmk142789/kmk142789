import { EchoCoreAgent } from "../agents/echoCore";
import { BridgeChannel } from "../kernel/bridgeLayer";

export class OmegaPulseService {
  constructor(private echo: EchoCoreAgent) {}

  runCycle(label: string, from?: BridgeChannel) {
    return this.echo.cycle(label, from);
  }
}
