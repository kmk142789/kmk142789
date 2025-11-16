"""Short-lived encrypted shadow memories with zero-knowledge attestations."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import base64
import hashlib
import json
import secrets
from typing import Callable, Mapping, MutableMapping, Sequence

from ..privacy import (
    EventCommitmentCircuit,
    HashCommitmentBackend,
    ProofClaim,
    ProofResult,
    ZeroKnowledgePrivacyLayer,
)

__all__ = [
    "ShadowMemoryPolicy",
    "ShadowMemoryRecord",
    "ShadowDecisionAttestation",
    "ShadowMemorySnapshot",
    "ShadowMemoryManager",
]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _tokenize(text: str) -> set[str]:
    tokens = {token.lower() for token in text.replace("/", " ").split() if token}
    return {token.strip(".,:;!?()[]{}") for token in tokens if token}


@dataclass(slots=True)
class ShadowMemoryPolicy:
    """Controls how long shadow memories survive."""

    default_ttl_seconds: int = 300
    min_ttl_seconds: int = 30
    max_ttl_seconds: int = 900

    def clamp(self, requested: int | None = None) -> int:
        ttl = requested or self.default_ttl_seconds
        ttl = max(self.min_ttl_seconds, ttl)
        ttl = min(self.max_ttl_seconds, ttl)
        return ttl


@dataclass(slots=True)
class ShadowMemoryRecord:
    """Encrypted payload plus commitment metadata."""

    shadow_id: str
    created_at: datetime
    expires_at: datetime
    encrypted_payload: str
    payload_digest: str
    tags: tuple[str, ...]
    metadata: Mapping[str, object]
    commitment: str
    proof: ProofResult | None


@dataclass(slots=True)
class ShadowDecisionAttestation:
    """Proof artifact linking decisions to shadow memories."""

    decision_id: str
    commitment: str
    record_ids: tuple[str, ...]
    generated_at: str
    proof: ProofResult | None = None

    def as_dict(self) -> MutableMapping[str, object]:
        payload: MutableMapping[str, object] = {
            "decision_id": self.decision_id,
            "commitment": self.commitment,
            "record_ids": list(self.record_ids),
            "generated_at": self.generated_at,
        }
        if self.proof:
            payload["proof"] = {
                "claim_id": self.proof.claim_id,
                "commitment": self.proof.commitment,
                "circuit": self.proof.circuit,
                "backend": self.proof.backend,
                "verified": self.proof.verified,
            }
        return payload


@dataclass(slots=True)
class ShadowMemorySnapshot:
    """Externally consumable snapshot of the manager."""

    active_count: int
    commitments: tuple[str, ...]
    next_expiration: str | None
    attestations: tuple[MutableMapping[str, object], ...]

    def as_dict(self) -> MutableMapping[str, object]:
        return {
            "active_count": self.active_count,
            "commitments": list(self.commitments),
            "next_expiration": self.next_expiration,
            "attestations": list(self.attestations),
        }


class ShadowMemoryManager:
    """Creates encrypted, auto-expiring shadow memories."""

    def __init__(
        self,
        *,
        privacy_layer: ZeroKnowledgePrivacyLayer | None = None,
        policy: ShadowMemoryPolicy | None = None,
        clock: Callable[[], datetime] = _utc_now,
        attestation_limit: int = 32,
    ) -> None:
        self._privacy = privacy_layer
        self._policy = policy or ShadowMemoryPolicy()
        self._clock = clock
        self._records: dict[str, ShadowMemoryRecord] = {}
        self._attestations: deque[ShadowDecisionAttestation] = deque(
            maxlen=max(1, attestation_limit)
        )
        self._event_circuit_registered = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def create_shadow_memory(
        self,
        payload: Mapping[str, object] | Sequence[object] | str,
        *,
        ttl_seconds: int | None = None,
        tags: Sequence[str] | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> ShadowMemoryRecord:
        """Encrypt ``payload`` and register it as a short-lived memory."""

        self._sweep()
        shadow_id = secrets.token_hex(8)
        payload_text = self._serialise_payload(payload)
        secret = secrets.token_hex(16)
        encrypted_payload = self._encrypt(payload_text, secret)
        payload_digest = hashlib.blake2b(
            payload_text.encode(), digest_size=32
        ).hexdigest()
        ttl = self._policy.clamp(ttl_seconds)
        expires_at = self._clock() + timedelta(seconds=ttl)
        proof: ProofResult | None = None
        commitment = payload_digest
        if self._privacy:
            self._ensure_privacy_support()
            claim = ProofClaim(
                claim_id=f"shadow::{shadow_id}",
                claim_type="event_commitment",
                subject="shadow-memory",
                statement={"event_hash": payload_digest},
                private_inputs={"payload_secret": secret},
                context={"shadow_id": shadow_id},
            )
            proof = self._privacy.prove("event_commitment", claim)
            commitment = proof.commitment
        record = ShadowMemoryRecord(
            shadow_id=shadow_id,
            created_at=self._clock(),
            expires_at=expires_at,
            encrypted_payload=encrypted_payload,
            payload_digest=payload_digest,
            tags=tuple(tags or ()),
            metadata=dict(metadata or {}),
            commitment=commitment,
            proof=proof,
        )
        self._records[shadow_id] = record
        return record

    def active_commitments(self) -> list[str]:
        self._sweep()
        return [record.commitment for record in self._records.values()]

    def intent_tokens(self) -> set[str]:
        self._sweep()
        tokens: set[str] = set()
        for record in self._records.values():
            for tag in record.tags:
                tokens.update(_tokenize(tag))
        return tokens

    def attest_influence(
        self,
        *,
        decision_id: str,
        record_ids: Sequence[str] | None = None,
    ) -> ShadowDecisionAttestation | None:
        self._sweep()
        if not self._records:
            return None
        if record_ids:
            records = [self._records[rid] for rid in record_ids if rid in self._records]
        else:
            records = list(self._records.values())
        if not records:
            return None
        commitment_material = "|".join(sorted(record.commitment for record in records))
        digest = hashlib.blake2b(
            f"{decision_id}|{commitment_material}".encode(), digest_size=32
        ).hexdigest()
        secret = secrets.token_hex(16)
        proof: ProofResult | None = None
        if self._privacy:
            self._ensure_privacy_support()
            claim = ProofClaim(
                claim_id=f"influence::{decision_id}::{secrets.token_hex(4)}",
                claim_type="event_commitment",
                subject="shadow-memory",
                statement={"event_hash": digest},
                private_inputs={"payload_secret": secret},
                context={
                    "shadow_records": [record.shadow_id for record in records],
                    "decision_id": decision_id,
                },
            )
            proof = self._privacy.prove("event_commitment", claim)
            commitment = proof.commitment
        else:
            commitment = digest
        attestation = ShadowDecisionAttestation(
            decision_id=decision_id,
            commitment=commitment,
            record_ids=tuple(record.shadow_id for record in records),
            generated_at=self._clock().isoformat(),
            proof=proof,
        )
        self._attestations.append(attestation)
        return attestation

    def snapshot(self) -> ShadowMemorySnapshot:
        self._sweep()
        commitments = tuple(record.commitment for record in self._records.values())
        next_expiration = None
        if self._records:
            next_expiration = min(record.expires_at for record in self._records.values())
        return ShadowMemorySnapshot(
            active_count=len(self._records),
            commitments=commitments,
            next_expiration=next_expiration.isoformat() if next_expiration else None,
            attestations=tuple(att.as_dict() for att in self._attestations),
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _sweep(self) -> None:
        now = self._clock()
        expired = [key for key, record in self._records.items() if record.expires_at <= now]
        for key in expired:
            self._records.pop(key, None)

    def _serialise_payload(
        self, payload: Mapping[str, object] | Sequence[object] | str
    ) -> str:
        if isinstance(payload, str):
            return payload
        return json.dumps(payload, sort_keys=True, default=str)

    def _encrypt(self, payload: str, secret: str) -> str:
        key = hashlib.blake2b(secret.encode(), digest_size=32).digest()
        data = payload.encode()
        cipher = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
        return base64.b64encode(cipher).decode()

    def _ensure_privacy_support(self) -> None:
        if not self._privacy:
            return
        if "hash_commitment" not in self._privacy.available_backends():
            self._privacy.register_backend(HashCommitmentBackend())
        if not self._event_circuit_registered:
            self._privacy.register_circuit(EventCommitmentCircuit())
            self._event_circuit_registered = True
