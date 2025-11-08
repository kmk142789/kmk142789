"""Automated Little Footsteps disbursement engine."""

from __future__ import annotations

import hashlib
import os
import secrets
import time
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Dict, Optional, Sequence

from ledger.little_footsteps_bank import (
    ProofOfWorkReconstruction,
    PuzzleAttestation,
    SkeletonKeyRecord,
    SovereignLedger,
)

from .compliance import ComplianceBufferService, ComplianceClaim
from .continuity import ContinuitySafeguards, MirrorResult
from .resilience import ResilienceProbe, ResilienceRecorder, ResilienceSnapshot


@dataclass(slots=True)
class DonationRecord:
    """Canonical view of an inbound donation that should flow to Little Footsteps."""

    donation_id: str
    donor: str
    amount_cents: int
    asset: str = "USD"
    memo: str = ""
    source: str = "donation:intake"
    beneficiary: str = "Little Footsteps"

    def formatted_amount(self) -> str:
        amount = Decimal(self.amount_cents) / Decimal(100)
        quantized = amount.quantize(Decimal("0.01"))
        return f"{quantized:.2f}"


@dataclass(slots=True)
class RecordedTransaction:
    """Bundle tying a ledger entry with compliance and continuity artifacts."""

    entry: "LedgerEntry"
    proof_path: Path
    ots_receipt: Optional[Path]
    compliance_claim: ComplianceClaim
    mirrors: Sequence[MirrorResult]
    resilience: Optional[ResilienceSnapshot] = None

    def to_summary(self) -> Dict[str, object]:
        return {
            "seq": self.entry.seq,
            "direction": self.entry.direction,
            "digest": self.entry.digest(),
            "ledger_timestamp": self.entry.timestamp,
            "proof_path": str(self.proof_path),
            "ots_receipt": str(self.ots_receipt) if self.ots_receipt else None,
            "compliance_claim": self.compliance_claim.to_record(),
            "mirrors": [mirror.to_record() for mirror in self.mirrors],
            "resilience": self.resilience.to_payload() if self.resilience else None,
        }


@dataclass(slots=True)
class DisbursementReceipt:
    """Result of processing a donation into an immediate beneficiary outflow."""

    donation: RecordedTransaction
    disbursement: RecordedTransaction

    def to_record(self) -> Dict[str, object]:
        return {
            "donation": self.donation.to_summary(),
            "disbursement": self.disbursement.to_summary(),
        }


