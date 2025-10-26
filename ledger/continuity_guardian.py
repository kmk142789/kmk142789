"""Continuity safeguards for Echo Bank sovereign ledger."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Optional


def _iso_now() -> str:
    return (
        datetime.now(tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


@dataclass(slots=True)
class Trustee:
    """Signatory that can participate in multi-sig recovery."""

    name: str
    contact: str
    public_key: Optional[str] = None

    def to_payload(self) -> Dict[str, Optional[str]]:
        return {
            "name": self.name,
            "contact": self.contact,
            "public_key": self.public_key,
        }


@dataclass(slots=True)
class MultiSigRecoveryPlan:
    """Description of trustee-controlled recovery posture."""

    trustees: List[Trustee]
    threshold: int
    recovery_contract: Optional[str] = None
    created_at: str = field(default_factory=_iso_now)

    def to_payload(self) -> Dict[str, object]:
        return {
            "trustees": [trustee.to_payload() for trustee in self.trustees],
            "threshold": self.threshold,
            "recovery_contract": self.recovery_contract,
            "created_at": self.created_at,
        }


@dataclass(slots=True)
class ReplicaNode:
    """Replica node that mirrors ledger artifacts."""

    name: str
    base_path: Path

    def ensure_structure(self) -> None:
        (self.base_path / "ledger").mkdir(parents=True, exist_ok=True)
        (self.base_path / "proofs").mkdir(parents=True, exist_ok=True)
        (self.base_path / "puzzles").mkdir(parents=True, exist_ok=True)
        (self.base_path / "compliance").mkdir(parents=True, exist_ok=True)

    def status_payload(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "path": os.fspath(self.base_path),
        }


class ContinuityGuardian:
    """Coordinates ledger mirroring and recovery state exports."""

    def __init__(
        self,
        *,
        bank: str,
        state_path: Path,
        mirror_nodes: Iterable[ReplicaNode],
        recovery_plan: Optional[MultiSigRecoveryPlan] = None,
    ) -> None:
        self.bank = bank
        self.state_path = state_path
        self.mirror_nodes = list(mirror_nodes)
        self.recovery_plan = recovery_plan
        if self.state_path.parent:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
        for node in self.mirror_nodes:
            node.ensure_structure()

    # ------------------------------------------------------------------
    # Synchronisation
    # ------------------------------------------------------------------

    def sync_entry(
        self,
        *,
        entry: "LedgerEntry",
        digest: str,
        ledger_path: Path,
        puzzle_path: Path,
        proof_path: Path,
        compliance_credential: Optional[Path] = None,
    ) -> None:
        if not self.mirror_nodes:
            self._export_state(entry, digest)
            return

        for node in self.mirror_nodes:
            self._copy(ledger_path, node.base_path / "ledger" / ledger_path.name)
            self._copy(puzzle_path, node.base_path / "puzzles" / puzzle_path.name)
            self._copy(proof_path, node.base_path / "proofs" / proof_path.name)
            if compliance_credential is not None and compliance_credential.exists():
                self._copy(
                    compliance_credential,
                    node.base_path / "compliance" / compliance_credential.name,
                )

        self._export_state(entry, digest)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _copy(self, source: Path, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    def _export_state(self, entry: "LedgerEntry", digest: str) -> None:
        payload = {
            "bank": self.bank,
            "last_seq": entry.seq,
            "last_digest": digest,
            "state_exported_at": _iso_now(),
            "mirrors": [node.status_payload() for node in self.mirror_nodes],
        }
        if self.recovery_plan:
            payload["recovery_plan"] = self.recovery_plan.to_payload()
        self.state_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


try:  # pragma: no cover - typing helper
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:  # pragma: no cover
        from .little_footsteps_bank import LedgerEntry
except Exception:  # pragma: no cover
    pass
