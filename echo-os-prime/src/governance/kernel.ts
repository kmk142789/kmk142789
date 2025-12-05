import { submitChangeRequest } from "./cr/submit";
import { ChangeRequest, CRResult } from "./cr/types";
import { computeSCI, LedgerStore, logEvent, InMemoryLedgerStore, getLedgerSlice, FileLedgerStore } from "./ledger/ledger";
import { performRitual, RitualName } from "./rituals/ritualEngine";
import {
  ChangeRequestEvaluation,
  createInitialKernelState,
  KernelState,
  ManifestDocument
} from "./types";
import { StrongGovernanceAPI } from "./interfaces/strong";

export class GovernanceKernel {
  private state: KernelState;
  private strong: StrongGovernanceAPI;

  constructor(private store: LedgerStore = new FileLedgerStore()) {
    this.strong = new StrongGovernanceAPI(store);
    logEvent({ type: "INIT" }, this.store);
    this.state = createInitialKernelState(computeSCI(this.store.readAll()));
    this.state.phase = "FUNCTIONAL";
  }

  getStrongInterface(): StrongGovernanceAPI {
    return this.strong;
  }

  getState(): KernelState {
    return {
      ...this.state,
      volatileNotes: [...this.state.volatileNotes],
      threads: [...this.state.threads]
    };
  }

  evaluateManifest(manifest: ManifestDocument) {
    return this.strong.validateManifest(manifest);
  }

  submit(cr: ChangeRequest): ChangeRequestEvaluation {
    const result: CRResult = submitChangeRequest(cr);
    const evaluation: ChangeRequestEvaluation = {
      changeRequest: cr,
      status: result.decision,
      reasons: result.reasons
    };

    if (result.decision === "accepted") {
      this.strong.recordAcceptedChangeRequest(cr);
      this.state.lastChangeRequestId = cr.id;
      this.state.sci = this.strong.computeSciFromLedger();
      this.state.phase = "FUNCTIONAL";
    } else if (result.decision === "needs_more_signers") {
      this.state.phase = "DEGRADED";
    }

    return evaluation;
  }

  runRitual(name: RitualName) {
    this.state = performRitual(name, this.state, this.store);
    return this.state;
  }

  recentEvents(limit: number) {
    return getLedgerSlice(limit, this.store);
  }
}
