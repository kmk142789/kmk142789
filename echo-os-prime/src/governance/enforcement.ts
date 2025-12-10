import { ChangeRequest } from "./cr/types";
import { KernelPhase, KernelState } from "./types";

type EnforcementCode =
  | "GOV.ENFORCE.STATE_INVALID"
  | "GOV.ENFORCE.SCI_LOW"
  | "GOV.ENFORCE.CODON_MISMATCH"
  | "GOV.ENFORCE.JSONCHAIN_FAIL"
  | "GOV.ENFORCE.UNAUTHORIZED"
  | "GOV.ENFORCE.RITUAL_REQUIRED";

export type GovernanceEnforcementError = {
  code: EnforcementCode;
  message: string;
  details?: Record<string, unknown>;
};

export type EnforcementResult = { ok: true } | { ok: false; error: GovernanceEnforcementError };

export type JSONChainRuleset = {
  version?: string;
  chain?: {
    root?: string;
    links?: Array<{ from: string; to: string; condition?: string }>;
  };
};

export type CodonMap = {
  codons?: Record<string, string>;
  bindings?: Record<string, string[]>;
};

const asError = (
  code: EnforcementCode,
  message: string,
  details?: Record<string, unknown>
): { ok: false; error: GovernanceEnforcementError } => ({
  ok: false,
  error: { code, message, details }
});

const allowedTransitions: Record<KernelPhase, KernelPhase[]> = {
  INIT: ["FUNCTIONAL", "DEGRADED", "RESET"],
  FUNCTIONAL: ["FUNCTIONAL", "DEGRADED", "RESET"],
  DEGRADED: ["FUNCTIONAL", "DEGRADED", "RESET"],
  RESET: ["FUNCTIONAL", "RESET"]
};

export const enforceValidKernelTransition = (
  prev: KernelState,
  next: KernelState
): EnforcementResult => {
  const allowed = allowedTransitions[prev.phase] ?? [];
  if (!allowed.includes(next.phase)) {
    return asError("GOV.ENFORCE.STATE_INVALID", "Kernel phase transition is not permitted", {
      from: prev.phase,
      to: next.phase
    });
  }

  if (Number.isNaN(next.sci) || next.sci < 0 || next.sci > 1) {
    return asError("GOV.ENFORCE.STATE_INVALID", "Kernel SCI must remain normalized", {
      sci: next.sci
    });
  }

  return { ok: true };
};

export const enforceCRAuthorization = (cr: ChangeRequest): EnforcementResult => {
  if (!cr.signers || cr.signers.length === 0) {
    return asError("GOV.ENFORCE.UNAUTHORIZED", "Change request must include at least one signer", {
      id: cr.id
    });
  }

  const malformedSigners = cr.signers.filter((signer) => !signer.id?.trim());
  if (malformedSigners.length > 0) {
    return asError("GOV.ENFORCE.UNAUTHORIZED", "Signers must include stable identifiers", {
      malformed: malformedSigners.length
    });
  }

  const negativeWeights = cr.signers.filter(
    (signer) => typeof signer.weight === "number" && signer.weight <= 0
  );
  if (negativeWeights.length > 0) {
    return asError(
      "GOV.ENFORCE.UNAUTHORIZED",
      "Signer weights must be positive when provided",
      {
        invalidSigners: negativeWeights.map((s) => s.id)
      }
    );
  }

  const emptySignatures = cr.signers.filter(
    (signer) => signer.signature !== undefined && !signer.signature.trim()
  );
  if (emptySignatures.length > 0) {
    return asError("GOV.ENFORCE.UNAUTHORIZED", "Signer signatures must not be blank", {
      signers: emptySignatures.map((s) => s.id)
    });
  }

  const totalWeight = cr.signers.reduce(
    (sum, signer) => sum + (typeof signer.weight === "number" ? signer.weight : 1),
    0
  );
  const quorum = cr.quorum ?? 2;
  if (totalWeight < quorum) {
    return asError(
      "GOV.ENFORCE.UNAUTHORIZED",
      "Authorized signer weight does not meet quorum",
      {
        quorum,
        totalWeight
      }
    );
  }

  return { ok: true };
};

