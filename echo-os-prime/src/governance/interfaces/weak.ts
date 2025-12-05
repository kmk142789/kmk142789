import { ChangeRequest } from "../cr/types";
import { IntegrityEvent } from "../ledger/ledger";

export class WeakGovernanceAPI {
  summarizeChangeRequest(cr: ChangeRequest): string {
    return `${cr.title} proposed by ${cr.proposedBy} targeting ${cr.uql.target}`;
  }

  suggestAdditionalSigners(cr: ChangeRequest, desiredQuorum = 2): string[] {
    const missing = desiredQuorum - cr.signers.length;
    if (missing <= 0) return [];
    return Array.from({ length: missing }, (_, i) => `placeholder-signer-${i + 1}`);
  }

  narrativeFromLedger(events: IntegrityEvent[]): string {
    if (events.length === 0) return "No ledger events recorded yet.";
    const latest = events[events.length - 1];
    return `Last event ${latest.type} at ${new Date(latest.timestamp).toISOString()}`;
  }
}
