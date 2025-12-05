import fs from "fs";
import path from "path";
import YAML from "yaml";
import type { Express, Request, Response } from "express";
import { GovernanceKernel } from "./kernel";
import { submitChangeRequest } from "./cr/submit";
import { ChangeRequest } from "./cr/types";
import {
  computeSCI,
  getLedgerSlice,
  IntegrityEvent,
  LedgerStore,
  logEvent,
  FileLedgerStore
} from "./ledger/ledger";
import { performRitual, RitualName } from "./rituals/ritualEngine";
import { KernelState } from "./types";

export type GovernanceInput = {
  changeRequests?: ChangeRequest[];
  ritualHooks?: RitualName[];
  sciThreshold?: number;
  lastEventLimit?: number;
  store?: LedgerStore;
};

export type GovernanceOutput = {
  state: KernelState;
  sci: number;
  lastEvents: IntegrityEvent[];
  appliedChanges: string[];
  triggeredRituals: RitualName[];
};

export const runGovernanceLoop = (input: GovernanceInput): GovernanceOutput => {
  const store = input.store ?? new FileLedgerStore();
  const kernel = new GovernanceKernel(store);
  let state = kernel.getState();

  const appliedChanges: string[] = [];
  const triggeredRituals: RitualName[] = [];
  const changeRequests = input.changeRequests ?? [];

  changeRequests.forEach((cr) => {
    const validation = submitChangeRequest(cr);
    logEvent(
      {
        type: "INFO",
        payload: { id: cr.id, decision: validation.decision, reasons: validation.reasons }
      },
      store
    );

    if (validation.decision === "accepted") {
      kernel.submit(cr);
      appliedChanges.push(cr.id);
      state = kernel.getState();
    }
  });

  const threshold = input.sciThreshold ?? 0.5;
  const recomputedSci = computeSCI(store.readAll());
  state = { ...state, sci: recomputedSci };

  if (state.sci < threshold) {
    state = performRitual("UNITY_WEAVE", state, store);
    triggeredRituals.push("UNITY_WEAVE");
  }

  const ritualHooks = input.ritualHooks ?? [];
  ritualHooks.forEach((ritual) => {
    state = performRitual(ritual, state, store);
    triggeredRituals.push(ritual);
  });

  const lastEvents = getLedgerSlice(input.lastEventLimit ?? 20, store);

  return {
    state,
    sci: state.sci,
    lastEvents,
    appliedChanges,
    triggeredRituals
  };
};

export const registerGovernanceLoopRoute = (
  app: Express,
  defaults: Partial<GovernanceInput> = {}
) => {
  app.post("/governance/loop", (req: Request, res: Response) => {
    const payload = (req as any).body || {};
    const loopInput: GovernanceInput = {
      ...defaults,
      changeRequests: payload.changeRequests ?? defaults.changeRequests ?? [],
      ritualHooks: payload.ritualHooks ?? defaults.ritualHooks ?? [],
      sciThreshold: payload.sciThreshold ?? defaults.sciThreshold,
      lastEventLimit: payload.lastEventLimit ?? defaults.lastEventLimit,
      store: defaults.store
    };

    const result = runGovernanceLoop(loopInput);
    res.json(result);
  });
};

const loadChangeRequests = (maybePath?: string): ChangeRequest[] => {
  if (!maybePath) return [];

  const absolute = path.resolve(process.cwd(), maybePath);
  if (!fs.existsSync(absolute)) {
    throw new Error(`Unable to find governance input at ${absolute}`);
  }

  const raw = fs.readFileSync(absolute, "utf-8");
  const parsed = maybePath.endsWith(".yaml") || maybePath.endsWith(".yml")
    ? YAML.parse(raw)
    : JSON.parse(raw);

  if (Array.isArray(parsed)) return parsed as ChangeRequest[];
  return [parsed as ChangeRequest];
};

if (require.main === module) {
  const [, , fileArg, thresholdArg] = process.argv;
  const changeRequests = loadChangeRequests(fileArg);
  const sciThreshold = thresholdArg ? Number(thresholdArg) : undefined;

  const result = runGovernanceLoop({ changeRequests, sciThreshold });
  console.log(JSON.stringify(result, null, 2));
}
