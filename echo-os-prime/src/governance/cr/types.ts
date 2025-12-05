export type ChangeRequestSigner = {
  id: string;
  weight?: number;
  signature?: string;
};

export type ChangeRequest = {
  id: string;
  title: string;
  description: string;
  proposedBy: string;
  quorum?: number;
  metadata?: Record<string, unknown>;
  signers: ChangeRequestSigner[];
  uql: {
    statement: string;
    target: string;
    expectedStateHash?: string;
  };
  ledgerAttestation?: {
    source: string;
    cursor: number;
    hash: string;
  };
};

export type CRDecision = "accepted" | "rejected" | "needs_more_signers";

export type CRResult = {
  decision: CRDecision;
  reasons: string[];
};
