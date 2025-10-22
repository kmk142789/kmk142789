"""Broadcast cross-ledger proofs for external attestation systems."""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence

from echo.atlas.temporal_ledger import LedgerEntry, TemporalLedger

from .ledger import PulseLedger, PulseReceipt

__all__ = [
    "CrossLedgerProof",
    "CrossLedgerBroadcast",
    "CrossLedgerBroadcaster",
]


@dataclass(slots=True)
class CrossLedgerProof:
    """Serialised proof representing a single cross-ledger linkage."""

    proof_id: str
    payload: Mapping[str, Any]
    json: str
    base64: str
    leaf_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proof_id": self.proof_id,
            "payload": self.payload,
            "json": self.json,
            "base64": self.base64,
            "leaf_hash": self.leaf_hash,
        }


@dataclass(slots=True)
class CrossLedgerBroadcast:
    """Bundle of proofs accompanied by a Merkle root anchor."""

    merkle_root: Optional[str]
    proofs: List[CrossLedgerProof]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "merkle_root": self.merkle_root,
            "proofs": [proof.to_dict() for proof in self.proofs],
        }


class CrossLedgerBroadcaster:
    """Export canonical proofs that bridge pulse receipts and temporal entries."""

    def __init__(self, *, pulse_ledger: PulseLedger, temporal_ledger: TemporalLedger) -> None:
        self._pulse_ledger = pulse_ledger
        self._temporal_ledger = temporal_ledger

    def build_bundle(self, *, limit: Optional[int] = None) -> CrossLedgerBroadcast:
        """Return a :class:`CrossLedgerBroadcast` describing known proofs."""

        entries = self._temporal_ledger.entries()
        if limit is not None:
            if limit <= 0:
                entries = []
            else:
                entries = entries[-limit:]

        receipt_index = {
            receipt.signature: receipt for receipt in self._pulse_ledger.iter_receipts()
        }

        proofs = [self._build_proof(entry, receipt_index.get(entry.proof_id)) for entry in entries]
        merkle_root = _compute_merkle_root([proof.leaf_hash for proof in proofs]) if proofs else None
        return CrossLedgerBroadcast(merkle_root=merkle_root, proofs=proofs)

    def _build_proof(self, entry: LedgerEntry, receipt: Optional[PulseReceipt]) -> CrossLedgerProof:
        payload: Dict[str, Any] = {
            "proof_id": entry.proof_id,
            "temporal_ledger": entry.to_dict(),
        }
        if receipt is not None:
            payload["pulse_receipt"] = receipt.to_dict()

        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        encoded = base64.b64encode(canonical.encode("utf-8")).decode("ascii")
        leaf_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return CrossLedgerProof(
            proof_id=entry.proof_id,
            payload=payload,
            json=canonical,
            base64=encoded,
            leaf_hash=leaf_hash,
        )


def _compute_merkle_root(leaf_hashes: Sequence[str]) -> str:
    """Return the Merkle root for the provided ``leaf_hashes``."""

    layer: List[bytes] = [bytes.fromhex(h) for h in leaf_hashes]
    while len(layer) > 1:
        if len(layer) % 2 == 1:
            layer.append(layer[-1])
        layer = [
            hashlib.sha256(layer[idx] + layer[idx + 1]).digest()
            for idx in range(0, len(layer), 2)
        ]
    return layer[0].hex()
