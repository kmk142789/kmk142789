"""EchoXyloCrossChainBridge: resilient cross-chain anchor harmonizer.

This module provides a lightweight coordination layer for cross-chain anchor
validation.  It helps tests stitch together anchor evidence from heterogeneous
chains (Ethereum, Solana, Bitcoin, or custom rollups), normalize proof metadata,
and determine whether cross-chain operations are ready to proceed.

Design goals
------------
- Deterministic, side-effect free utilities so tests can run without network
  access.
- Human-friendly diagnostics that describe which chains are missing or below the
  required confirmation/finality thresholds.
- Canonical proof hashing that mirrors other cross-chain utilities in the
  repository for consistent signing and logging.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Mapping, Sequence


@dataclass(frozen=True)
class AnchorProof:
    """Normalised proof payload produced for a chain anchor."""

    chain: str
    anchor_id: str
    proof_type: str
    payload: Mapping[str, object]
    commitment: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "commitment", _canonical_hash(self.payload))


@dataclass(frozen=True)
class AnchorState:
    """Stateful view of an anchor across chains."""

    chain: str
    anchor_id: str
    confirmations: int
    finality_score: float
    proof: AnchorProof | None = None
    last_checked: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def is_ready(self, *, min_confirmations: int, finality_threshold: float) -> bool:
        return (
            self.confirmations >= min_confirmations
            and self.finality_score >= finality_threshold
        )


@dataclass(frozen=True)
class BridgeAssessment:
    """Aggregated readiness view for the cross-chain bridge."""

    ready: bool
    coverage: float
    aggregated_finality: float
    missing_chains: tuple[str, ...]
    anchors: tuple[AnchorState, ...]
    risk_score: float


class EchoXyloCrossChainBridge:
    """Coordinate anchor readiness and diagnostics across chains."""

    def __init__(
        self,
        *,
        required_chains: Sequence[str] | None = None,
        finality_threshold: float = 0.66,
        min_confirmations: int = 1,
    ) -> None:
        self.required_chains = tuple(required_chains or ("ethereum", "solana", "bitcoin"))
        self.finality_threshold = finality_threshold
        self.min_confirmations = min_confirmations
        self._anchors: list[AnchorState] = []

    @property
    def anchors(self) -> tuple[AnchorState, ...]:
        """Return registered anchors ordered by chain then anchor id."""

        return tuple(sorted(self._anchors, key=lambda entry: (entry.chain, entry.anchor_id)))

    def register_anchor(
        self,
        *,
        chain: str,
        anchor_id: str,
        confirmations: int,
        finality_score: float,
        proof: Mapping[str, object] | None = None,
        proof_type: str = "hash_attestation",
    ) -> AnchorState:
        """Register or replace an anchor state.

        ``finality_score`` is a float between 0 and 1 describing the probability
        that the chain will not reorganize the anchor.  Callers may attach a
        ``proof`` payload; when provided it is canonicalised into an
        :class:`AnchorProof` and stored alongside the state.
        """

        normalized_score = _clamp(finality_score)
        anchor = AnchorState(
            chain=chain.lower(),
            anchor_id=str(anchor_id),
            confirmations=int(confirmations),
            finality_score=normalized_score,
            proof=AnchorProof(
                chain=chain.lower(),
                anchor_id=str(anchor_id),
                proof_type=proof_type,
                payload=proof or {},
            )
            if proof is not None
            else None,
        )
        # Replace existing anchor for the same chain/anchor_id if present.
        self._anchors = [
            entry
            for entry in self._anchors
            if not (entry.chain == anchor.chain and entry.anchor_id == anchor.anchor_id)
        ]
        self._anchors.append(anchor)
        return anchor

    def attach_proof(self, chain: str, anchor_id: str, proof: Mapping[str, object], *, proof_type: str = "hash_attestation") -> AnchorState:
        """Attach or update proof metadata for an existing anchor."""

        updated: list[AnchorState] = []
        target: AnchorState | None = None
        for entry in self._anchors:
            if entry.chain == chain.lower() and entry.anchor_id == str(anchor_id):
                target = AnchorState(
                    chain=entry.chain,
                    anchor_id=entry.anchor_id,
                    confirmations=entry.confirmations,
                    finality_score=entry.finality_score,
                    proof=AnchorProof(
                        chain=entry.chain,
                        anchor_id=entry.anchor_id,
                        proof_type=proof_type,
                        payload=proof,
                    ),
                    last_checked=datetime.now(timezone.utc).isoformat(),
                )
                updated.append(target)
            else:
                updated.append(entry)
        if target is None:
            raise KeyError(f"anchor {chain}:{anchor_id} not registered")
        self._anchors = updated
        return target

    def assess(self) -> BridgeAssessment:
        """Compute readiness across required chains."""

        best_by_chain = self._best_states_by_chain()
        missing = tuple(chain for chain in self.required_chains if chain not in best_by_chain)
        coverage = len(best_by_chain) / len(self.required_chains) if self.required_chains else 1.0

        aggregated_finality = 0.0
        readiness_flags: list[bool] = []
        for chain in self.required_chains:
            state = best_by_chain.get(chain)
            if state:
                aggregated_finality += state.finality_score
                readiness_flags.append(
                    state.is_ready(
                        min_confirmations=self.min_confirmations,
                        finality_threshold=self.finality_threshold,
                    )
                )
            else:
                readiness_flags.append(False)
        aggregated_finality = aggregated_finality / len(self.required_chains) if self.required_chains else 0.0
        ready = all(readiness_flags) and not missing

        # Risk drops as coverage and finality increase. Clamp to [0, 1].
        risk_score = round(1 - (coverage * aggregated_finality), 3)
        risk_score = max(0.0, min(1.0, risk_score))

        return BridgeAssessment(
            ready=ready,
            coverage=round(coverage, 3),
            aggregated_finality=round(aggregated_finality, 3),
            missing_chains=missing,
            anchors=self.anchors,
            risk_score=risk_score,
        )

    def build_envelope(self) -> dict:
        """Return a serialisable envelope summarising the bridge state."""

        assessment = self.assess()
        return {
            "ready": assessment.ready,
            "coverage": assessment.coverage,
            "aggregated_finality": assessment.aggregated_finality,
            "risk_score": assessment.risk_score,
            "missing_chains": list(assessment.missing_chains),
            "anchors": [
                {
                    "chain": anchor.chain,
                    "anchor_id": anchor.anchor_id,
                    "confirmations": anchor.confirmations,
                    "finality_score": round(anchor.finality_score, 3),
                    "proof_commitment": anchor.proof.commitment if anchor.proof else None,
                    "proof_type": anchor.proof.proof_type if anchor.proof else None,
                    "last_checked": anchor.last_checked,
                }
                for anchor in assessment.anchors
            ],
        }

    def _best_states_by_chain(self) -> dict[str, AnchorState]:
        best: dict[str, AnchorState] = {}
        for anchor in self._anchors:
            existing = best.get(anchor.chain)
            if existing is None or anchor.finality_score > existing.finality_score:
                best[anchor.chain] = anchor
        return best


def _clamp(value: float) -> float:
    if value < 0:
        return 0.0
    if value > 1:
        return 1.0
    return float(value)


def _canonical_hash(payload: Mapping[str, object]) -> str:
    """Return a deterministic hash for proof payloads.

    The function uses JSON canonicalisation to keep hashes stable across tests,
    mirroring the strategy used by cross-chain DID commitments.
    """

    serialised = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(serialised.encode("utf-8")).hexdigest()
    return "0x" + digest


__all__ = [
    "AnchorProof",
    "AnchorState",
    "BridgeAssessment",
    "EchoXyloCrossChainBridge",
]
