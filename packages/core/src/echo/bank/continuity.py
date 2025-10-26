"""Continuity safeguards that keep the Echo Bank ledger resilient."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass(slots=True)
class MirrorResult:
    """Result of mirroring a ledger artifact to a continuity location."""

    mirror_path: Path
    ledger_copy: Optional[Path]
    proof_copy: Optional[Path]
    ots_copy: Optional[Path]

    def to_record(self) -> dict[str, str]:
        record: dict[str, str] = {"mirror_path": str(self.mirror_path)}
        if self.ledger_copy:
            record["ledger_copy"] = str(self.ledger_copy)
        if self.proof_copy:
            record["proof_copy"] = str(self.proof_copy)
        if self.ots_copy:
            record["ots_copy"] = str(self.ots_copy)
        return record


@dataclass(slots=True)
class ContinuityConfig:
    """Configuration that guides how continuity safeguards run."""

    mirrors: List[Path]
    trustees: List[str]
    threshold: int = 2

    @classmethod
    def default(cls, base_dir: Path) -> "ContinuityConfig":
        mirror_root = base_dir / "mirrors"
        return cls(
            mirrors=[
                mirror_root / "ledger",
                mirror_root / "proofs",
                mirror_root / "ots",
            ],
            trustees=["Echo Bank", "Little Footsteps", "Echo Guardian"],
            threshold=2,
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "mirrors": [str(path) for path in self.mirrors],
            "trustees": self.trustees,
            "threshold": self.threshold,
        }


def _iso_now() -> str:
    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class ContinuitySafeguards:
    """Mirror ledger artifacts and log multi-sig recovery checkpoints."""

    def __init__(
        self,
        *,
        state_dir: Path | str = Path("state/continuity"),
        config: ContinuityConfig | None = None,
    ) -> None:
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.state_dir / "config.json"
        if config is None:
            config = self._load_or_create_config()
        else:
            self._persist_config(config)
        self.config = config
        for mirror in self.config.mirrors:
            mirror.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def mirror_artifacts(
        self,
        ledger_path: Path,
        proof_path: Path,
        ots_receipt: Optional[Path] = None,
    ) -> list[MirrorResult]:
        """Mirror the ledger and proof bundle to every configured location."""

        results: list[MirrorResult] = []
        for mirror in self.config.mirrors:
            ledger_copy = self._copy_if_exists(ledger_path, mirror / ledger_path.name)
            proof_copy = self._copy_if_exists(proof_path, mirror / proof_path.name)
            ots_copy = None
            if ots_receipt is not None:
                ots_copy = self._copy_if_exists(ots_receipt, mirror / ots_receipt.name)
            results.append(MirrorResult(mirror_path=mirror, ledger_copy=ledger_copy, proof_copy=proof_copy, ots_copy=ots_copy))
        return results

    def record_multisig_checkpoint(self, seq: int, digest: str) -> Path:
        """Append a checkpoint describing how trustees can recover the ledger."""

        payload = {
            "seq": seq,
            "digest": digest,
            "timestamp": _iso_now(),
            "threshold": self.config.threshold,
            "trustees": self.config.trustees,
        }
        checkpoint_path = self.state_dir / "multisig_recovery.jsonl"
        with checkpoint_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
        return checkpoint_path

    def continuity_report(self) -> dict[str, object]:
        """Return a snapshot describing the configured safeguards."""

        checkpoint_path = self.state_dir / "multisig_recovery.jsonl"
        checkpoints: list[dict[str, object]] = []
        if checkpoint_path.exists():
            for line in checkpoint_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                checkpoints.append(json.loads(line))
        return {
            "config": self.config.to_payload(),
            "checkpoints": checkpoints,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _copy_if_exists(self, source: Path, destination: Path) -> Optional[Path]:
        if not source.exists():
            return None
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        return destination

    def _load_or_create_config(self) -> ContinuityConfig:
        if self.config_path.exists():
            payload = json.loads(self.config_path.read_text(encoding="utf-8"))
            mirrors = [Path(entry) for entry in payload.get("mirrors", [])]
            trustees = payload.get("trustees", ["Echo Bank", "Little Footsteps", "Echo Guardian"])
            threshold = int(payload.get("threshold", 2))
            return ContinuityConfig(mirrors=mirrors, trustees=trustees, threshold=threshold)
        config = ContinuityConfig.default(self.state_dir)
        self._persist_config(config)
        return config

    def _persist_config(self, config: ContinuityConfig) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(config.to_payload(), indent=2), encoding="utf-8")