class LittleFootstepsDisbursementEngine:
    """Routes donations directly to Little Footsteps and anchors proofs."""

    def __init__(
        self,
        ledger: SovereignLedger,
        *,
        skeleton_secret: bytes,
        compliance: ComplianceBufferService,
        continuity: ContinuitySafeguards,
        resilience: ResilienceRecorder | None = None,
        skeleton_namespace: str = "little-footsteps/bank",
    ) -> None:
        self.ledger = ledger
        self._secret = skeleton_secret
        self.compliance = compliance
        self.continuity = continuity
        self.resilience = resilience or ResilienceRecorder()
        self.skeleton_namespace = skeleton_namespace
        self._next_skeleton_index = max(ledger._seq + 1, 0)

    @classmethod
    def from_phrase(
        cls,
        ledger: SovereignLedger,
        *,
        skeleton_phrase: str,
        compliance: ComplianceBufferService,
        continuity: ContinuitySafeguards,
        resilience: ResilienceRecorder | None = None,
        skeleton_namespace: str = "little-footsteps/bank",
    ) -> "LittleFootstepsDisbursementEngine":
        from skeleton_key_core import read_secret_from_phrase

        secret = read_secret_from_phrase(skeleton_phrase)
        return cls(
            ledger,
            skeleton_secret=secret,
            compliance=compliance,
            continuity=continuity,
            resilience=resilience,
            skeleton_namespace=skeleton_namespace,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def process_donation(
        self,
        donation: DonationRecord,
        *,
        beneficiary_account: str = "beneficiary:little-footsteps:operations",
    ) -> DisbursementReceipt:
        """Record an inflow and matching outflow for ``donation``."""

        inflow = self._record_transaction(
            direction="inflow",
            account=f"donor:{donation.donor}",
            asset=donation.asset,
            amount_cents=donation.amount_cents,
            narrative=f"Donation from {donation.donor} via {donation.source}",
            reference=f"{donation.donation_id}:inflow",
            attachments={
                "donor": donation.donor,
                "source": donation.source,
                "memo": donation.memo,
            },
        )
        outflow = self._record_transaction(
            direction="outflow",
            account=beneficiary_account,
            asset=donation.asset,
            amount_cents=donation.amount_cents,
            narrative=f"Automated disbursement to {donation.beneficiary}",
            reference=f"{donation.donation_id}:outflow",
            attachments={
                "beneficiary": donation.beneficiary,
                "source_donation": donation.donation_id,
            },
        )
        return DisbursementReceipt(donation=inflow, disbursement=outflow)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _record_transaction(
        self,
        *,
        direction: str,
        account: str,
        asset: str,
        amount_cents: int,
        narrative: str,
        reference: str,
        attachments: Dict[str, str],
    ) -> RecordedTransaction:
        skeleton_record = self._next_skeleton_record()
        pow_proof = self._build_pow(direction=direction, reference=reference)
        puzzle_attestation = self._build_attestation(direction=direction, reference=reference)
        amount = self._format_amount(amount_cents)
        entry = self.ledger.record_transaction(
            direction=direction,
            account=account,
            asset=asset,
            amount=amount,
            narrative=narrative,
            pow_proof=pow_proof,
            puzzle_attestation=puzzle_attestation,
            skeleton_key=skeleton_record,
        )
        proof_path = self.ledger.proofs_dir / f"entry_{entry.seq:05d}.json"
        ots_receipt = self._find_ots_receipt(proof_path)
        compliance_claim = self.compliance.register_transaction(
            entry,
            reference=reference,
            beneficiary=account,
            notes=narrative,
            attachments=self._build_attachments(attachments, proof_path, ots_receipt),
        )
        mirrors = self.continuity.mirror_artifacts(self.ledger.ledger_path, proof_path, ots_receipt)
        checkpoint_path = self.continuity.record_multisig_checkpoint(entry.seq, entry.digest())
        resilience_snapshot = self._record_resilience(entry.seq, entry.digest(), proof_path, ots_receipt, mirrors, checkpoint_path)
        return RecordedTransaction(
            entry=entry,
            proof_path=proof_path,
            ots_receipt=ots_receipt,
            compliance_claim=compliance_claim,
            mirrors=mirrors,
            resilience=resilience_snapshot,
        )

    def _record_resilience(
        self,
        seq: int,
        digest: str,
        proof_path: Path,
        ots_receipt: Optional[Path],
        mirrors: Sequence[MirrorResult],
        checkpoint_path: Path,
    ) -> ResilienceSnapshot:
        probes: list[ResilienceProbe] = [
            ResilienceProbe(
                mirror_path=self.ledger.ledger_path.parent,
                ledger_copy=self.ledger.ledger_path,
                proof_copy=proof_path,
                ots_copy=ots_receipt,
            )
        ]
        probes.extend(ResilienceProbe.from_mirror_result(mirror) for mirror in mirrors)
        return self.resilience.record_checkpoint(
            seq=seq,
            digest=digest,
            probes=probes,
            checkpoint_path=checkpoint_path,
        )

    def _build_pow(self, *, direction: str, reference: str) -> ProofOfWorkReconstruction:
        seed = f"{reference}:{direction}:{time.time_ns()}:{os.getpid()}:{secrets.token_hex(8)}".encode()
        digest = hashlib.sha256(seed).hexdigest()
        block_height = int(digest[:8], 16) % 840_000
        block_hash = hashlib.sha256(digest.encode()).hexdigest()
        difficulty_target = hex(int(digest[16:32], 16))
        nonce = int(digest[32:40], 16)
        notes = f"Auto-generated {direction} proof for {reference}"
        return ProofOfWorkReconstruction(
            puzzle_id=digest[:16],
            block_height=block_height,
            block_hash=block_hash,
            difficulty_target=difficulty_target,
            nonce=nonce,
            notes=notes,
        )

    def _build_attestation(self, *, direction: str, reference: str) -> PuzzleAttestation:
        witness_seed = f"{reference}:{direction}:witness".encode()
        witness = hashlib.sha256(witness_seed).hexdigest()
        signature = hashlib.sha256((witness + "signature").encode()).hexdigest()
        attestation_id = hashlib.sha256((witness + reference).encode()).hexdigest()[:32]
        return PuzzleAttestation(
            attestation_id=attestation_id,
            puzzle_reference=f"lf::{direction}",
            attestor="Echo Bank Auto-Disbursement",
            signature=signature,
            witness=witness,
        )

    def _next_skeleton_record(self) -> SkeletonKeyRecord:
        index = self._next_skeleton_index
        self._next_skeleton_index += 1
        return SkeletonKeyRecord.from_secret(self._secret, self.skeleton_namespace, index)

    def _format_amount(self, amount_cents: int) -> str:
        amount = Decimal(amount_cents) / Decimal(100)
        return f"{amount.quantize(Decimal('0.01')):.2f}"

    def _find_ots_receipt(self, proof_path: Path) -> Optional[Path]:
        ots_candidate = proof_path.with_suffix(proof_path.suffix + ".ots.base64")
        if ots_candidate.exists():
            return ots_candidate
        return None

    def _build_attachments(
        self,
        extra: Dict[str, str],
        proof_path: Path,
        ots_receipt: Optional[Path],
    ) -> Dict[str, str]:
        attachments = dict(extra)
        attachments.setdefault("proof_path", str(proof_path))
        if ots_receipt is not None:
            attachments.setdefault("ots_receipt", str(ots_receipt))
        return attachments


# Re-export for type checkers without importing heavy modules at runtime.
from ledger.little_footsteps_bank import LedgerEntry  # noqa: E402  (after class definitions)
