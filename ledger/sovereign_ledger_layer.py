"""Sovereign Ledger layer that binds amendments to verifiable credentials.

The layer computes digests for ratified amendments, emits verifiable
credential payloads, and records registry entries so downstream systems
(or on-chain mappers) can verify which constitutional texts are active.
It also tracks autonomous feature plans so roadmap items can be audited
against their constitutional anchors.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence


@dataclass(slots=True)
class AmendmentCredentialRecord:
    """Content-addressed credential record for a ratified amendment."""

    amendment_id: str
    title: str
    credential_id: str
    amendment_digest: str
    issued_at: str
    issuer: str
    ledger_anchor: str
    credential_path: str
    proof_bundle: Optional[str] = None
    schema_uri: Optional[str] = None

    def to_payload(self) -> Dict[str, Optional[str]]:
        return asdict(self)


@dataclass(slots=True)
class AutonomousFeatureRecord:
    """Roadmap entry mapped to a constitutional anchor."""

    feature_id: str
    codename: str
    amendment_reference: str
    objective: str
    success_criteria: List[str]
    ledger_anchor: str
    issued_at: str
    digest: str
    artifact_path: str

    def to_payload(self) -> Dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class AutonomousFeatureUpgradeRecord:
    """Upgrade event that links a feature to its successor artifact."""

    upgrade_id: str
    from_feature_id: str
    to_feature_id: str
    codename: str
    reason: str
    ledger_anchor: str
    issued_at: str
    digest: str
    artifact_path: str

    def to_payload(self) -> Dict[str, object]:
        return asdict(self)


class SovereignLedgerLayer:
    """Map constitutional amendments and features to verifiable credentials."""

    def __init__(
        self,
        *,
        registry_path: Path,
        credential_dir: Path,
        feature_registry_path: Optional[Path] = None,
        feature_upgrade_registry_path: Optional[Path] = None,
    ) -> None:
        self.registry_path = registry_path
        self.credential_dir = credential_dir
        self.feature_registry_path = feature_registry_path or registry_path.parent / "autonomous_features.jsonl"
        self.feature_upgrade_registry_path = feature_upgrade_registry_path or registry_path.parent / "autonomous_feature_upgrades.jsonl"
        self.credential_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.feature_registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.feature_upgrade_registry_path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Amendment credentials
    # ------------------------------------------------------------------
    def issue_amendment_credential(
        self,
        *,
        amendment_path: Path,
        amendment_id: str,
        title: str,
        issuer: str,
        ledger_anchor: str,
        schema_uri: str = "https://schemas.echo/sovereign-ledger/amendment-vc-v1",
        proof_bundle: Optional[str] = None,
    ) -> AmendmentCredentialRecord:
        content = amendment_path.read_text(encoding="utf-8")
        digest = self._sha256_hex(content.encode("utf-8"))
        issued_at = self._iso_now()
        credential_id = f"vc:echo:amendment:{amendment_id.lower()}:{digest[:12]}"
        credential_payload = {
            "@context": ["https://www.w3.org/2018/credentials/v1", schema_uri],
            "id": credential_id,
            "type": ["VerifiableCredential", "EchoAmendmentCredential"],
            "issuer": issuer,
            "issuanceDate": issued_at,
            "credentialSubject": {
                "id": f"urn:echo:amendment:{amendment_id.lower()}",
                "title": title,
                "digest": digest,
                "ledger_anchor": ledger_anchor,
                "proof_bundle": proof_bundle,
            },
        }
        credential_path = self.credential_dir / f"amendment_{amendment_id.lower()}_credential.vc.json"
        credential_path.write_text(json.dumps(credential_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        record = AmendmentCredentialRecord(
            amendment_id=amendment_id,
            title=title,
            credential_id=credential_id,
            amendment_digest=digest,
            issued_at=issued_at,
            issuer=issuer,
            ledger_anchor=ledger_anchor,
            credential_path=str(credential_path),
            proof_bundle=proof_bundle,
            schema_uri=schema_uri,
        )
        self._append_registry_record(record)
        return record

    def _append_registry_record(self, record: AmendmentCredentialRecord) -> None:
        payload = record.to_payload()
        with self.registry_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    # ------------------------------------------------------------------
    # Autonomous feature recording
    # ------------------------------------------------------------------
    def record_autonomous_feature(
        self,
        *,
        codename: str,
        amendment_reference: str,
        objective: str,
        success_criteria: Iterable[str],
        ledger_anchor: str,
        artifact_path: Path,
    ) -> AutonomousFeatureRecord:
        issued_at = self._iso_now()
        digest = self._sha256_hex(artifact_path.read_bytes())
        feature_id = f"feature:{digest[:16]}"
        record = AutonomousFeatureRecord(
            feature_id=feature_id,
            codename=codename,
            amendment_reference=amendment_reference,
            objective=objective,
            success_criteria=list(success_criteria),
            ledger_anchor=ledger_anchor,
            issued_at=issued_at,
            digest=digest,
            artifact_path=str(artifact_path),
        )
        payload = record.to_payload()
        with self.feature_registry_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
        return record

    def record_autonomous_feature_upgrade(
        self,
        *,
        base_feature_id: str,
        codename: str,
        reason: str,
        ledger_anchor: str,
        artifact_path: Path,
    ) -> AutonomousFeatureUpgradeRecord:
        """Register an upgrade for an existing autonomous feature artifact.

        The upgrade record links the previous feature snapshot to the new
        artifact digest so downstream systems can trace upgrade lineage and
        validate ledger anchors.
        """

        feature_index = {entry.feature_id: entry for entry in self.load_autonomous_features()}
        if base_feature_id not in feature_index:
            raise ValueError(f"Unknown feature id: {base_feature_id}")

        issued_at = self._iso_now()
        digest = self._sha256_hex(artifact_path.read_bytes())
        to_feature_id = f"feature:{digest[:16]}"
        upgrade_id = f"feature-upgrade:{digest[:12]}"
        record = AutonomousFeatureUpgradeRecord(
            upgrade_id=upgrade_id,
            from_feature_id=base_feature_id,
            to_feature_id=to_feature_id,
            codename=codename,
            reason=reason,
            ledger_anchor=ledger_anchor,
            issued_at=issued_at,
            digest=digest,
            artifact_path=str(artifact_path),
        )
        with self.feature_upgrade_registry_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_payload(), sort_keys=True) + "\n")
        return record

    def load_autonomous_features(self) -> Sequence[AutonomousFeatureRecord]:
        """Load feature records from the registry JSONL file."""

        if not self.feature_registry_path.exists():
            return []

        records: list[AutonomousFeatureRecord] = []
        with self.feature_registry_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                payload = json.loads(line)
                records.append(AutonomousFeatureRecord(**payload))
        return records

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _sha256_hex(payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def _iso_now() -> str:
        return (
            datetime.now(tz=timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )
