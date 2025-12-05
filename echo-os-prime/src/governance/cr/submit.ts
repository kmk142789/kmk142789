import { ChangeRequest, CRResult } from "./types";
import {
  validateLedgerAttestation,
  validateStructuralIntegrity,
  validateUqlConsistency
} from "./validators";

export const submitChangeRequest = (cr: ChangeRequest): CRResult => {
  const structural = validateStructuralIntegrity(cr);
  if (!structural.valid) {
    return { decision: "rejected", reasons: structural.errors || [] };
  }

  const uql = validateUqlConsistency(cr);
  if (!uql.valid) {
    return { decision: "rejected", reasons: uql.errors || [] };
  }

  const attestation = validateLedgerAttestation(cr);
  if (!attestation.valid) {
    return { decision: "rejected", reasons: attestation.errors || [] };
  }

  const quorum = cr.quorum ?? 2;
  const uniqueSigners = new Set(cr.signers.map((s) => s.id));

  if (uniqueSigners.size !== cr.signers.length) {
    return {
      decision: "rejected",
      reasons: ["Duplicate signers detected; quorum cannot be validated"]
    };
  }

  if (uniqueSigners.size < quorum) {
    return {
      decision: "needs_more_signers",
      reasons: [`Quorum of ${quorum} signers not met`]
    };
  }

  return { decision: "accepted", reasons: [] };
};
