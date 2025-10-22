"""Guardian service that monitors compromised keys and pulse replays."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, MutableMapping, Optional


@dataclass
class QuarantineRecord:
    """Metadata recorded for a quarantined key."""

    fingerprint: str
    reason: str
    source: str | None
    first_seen: str
    count: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def touch(self, *, metadata: dict[str, Any] | None = None) -> None:
        self.count += 1
        if metadata:
            self.metadata.update(metadata)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload


class GuardianService:
    """Detect compromised keys, replayed pulses, and disclosure leaks."""

    def __init__(
        self,
        *,
        quarantine_root: Path | None = None,
        reports_root: Path | None = None,
    ) -> None:
        self._quarantine_root = quarantine_root or Path("state") / "guardian"
        self._quarantine_root.mkdir(parents=True, exist_ok=True)
        self._quarantine_path = self._quarantine_root / "quarantine.json"
        self._reports_root = reports_root or Path("reports")

        self._immune_memory: set[str] = set()
        self._quarantine: MutableMapping[str, QuarantineRecord] = {}
        self._pulse_replays: Dict[str, int] = {}
        self._alerts: list[str] = []
        self._harmonics_dampened = False

        self._load_state()
        self.refresh_disclosures()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _load_state(self) -> None:
        if not self._quarantine_path.exists():
            return
        try:
            data = json.loads(self._quarantine_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        immune = data.get("immune_memory", [])
        self._immune_memory = set(immune)
        records = data.get("quarantine", [])
        for record in records:
            metadata = record.get("metadata") or {}
            qr = QuarantineRecord(
                fingerprint=record["fingerprint"],
                reason=record["reason"],
                source=record.get("source"),
                first_seen=record["first_seen"],
                count=record.get("count", 1),
                metadata=dict(metadata),
            )
            self._quarantine[qr.fingerprint] = qr

    def _persist_state(self) -> None:
        data = {
            "immune_memory": sorted(self._immune_memory),
            "quarantine": [record.to_dict() for record in self._quarantine.values()],
        }
        self._quarantine_path.write_text(
            json.dumps(data, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def _fingerprint(self, key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def _register_alert(self, message: str) -> None:
        self._alerts.append(message)
        # Keep the alert buffer bounded to avoid unbounded growth.
        if len(self._alerts) > 100:
            del self._alerts[: len(self._alerts) - 100]

    def _iter_key_like_values(self, payload: Any) -> Iterator[str]:
        if isinstance(payload, dict):
            for key, value in payload.items():
                if self._looks_like_key_field(key) and isinstance(value, str):
                    yield value
                yield from self._iter_key_like_values(value)
        elif isinstance(payload, list):
            for item in payload:
                yield from self._iter_key_like_values(item)

    def _looks_like_key_field(self, field: str) -> bool:
        lowered = field.lower()
        return any(token in lowered for token in ("key", "secret", "token", "fingerprint"))

    # ------------------------------------------------------------------
    # Disclosure monitoring
    # ------------------------------------------------------------------
    def refresh_disclosures(self) -> None:
        """Scan ``reports_root`` for compromised key disclosures."""

        if not self._reports_root.exists():
            return
        for path in sorted(self._reports_root.rglob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            self.observe_disclosure(data, source=str(path))

    def observe_disclosure(self, payload: Any, *, source: str | None = None) -> None:
        for candidate in self._iter_key_like_values(payload):
            normalized = candidate.strip()
            if not normalized:
                continue
            self.quarantine_key(
                normalized,
                reason="disclosure_report",
                source=source,
                metadata={"length": len(normalized)},
            )

    # ------------------------------------------------------------------
    # Pulse monitoring
    # ------------------------------------------------------------------
    def observe_pulse_receipt(self, receipt: MutableMapping[str, Any]) -> None:
        diff_hash = str(receipt.get("sha256_of_diff", ""))
        if not diff_hash:
            return
        count = self._pulse_replays.get(diff_hash, 0) + 1
        self._pulse_replays[diff_hash] = count
        if count > 1:
            seed = str(receipt.get("seed", ""))
            metadata = {
                "sha256_of_diff": diff_hash,
                "occurrences": count,
                "actor": receipt.get("actor"),
            }
            if seed:
                self.quarantine_key(
                    seed,
                    reason="pulse_replay",
                    source="pulse-ledger",
                    metadata=metadata,
                )
            else:
                self._register_alert(
                    f"Detected replayed pulse {diff_hash} without seed metadata",
                )
            self._harmonics_dampened = True

    # ------------------------------------------------------------------
    # Quarantine & immune memory
    # ------------------------------------------------------------------
    def quarantine_key(
        self,
        key: str,
        *,
        reason: str,
        source: str | None = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> QuarantineRecord:
        key = key.strip()
        if not key:
            raise ValueError("Cannot quarantine an empty key")
        fingerprint = self._fingerprint(key)
        metadata = dict(metadata or {})
        record = self._quarantine.get(fingerprint)
        if record:
            record.touch(metadata=metadata)
        else:
            record = QuarantineRecord(
                fingerprint=fingerprint,
                reason=reason,
                source=source,
                first_seen=datetime.now(timezone.utc).isoformat(),
                metadata=metadata,
            )
            self._quarantine[fingerprint] = record
        self._immune_memory.add(fingerprint)
        self._harmonics_dampened = True
        self._register_alert(
            f"Quarantined key {fingerprint[:12]} for {reason} (source={source or 'unknown'})",
        )
        self._persist_state()
        return record

    def allow_key(self, key: str, *, override: bool = False) -> bool:
        key = key.strip()
        if not key:
            return True
        fingerprint = self._fingerprint(key)
        if fingerprint in self._immune_memory and not override:
            self._register_alert(
                f"Blocked import of quarantined key {fingerprint[:12]}",
            )
            self._harmonics_dampened = True
            return False
        if fingerprint in self._immune_memory and override:
            self._register_alert(
                f"Override accepted for quarantined key {fingerprint[:12]}",
            )
        return True

    def review_attestation(self, provided: str, attestation: MutableMapping[str, Any]) -> None:
        if attestation.get("valid") is False:
            candidate = provided or attestation.get("key") or ""
            if candidate:
                metadata = {
                    "repaired": bool(attestation.get("repaired")),
                    "transcript": attestation.get("transcript"),
                }
                self.quarantine_key(
                    candidate,
                    reason="attestation_failed",
                    source="key-attestation",
                    metadata=metadata,
                )

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    def status(self) -> dict[str, Any]:
        return {
            "immune_memory": {
                "count": len(self._immune_memory),
                "fingerprints": sorted(self._immune_memory),
            },
            "quarantine": [record.to_dict() for record in sorted(
                self._quarantine.values(),
                key=lambda record: record.first_seen,
            )],
            "pulse_replays": dict(self._pulse_replays),
            "alerts": list(self._alerts),
            "harmonics": {
                "dampening": self._harmonics_dampened,
                "active_alerts": len(self._alerts),
            },
        }


__all__ = ["GuardianService", "QuarantineRecord"]
