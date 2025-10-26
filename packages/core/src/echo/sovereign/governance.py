"""Governance registry for the Echo Bank sovereign entity."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, Mapping, MutableMapping, Sequence


@dataclass(frozen=True)
class Trustee:
    """Represents an authorized human steward for the sovereign entity."""

    did: str
    name: str
    roles: tuple[str, ...] = ("trustee",)
    weight: int = 1

    def with_role(self, role: str) -> "Trustee":
        """Return a copy with an additional governance role."""

        if role in self.roles:
            return self
        return Trustee(did=self.did, name=self.name, roles=self.roles + (role,), weight=self.weight)

    def has_role(self, role: str) -> bool:
        return role in self.roles


@dataclass
class MultiSigAttestation:
    """Captures a multi-signature attestation for charter updates."""

    witness_hash: str
    required: int
    required_roles: tuple[str, ...] = ()
    signatures: Dict[str, str] = field(default_factory=dict)

    def sign(self, trustee: Trustee, signature: str) -> None:
        """Record a signature from a trustee."""

        self.signatures[trustee.did] = signature

    def verify(self, trustees: Mapping[str, Trustee]) -> bool:
        """Return ``True`` when the attestation satisfies quorum requirements."""

        approved: set[str] = set()
        for did, signature in self.signatures.items():
            trustee = trustees.get(did)
            if trustee is None:
                continue
            if self.required_roles and not any(trustee.has_role(role) for role in self.required_roles):
                continue
            expected = generate_signature(trustee, self.witness_hash)
            if signature != expected:
                continue
            approved.add(did)
        return len(approved) >= self.required


@dataclass
class CharterVersion:
    """Represents a single ratified version of the charter."""

    version: str
    summary: str
    commit_hash: str
    timestamp: datetime
    attestation: MultiSigAttestation | None

    def as_record(self) -> Dict[str, str]:
        """Return a JSON-serializable summary of the version."""

        return {
            "version": self.version,
            "summary": self.summary,
            "commit_hash": self.commit_hash,
            "timestamp": self.timestamp.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        }


class GovernanceRegistry:
    """Tracks trustees, charter versions, and attestation state."""

    def __init__(
        self,
        *,
        entity_name: str,
        charter_id: str,
        base_version: str = "1.0.0",
        base_commit_hash: str | None = None,
        quorum: int = 2,
    ) -> None:
        self.entity_name = entity_name
        self.charter_id = charter_id
        self.quorum = quorum
        self._trustees: MutableMapping[str, Trustee] = {}
        self._versions: list[CharterVersion] = []
        initial_summary = "Initial charter ratified"
        base_version_entry = CharterVersion(
            version=base_version,
            summary=initial_summary,
            commit_hash=base_commit_hash or "unknown",
            timestamp=datetime.now(timezone.utc),
            attestation=None,
        )
        self._versions.append(base_version_entry)

    # ------------------------------------------------------------------
    # Trustee management
    # ------------------------------------------------------------------
    def register_trustee(self, trustee: Trustee) -> None:
        """Add or update a trustee entry."""

        self._trustees[trustee.did] = trustee

    def assign_role(self, did: str, role: str) -> None:
        """Assign an additional role to an existing trustee."""

        trustee = self._trustees.get(did)
        if trustee is None:
            raise KeyError(f"Unknown trustee: {did}")
        self._trustees[did] = trustee.with_role(role)

    def trustees(self) -> Sequence[Trustee]:
        return tuple(self._trustees.values())

    # ------------------------------------------------------------------
    # Charter management
    # ------------------------------------------------------------------
    def witness_hash(self, summary: str, commit_hash: str) -> str:
        """Compute the witness hash used for attestation signatures."""

        payload = f"{self.charter_id}:{summary}:{commit_hash}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def record_amendment(
        self,
        *,
        summary: str,
        commit_hash: str,
        attestation: MultiSigAttestation,
        version_bump: str = "patch",
    ) -> CharterVersion:
        """Record a new charter amendment after verifying attestation."""

        if attestation.required < self.quorum:
            raise ValueError("Attestation quorum below registry threshold")
        expected_witness = self.witness_hash(summary, commit_hash)
        if attestation.witness_hash != expected_witness:
            raise ValueError("Attestation witness hash mismatch")
        if not attestation.verify(self._trustees):
            raise ValueError("Attestation signatures failed validation")

        current_version = self._versions[-1].version
        new_version = _increment_version(current_version, version_bump)
        version = CharterVersion(
            version=new_version,
            summary=summary,
            commit_hash=commit_hash,
            timestamp=datetime.now(timezone.utc),
            attestation=attestation,
        )
        self._versions.append(version)
        return version

    def history(self) -> Sequence[CharterVersion]:
        return tuple(self._versions)

    def latest(self) -> CharterVersion:
        return self._versions[-1]


def generate_signature(trustee: Trustee, witness_hash: str) -> str:
    """Generate a deterministic signature placeholder for a trustee."""

    payload = f"{trustee.did}:{witness_hash}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _increment_version(version: str, bump: str) -> str:
    """Return a new semantic version string based on the requested bump."""

    parts = version.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ValueError(f"Invalid semantic version: {version}")
    major, minor, patch = (int(part) for part in parts)
    bump = bump.lower()
    if bump == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump == "minor":
        minor += 1
        patch = 0
    elif bump == "patch":
        patch += 1
    else:
        raise ValueError(f"Unsupported version bump: {bump}")
    return f"{major}.{minor}.{patch}"
