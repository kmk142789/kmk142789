"""Cross-jurisdiction trust fabric built from verifiable attestations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence

from .verifiable_credentials import CredentialVerificationError, verify_credential


def _parse_datetime(value: Any) -> Optional[datetime]:
    """Parse an ISO formatted datetime string into a :class:`datetime` object."""

    if not isinstance(value, str):
        return None
    candidate = value
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    return parsed


def _coerce_confidence(value: Any, default: float = 1.0) -> float:
    """Return ``value`` as a bounded confidence score between ``0`` and ``1``."""

    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, confidence))


@dataclass
class TrustEntity:
    """Represents a DID-backed entity that participates in the trust fabric."""

    did: str
    jurisdiction: Optional[str] = None
    entity_type: Optional[str] = None
    display_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update(self, payload: Mapping[str, Any]) -> None:
        """Merge contextual metadata from a credential subject or claim payload."""

        jurisdiction = payload.get("jurisdiction")
        if isinstance(jurisdiction, str):
            self.jurisdiction = jurisdiction

        entity_type = payload.get("entityType") or payload.get("type")
        if isinstance(entity_type, str):
            self.entity_type = entity_type

        display_name = payload.get("displayName") or payload.get("name")
        if isinstance(display_name, str):
            self.display_name = display_name

        metadata = payload.get("metadata")
        if isinstance(metadata, Mapping):
            self.metadata.update({str(k): metadata[k] for k in metadata})


@dataclass(frozen=True)
class TrustLink:
    """Directed relationship between two DIDs backed by an attestation."""

    source: str
    target: str
    relationship: str
    attestation_id: str
    issued_at: datetime
    expires_at: Optional[datetime]
    confidence: float = 1.0
    evidence: Dict[str, Any] = field(default_factory=dict)


class CrossJurisdictionTrustFabric:
    """Aggregates cross-jurisdiction trust attestations into an explorable fabric."""

    def __init__(
        self,
        *,
        public_key_resolver: Callable[[str], Optional[str]],
        accepted_types: Optional[Sequence[str]] = None,
    ) -> None:
        self._public_key_resolver = public_key_resolver
        self._accepted_types = tuple(accepted_types) if accepted_types else None
        self._entities: MutableMapping[str, TrustEntity] = {}
        self._links: List[TrustLink] = []
        self._link_index: set[tuple[str, str, str, str]] = set()
        self._attestations: MutableMapping[str, Mapping[str, Any]] = {}

    # ------------------------------------------------------------------
    # Public accessors
    # ------------------------------------------------------------------
    @property
    def entities(self) -> Sequence[TrustEntity]:
        return tuple(self._entities.values())

    @property
    def links(self) -> Sequence[TrustLink]:
        return tuple(self._links)

    @property
    def attestations(self) -> Mapping[str, Mapping[str, Any]]:
        return dict(self._attestations)

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------
    def ingest(self, credential: Mapping[str, Any]) -> Sequence[TrustLink]:
        """Validate *credential* and add its trust relationships to the fabric."""

        attestation_id = self._extract_attestation_id(credential)
        if attestation_id in self._attestations:
            return tuple(link for link in self._links if link.attestation_id == attestation_id)

        issuer_did = self._extract_issuer_did(credential)
        verification_key = self._public_key_resolver(issuer_did)
        if not isinstance(verification_key, str):
            raise CredentialVerificationError(f"Missing verification key for issuer: {issuer_did}")

        if self._accepted_types is not None:
            types = credential.get("type")
            if isinstance(types, str):
                types = [types]
            if not any(t in self._accepted_types for t in types or []):
                return ()

        try:
            verify_credential(credential, public_key_b64=verification_key)
        except CredentialVerificationError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise CredentialVerificationError("Credential verification failed") from exc

        subject = credential.get("credentialSubject")
        if not isinstance(subject, Mapping):
            raise CredentialVerificationError("Credential subject missing or invalid")

        subject_id = subject.get("id")
        if not isinstance(subject_id, str):
            raise CredentialVerificationError("Credential subject is missing an id")

        issued_at = _parse_datetime(credential.get("issuanceDate")) or datetime.utcnow()
        expires_at = _parse_datetime(credential.get("expirationDate"))

        issuer_entity = self._ensure_entity(issuer_did, {"displayName": credential.get("issuer")})
        issuer_entity.update(subject if issuer_did == subject_id else {})

        subject_entity = self._ensure_entity(subject_id, subject)

        relationship = str(subject.get("relationship", "verifies"))
        confidence = _coerce_confidence(subject.get("confidence"), 1.0)
        evidence: Dict[str, Any] = {}
        for key in ("trustFramework", "jurisdiction", "registry", "roles"):
            if key in subject:
                evidence[key] = subject[key]

        issuer_link = TrustLink(
            source=issuer_did,
            target=subject_id,
            relationship=relationship,
            attestation_id=attestation_id,
            issued_at=issued_at,
            expires_at=expires_at,
            confidence=confidence,
            evidence=evidence,
        )
        self._register_link(issuer_link)

        pathway_links = [issuer_link]

        trusts = subject.get("trusts")
        if isinstance(trusts, Iterable):
            for entry in trusts:
                if not isinstance(entry, Mapping):
                    continue
                target = entry.get("target") or entry.get("id")
                if not isinstance(target, str):
                    continue
                self._ensure_entity(target, entry)
                trust_relationship = str(entry.get("relationship", "trusts"))
                trust_confidence = _coerce_confidence(entry.get("confidence"), confidence)
                trust_evidence = {
                    key: entry[key]
                    for key in (
                        "jurisdiction",
                        "entityType",
                        "displayName",
                        "interoperability",
                        "assuranceLevel",
                    )
                    if key in entry
                }
                link = TrustLink(
                    source=subject_id,
                    target=target,
                    relationship=trust_relationship,
                    attestation_id=attestation_id,
                    issued_at=issued_at,
                    expires_at=expires_at,
                    confidence=trust_confidence,
                    evidence=trust_evidence,
                )
                self._register_link(link)
                pathway_links.append(link)

        self._attestations[attestation_id] = dict(credential)
        return tuple(pathway_links)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def interoperability_map(self) -> Dict[str, List[TrustLink]]:
        """Return a mapping of issuers or entities to their outbound trust links."""

        result: Dict[str, List[TrustLink]] = {}
        for link in self._links:
            result.setdefault(link.source, []).append(link)
        return result

    def relationships_for(self, did: str) -> Sequence[TrustLink]:
        """Return all outbound links for ``did``."""

        return tuple(link for link in self._links if link.source == did)

    def entity(self, did: str) -> Optional[TrustEntity]:
        return self._entities.get(did)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _register_link(self, link: TrustLink) -> None:
        key = (link.source, link.target, link.relationship, link.attestation_id)
        if key in self._link_index:
            return
        self._links.append(link)
        self._link_index.add(key)

    def _ensure_entity(self, did: str, payload: Mapping[str, Any] | None) -> TrustEntity:
        entity = self._entities.get(did)
        if entity is None:
            entity = TrustEntity(did=did)
            self._entities[did] = entity
        if payload:
            entity.update(payload)
        return entity

    @staticmethod
    def _extract_attestation_id(credential: Mapping[str, Any]) -> str:
        identifier = credential.get("id")
        if isinstance(identifier, str):
            return identifier
        raise CredentialVerificationError("Credential missing identifier")

    @staticmethod
    def _extract_issuer_did(credential: Mapping[str, Any]) -> str:
        issuer = credential.get("issuer")
        if isinstance(issuer, str):
            return issuer
        if isinstance(issuer, Mapping):
            issuer_id = issuer.get("id")
            if isinstance(issuer_id, str):
                return issuer_id
        raise CredentialVerificationError("Credential missing issuer id")


__all__ = [
    "CrossJurisdictionTrustFabric",
    "TrustEntity",
    "TrustLink",
]

