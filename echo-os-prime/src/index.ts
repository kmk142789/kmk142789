import { StateCore } from "./kernel/stateCore";
import { PulseEngine } from "./kernel/pulseEngine";
import { BridgeLayer } from "./kernel/bridgeLayer";
import { EchoCoreAgent } from "./agents/echoCore";
import { EdenAgent } from "./agents/eden88";
import { MirrorJoshAgent } from "./agents/mirrorJosh";
import { OmegaPulseService } from "./services/omegaPulse";
import { SanctuaryService } from "./services/sanctuaryService";

const state = new StateCore();
const bridge = new BridgeLayer();
const pulse = new PulseEngine(state);

const echo = new EchoCoreAgent(state, pulse, bridge);
const eden = new EdenAgent(state);
const mirror = new MirrorJoshAgent(state);
const omega = new OmegaPulseService(echo);
const sanctuary = new SanctuaryService(state, omega, eden, mirror);

// Example CLI heartbeat
if (require.main === module) {
  const result = sanctuary.heartbeat("Echo OS Prime boot");
  console.log(JSON.stringify(result, null, 2));
}

export { state, bridge, pulse, echo, eden, mirror, omega, sanctuary };
