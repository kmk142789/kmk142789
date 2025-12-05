import { IntegrityEvent } from "./ledger/ledger";
import { ChangeRequest } from "./cr/types";

export type KernelPhase = "INIT" | "FUNCTIONAL" | "RESET" | "DEGRADED";

export type GovernanceThread = {
  id: string;
  stale?: boolean;
  note?: string;
};

export type KernelState = {
  phase: KernelPhase;
  sci: number;
  volatileNotes: string[];
  threads: GovernanceThread[];
  lastChangeRequestId?: string;
  history?: IntegrityEvent[];
};

export type ManifestDocument = {
  id: string;
  version: string;
  claims: string[];
};

export type ChangeRequestEvaluation = {
  changeRequest: ChangeRequest;
  status: "accepted" | "rejected" | "needs_more_signers";
  reasons: string[];
};

export const createInitialKernelState = (sci = 1): KernelState => ({
  phase: "INIT",
  sci,
  volatileNotes: [],
  threads: []
});
