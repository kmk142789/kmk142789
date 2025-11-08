"""Synchronise cryptographic pulse receipts with the temporal propagation ledger."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

from echo.atlas.temporal_ledger import (
    LedgerEntry,
    LedgerEntryInput,
    TemporalLedger,
    VotePayload,
)
from echo.temporal_ledger import TemporalConsensusFabric

from .ledger import PulseLedger, PulseReceipt

__all__ = ["CrossLedgerSynchronizer"]


def _parse_timestamp(raw: str) -> datetime:
    ts = datetime.fromisoformat(raw)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts


@dataclass(slots=True)
class CrossLedgerSynchronizer:
    """Bridge cryptographic validation receipts into the temporal propagation ledger.

    The synchronizer walks the signed receipts managed by :class:`PulseLedger`
    and ensures that each receipt is reflected in the
    :class:`~echo.atlas.temporal_ledger.TemporalLedger`. Each record is stored
    with the receipt signature as ``proof_id`` so downstream tools can verify
    that the propagation history is anchored to a cryptographically sealed
    artefact.
    """

    pulse_ledger: PulseLedger
    temporal_ledger: TemporalLedger
    consensus_fabric: TemporalConsensusFabric | None = None
    consensus_vote_weight: float = 1.0
    actor: str = "Pulse Ledger Synchronizer"
    action: str = "propagation-validation-linked"

    def sync(self) -> List[LedgerEntry]:
        """Append missing temporal ledger entries for known pulse receipts."""

        existing = {entry.proof_id: entry for entry in self.temporal_ledger.entries()}
        appended: List[LedgerEntry] = []
        for receipt in self.pulse_ledger.iter_receipts():
            proof_id = receipt.signature
            if proof_id in existing:
                continue
            entry_input = LedgerEntryInput(
                actor=self.actor,
                action=self.action,
                ref=self._reference_for(receipt),
                proof_id=proof_id,
                ts=_parse_timestamp(receipt.time),
            )
            if self.consensus_fabric is not None:
                self.consensus_fabric.ensure_round()
                vote = VotePayload(
                    voter=receipt.actor,
                    ballot=receipt.result,
                    weight=self.consensus_vote_weight,
                    signature=receipt.signature,
                )
                snapshot = self.consensus_fabric.register_vote(vote)
                entry_input = entry_input.model_copy(update={"consensus_round": snapshot})
            ledger_entry = self.temporal_ledger.append(entry_input)
            existing[proof_id] = ledger_entry
            appended.append(ledger_entry)
            if self.consensus_fabric is not None:
                self.consensus_fabric.record_ledger_entry(ledger_entry)
                if self.consensus_fabric.quorum_reached:
                    summary = (
                        f"Pulse receipts consensus quorum achieved for round "
                        f"{self.consensus_fabric.current_round_id}"
                    )
                    self.consensus_fabric.publish_wave(
                        summary=summary,
                        mode="pulse-cross-ledger",
                    )
        return appended

    def _reference_for(self, receipt: PulseReceipt) -> str:
        seed = receipt.seed if receipt.seed else "—"
        return f"{receipt.actor}:{receipt.result}:{receipt.sha256_of_diff}:{seed}"
