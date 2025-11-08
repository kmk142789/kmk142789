"""Resilience helpers that evaluate mirror health and persist metrics."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Optional, Sequence

from .continuity import MirrorResult


def _iso_now() -> str:
    """Return the current UTC time formatted in ISO-8601 with a ``Z`` suffix."""

    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _to_path(value: Optional[Path | str]) -> Optional[Path]:
    if value is None:
        return None
    if isinstance(value, Path):
        return value
    return Path(value)


@dataclass(slots=True)
class ResilienceProbe:
    """Describe the artifacts that should exist for a mirrored location."""

    mirror_path: Path
    ledger_copy: Optional[Path] = None
    proof_copy: Optional[Path] = None
    ots_copy: Optional[Path] = None

    @classmethod
    def from_mirror_result(cls, result: MirrorResult) -> "ResilienceProbe":
        """Build a probe from a :class:`~echo.bank.continuity.MirrorResult`."""

        return cls(
            mirror_path=result.mirror_path,
            ledger_copy=_to_path(result.ledger_copy),
            proof_copy=_to_path(result.proof_copy),
            ots_copy=_to_path(result.ots_copy),
        )


@dataclass(slots=True)
class MirrorHealth:
    """Health summary for a single mirror target."""

    mirror_path: Path
    ledger_ok: bool
    proof_ok: bool
    ots_ok: bool
    issues: list[str] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return not self.issues

    def to_payload(self) -> dict[str, object]:
        return {
            "mirror_path": str(self.mirror_path),
            "ledger_ok": self.ledger_ok,
            "proof_ok": self.proof_ok,
            "ots_ok": self.ots_ok,
            "issues": list(self.issues),
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> "MirrorHealth":
        issues = payload.get("issues")
        if isinstance(issues, Sequence):
            issue_list = [str(item) for item in issues]
        else:
            issue_list = []
        return cls(
            mirror_path=Path(str(payload.get("mirror_path", ""))),
            ledger_ok=bool(payload.get("ledger_ok", False)),
            proof_ok=bool(payload.get("proof_ok", False)),
            ots_ok=bool(payload.get("ots_ok", False)),
            issues=issue_list,
        )


@dataclass(slots=True)
class ResilienceSnapshot:
    """Aggregated resilience metrics captured after a continuity checkpoint."""

    seq: int
    digest: str
    recorded_at: str
    failover_ready: bool
    healthy_mirrors: int
    total_mirrors: int
    mirrors: list[MirrorHealth]
    issues: list[str]
    checkpoint_path: Optional[Path] = None

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "seq": self.seq,
            "digest": self.digest,
            "recorded_at": self.recorded_at,
            "failover_ready": self.failover_ready,
            "healthy_mirrors": self.healthy_mirrors,
            "total_mirrors": self.total_mirrors,
            "mirrors": [mirror.to_payload() for mirror in self.mirrors],
            "issues": list(self.issues),
        }
        if self.checkpoint_path is not None:
            payload["checkpoint_path"] = str(self.checkpoint_path)
        return payload

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> "ResilienceSnapshot":
        mirrors_payload = payload.get("mirrors")
        mirrors: list[MirrorHealth] = []
        if isinstance(mirrors_payload, Sequence):
            for entry in mirrors_payload:
                if isinstance(entry, Mapping):
                    mirrors.append(MirrorHealth.from_payload(entry))
        issues_payload = payload.get("issues")
        issues = [str(item) for item in issues_payload] if isinstance(issues_payload, Sequence) else []
        checkpoint_path = payload.get("checkpoint_path")
        path_value = Path(str(checkpoint_path)) if checkpoint_path else None
        return cls(
            seq=int(payload.get("seq", 0)),
            digest=str(payload.get("digest", "")),
            recorded_at=str(payload.get("recorded_at", "")),
            failover_ready=bool(payload.get("failover_ready", False)),
            healthy_mirrors=int(payload.get("healthy_mirrors", 0)),
            total_mirrors=int(payload.get("total_mirrors", 0)),
            mirrors=mirrors,
            issues=issues,
            checkpoint_path=path_value,
        )


class ResilienceRecorder:
    """Persist mirror health snapshots to support resilience audits."""

    def __init__(
        self,
        *,
        state_dir: Path | str = Path("state/resilience"),
        min_failover_nodes: int = 2,
    ) -> None:
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self._history_path = self.state_dir / "resilience_metrics.jsonl"
        self._latest_path = self.state_dir / "latest.json"
        self._min_failover_nodes = max(1, int(min_failover_nodes))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def record_checkpoint(
        self,
        *,
        seq: int,
        digest: str,
        probes: Sequence[ResilienceProbe],
        checkpoint_path: Optional[Path] = None,
    ) -> ResilienceSnapshot:
        """Evaluate ``probes`` and persist a snapshot describing mirror health."""

        snapshot = self._build_snapshot(
            seq=seq,
            digest=digest,
            probes=probes,
            checkpoint_path=checkpoint_path,
        )
        self._persist(snapshot)
        return snapshot

    def latest_snapshot(self) -> Optional[ResilienceSnapshot]:
        """Return the most recently persisted snapshot, if available."""

        if not self._latest_path.exists():
            return None
        payload = json.loads(self._latest_path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):  # pragma: no cover - defensive
            return None
        return ResilienceSnapshot.from_payload(payload)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_snapshot(
        self,
        *,
        seq: int,
        digest: str,
        probes: Sequence[ResilienceProbe],
        checkpoint_path: Optional[Path],
    ) -> ResilienceSnapshot:
        mirrors: list[MirrorHealth] = []
        for probe in probes:
            mirrors.append(self._evaluate_probe(probe))
        healthy = sum(1 for mirror in mirrors if mirror.healthy)
        issues: list[str] = []
        for mirror in mirrors:
            issues.extend(mirror.issues)
        failover_ready = healthy >= self._min_failover_nodes
        return ResilienceSnapshot(
            seq=seq,
            digest=digest,
            recorded_at=_iso_now(),
            failover_ready=failover_ready,
            healthy_mirrors=healthy,
            total_mirrors=len(mirrors),
            mirrors=mirrors,
            issues=issues,
            checkpoint_path=checkpoint_path,
        )

    def _evaluate_probe(self, probe: ResilienceProbe) -> MirrorHealth:
        issues: list[str] = []
        ledger_ok = False
        proof_ok = False
        ots_ok = False

        if probe.ledger_copy is not None:
            ledger_ok = probe.ledger_copy.exists()
            if not ledger_ok:
                issues.append(f"Ledger copy missing at {probe.ledger_copy}")
        else:
            issues.append("Ledger copy path not provided")

        if probe.proof_copy is not None:
            proof_ok = probe.proof_copy.exists()
            if not proof_ok:
                issues.append(f"Proof bundle missing at {probe.proof_copy}")
        else:
            issues.append("Proof bundle path not provided")

        if probe.ots_copy is not None:
            ots_ok = probe.ots_copy.exists()
            if not ots_ok:
                issues.append(f"OTS receipt missing at {probe.ots_copy}")
        else:
            ots_ok = True  # Optional; absence should not fail the mirror outright

        return MirrorHealth(
            mirror_path=probe.mirror_path,
            ledger_ok=ledger_ok,
            proof_ok=proof_ok,
            ots_ok=ots_ok,
            issues=issues,
        )

    def _persist(self, snapshot: ResilienceSnapshot) -> None:
        payload = snapshot.to_payload()
        with self._history_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
        self._latest_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------
    @staticmethod
    def load_latest_snapshot(path: Path) -> Optional[ResilienceSnapshot]:
        """Load a snapshot from ``path`` if the file exists."""

        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            return None
        return ResilienceSnapshot.from_payload(payload)


__all__ = [
    "MirrorHealth",
    "ResilienceProbe",
    "ResilienceRecorder",
    "ResilienceSnapshot",
]

