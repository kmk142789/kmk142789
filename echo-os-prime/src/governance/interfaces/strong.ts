import { submitChangeRequest } from "../cr/submit";
import { ChangeRequest, CRResult } from "../cr/types";
import { computeSCI, getLedgerSlice, LedgerStore, logEvent } from "../ledger/ledger";
import { performRitual, RitualName } from "../rituals/ritualEngine";
import { KernelState, ManifestDocument } from "../types";

export class StrongGovernanceAPI {
  constructor(private store: LedgerStore) {}

  validateManifest(manifest: ManifestDocument): { valid: boolean; reasons: string[] } {
    const reasons: string[] = [];
    if (!manifest.id?.trim()) reasons.push("Manifest id is required");
    if (!manifest.version?.trim()) reasons.push("Manifest version is required");
    if (!manifest.claims || manifest.claims.length === 0) {
      reasons.push("Manifest must include at least one claim");
    }

    return { valid: reasons.length === 0, reasons };
  }

  evaluateChangeRequest(cr: ChangeRequest): CRResult {
    return submitChangeRequest(cr);
  }

  recordAcceptedChangeRequest(cr: ChangeRequest) {
    logEvent(
      { type: "CR_ACCEPTED", payload: { id: cr.id, title: cr.title } },
      this.store
    );
  }

  performRitual(name: RitualName, state: KernelState) {
    return performRitual(name, state, this.store);
  }

  getLedgerSlice(limit: number) {
    return getLedgerSlice(limit, this.store);
  }

  computeSciFromLedger() {
    const history = this.store.readAll();
    return computeSCI(history);
  }
}