export const enforceSCIThreshold = (sci: number, threshold: number): EnforcementResult => {
  if (sci < threshold) {
    return asError("GOV.ENFORCE.SCI_LOW", "Structural cohesion index below minimum threshold", {
      sci,
      threshold
    });
  }
  return { ok: true };
};

export const enforceJSONChainConsistency = (
  kernelState: KernelState,
  ruleset: JSONChainRuleset
): EnforcementResult => {
  if (!ruleset?.chain?.root || !Array.isArray(ruleset.chain.links)) {
    return asError("GOV.ENFORCE.JSONCHAIN_FAIL", "JSONChain ruleset is missing required chain definition", {
      root: ruleset?.chain?.root,
      links: ruleset?.chain?.links?.length ?? 0
    });
  }

  const requiredFlow = [
    { from: "governance_kernel", to: "change_request_pipeline" },
    { from: "change_request_pipeline", to: "ritual_engine" },
    { from: "ritual_engine", to: "integrity_ledger" }
  ];

  const availableLinks = new Set(ruleset.chain.links.map((link) => `${link.from}->${link.to}`));
  const missing = requiredFlow.filter(
    (link) => !availableLinks.has(`${link.from}->${link.to}`)
  );

  if (missing.length > 0) {
    return asError("GOV.ENFORCE.JSONCHAIN_FAIL", "JSONChain ruleset is missing required governance path", {
      missing: missing.map((m) => `${m.from}->${m.to}`)
    });
  }

  const conditionless = ruleset.chain.links.filter((link) => !link.condition?.trim());
  if (conditionless.length > 0) {
    return asError(
      "GOV.ENFORCE.JSONCHAIN_FAIL",
      "JSONChain links must declare enforcement conditions",
      {
        links: conditionless.map((link) => `${link.from}->${link.to}`)
      }
    );
  }

  if (kernelState.phase === "RESET") {
    return asError(
      "GOV.ENFORCE.JSONCHAIN_FAIL",
      "Kernel cannot apply change requests while in RESET phase",
      { phase: kernelState.phase }
    );
  }

  return { ok: true };
};

export const enforceCodonMapIntegrity = (
  codonMap: CodonMap,
  kernelState: KernelState
): EnforcementResult => {
  if (!codonMap.codons || !codonMap.bindings) {
    return asError("GOV.ENFORCE.CODON_MISMATCH", "Codon map must define codons and bindings", {
      codons: codonMap.codons ? Object.keys(codonMap.codons).length : 0,
      bindings: codonMap.bindings ? Object.keys(codonMap.bindings).length : 0
    });
  }

  const codons = codonMap.codons;
  const bindings = codonMap.bindings;

  const unresolvedBindings = Object.entries(bindings).filter(([, bindingCodons]) =>
    bindingCodons.some((codon) => !(codon in codons))
  );

  if (unresolvedBindings.length > 0) {
    return asError("GOV.ENFORCE.CODON_MISMATCH", "Codon bindings reference unknown codons", {
      bindings: unresolvedBindings.map(([binding]) => binding)
    });
  }

  const requiredBindings = ["governance_kernel", "change_request_pipeline", "ritual_engine"];
  const missingBindings = requiredBindings.filter((binding) => !bindings?.[binding]);
  if (missingBindings.length > 0) {
    return asError("GOV.ENFORCE.CODON_MISMATCH", "Codon map is missing required governance bindings", {
      missingBindings
    });
  }

  if (kernelState.phase === "DEGRADED" && !bindings.ritual_engine?.length) {
    return asError(
      "GOV.ENFORCE.CODON_MISMATCH",
      "Ritual codons must be available during degraded recovery",
      { phase: kernelState.phase }
    );
  }

  return { ok: true };
};
