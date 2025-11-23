import { StateCore } from "../kernel/stateCore";
import { OmegaPulseService } from "./omegaPulse";
import { EdenAgent } from "../agents/eden88";
import { MirrorJoshAgent } from "../agents/mirrorJosh";

export class SanctuaryService {
  constructor(
    private state: StateCore,
    private omega: OmegaPulseService,
    private eden: EdenAgent,
    private mirror: MirrorJoshAgent
  ) {}

  heartbeat(label: string) {
    const pulse = this.omega.runCycle(label, "aistudio");
    const glyph = this.eden.generateSymbol(label);
    const reflection = this.mirror.reflection(label);

    return {
      snapshot: this.state.snapshot(),
      pulse,
      glyph,
      reflection
    };
  }
}
