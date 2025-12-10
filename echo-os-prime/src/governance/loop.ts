/// <reference path="../shims-express.d.ts" />
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
import {
  CodonMap,
  enforceCodonMapIntegrity,
  enforceCRAuthorization,
  enforceJSONChainConsistency,
  enforceSCIThreshold,
  enforceValidKernelTransition,
  GovernanceEnforcementError,
  JSONChainRuleset
} from "./enforcement";

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
  enforcementErrors: GovernanceEnforcementError[];
};

export const runGovernanceLoop = (input: GovernanceInput): GovernanceOutput => {
  const store = input.store ?? new FileLedgerStore();
  const kernel = new GovernanceKernel(store);
  let state = kernel.getState();

  const appliedChanges: string[] = [];
  const triggeredRituals: RitualName[] = [];
  const changeRequests = input.changeRequests ?? [];
  const enforcementErrors: GovernanceEnforcementError[] = [];

  const recordEnforcementError = (error: GovernanceEnforcementError) => {
    enforcementErrors.push(error);
    logEvent(
      { type: "INFO", payload: { code: error.code, message: error.message, details: error.details } },
      store
    );
  };

  const safeLoad = <T>(relativePath: string): T | undefined => {
    const primary = path.resolve(process.cwd(), relativePath);
    const fallbackProject = path.resolve(__dirname, "../..", relativePath);
    const fallbackRepo = path.resolve(__dirname, "../../..", relativePath);
    const resolved = [primary, fallbackProject, fallbackRepo].find((candidate) =>
      fs.existsSync(candidate)
    );

    if (!resolved) return undefined;
    const raw = fs.readFileSync(resolved, "utf-8");
    return JSON.parse(raw) as T;
  };

  const jsonchainRuleset = safeLoad<JSONChainRuleset>("jsonchain_ruleset.json");
  if (!jsonchainRuleset) {
    recordEnforcementError({
      code: "GOV.ENFORCE.JSONCHAIN_FAIL",
      message: "Missing JSONChain ruleset specification",
      details: { path: path.resolve(process.cwd(), "jsonchain_ruleset.json") }
    });
  }

  const codonMap = safeLoad<CodonMap>("codon_map.json");
  if (!codonMap) {
    recordEnforcementError({
      code: "GOV.ENFORCE.CODON_MISMATCH",
      message: "Missing codon map specification",
      details: { path: path.resolve(process.cwd(), "codon_map.json") }
    });
  }

  const threshold = input.sciThreshold ?? 0.5;
  const recomputedSci = computeSCI(store.readAll());
  state = { ...state, sci: recomputedSci };

  let processingBlocked = false;
  const sciCheck = enforceSCIThreshold(state.sci, threshold);
  if (!sciCheck.ok) {
    recordEnforcementError(sciCheck.error);
    const ritualState = performRitual("UNITY_WEAVE", state, store);
    const transitionCheck = enforceValidKernelTransition(state, ritualState);
    if (!transitionCheck.ok) {
      recordEnforcementError(transitionCheck.error);
    }
    const recalibratedSci = computeSCI(store.readAll());
    state = { ...ritualState, sci: recalibratedSci };
    triggeredRituals.push("UNITY_WEAVE");

    if (state.sci < threshold) {
      recordEnforcementError({
        code: "GOV.ENFORCE.RITUAL_REQUIRED",
        message: "SCI remains below threshold after UNITY_WEAVE; change requests halted",
        details: { sci: state.sci, threshold }
      });
      processingBlocked = true;
    }
  }

  const recordRejection = (cr: ChangeRequest, message: string, code?: string) => {
    logEvent(
      {
        type: "INFO",
        payload: { id: cr.id, decision: "rejected", reasons: [message], code }
      },
      store
    );
  };

  changeRequests.forEach((cr) => {
    if (processingBlocked) return;

    const authCheck = enforceCRAuthorization(cr);
    if (!authCheck.ok) {
      recordEnforcementError(authCheck.error);
      recordRejection(cr, authCheck.error.message, authCheck.error.code);
      return;
    }

    if (!jsonchainRuleset) {
      recordRejection(cr, "JSONChain ruleset unavailable", "GOV.ENFORCE.JSONCHAIN_FAIL");
      return;
    }
    const jsonchainCheck = enforceJSONChainConsistency(state, jsonchainRuleset);
    if (!jsonchainCheck.ok) {
      recordEnforcementError(jsonchainCheck.error);
      recordRejection(cr, jsonchainCheck.error.message, jsonchainCheck.error.code);
      return;
    }

    if (!codonMap) {
      recordRejection(cr, "Codon map unavailable", "GOV.ENFORCE.CODON_MISMATCH");
      return;
    }
    const codonCheck = enforceCodonMapIntegrity(codonMap, state);
    if (!codonCheck.ok) {
      recordEnforcementError(codonCheck.error);
      recordRejection(cr, codonCheck.error.message, codonCheck.error.code);
      return;
    }

    const validation = submitChangeRequest(cr);
    logEvent(
      {
        type: "INFO",
        payload: { id: cr.id, decision: validation.decision, reasons: validation.reasons }
      },
      store
    );

    if (validation.decision === "accepted") {
      const prevState = state;
      kernel.submit(cr);
      const nextState = kernel.getState();
      const transitionCheck = enforceValidKernelTransition(prevState, nextState);
      if (!transitionCheck.ok) {
        recordEnforcementError(transitionCheck.error);
        return;
      }
      appliedChanges.push(cr.id);
      state = nextState;
    }
  });

  const ritualHooks = input.ritualHooks ?? [];
  ritualHooks.forEach((ritual) => {
    const nextState = performRitual(ritual, state, store);
    const transitionCheck = enforceValidKernelTransition(state, nextState);
    if (!transitionCheck.ok) {
      recordEnforcementError(transitionCheck.error);
      return;
    }
    state = nextState;
    triggeredRituals.push(ritual);
  });

  const finalSci = computeSCI(store.readAll());
  state = { ...state, sci: finalSci };

  const lastEvents = getLedgerSlice(input.lastEventLimit ?? 20, store);

  return {
    state,
    sci: state.sci,
    lastEvents,
    appliedChanges,
    triggeredRituals,
    enforcementErrors
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
  if (result.enforcementErrors.length > 0) {
    console.error("Governance enforcement errors detected:");
    result.enforcementErrors.forEach((error) => {
      console.error(`- [${error.code}] ${error.message}`);
      if (error.details) {
        console.error(`    details: ${JSON.stringify(error.details)}`);
      }
    });
  }
  console.log(JSON.stringify(result, null, 2));
}
