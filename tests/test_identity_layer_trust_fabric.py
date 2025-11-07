from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from echo.identity_layer import (
    CredentialIssuer,
    CredentialVerificationError,
    CrossJurisdictionTrustFabric,
    EncryptedIdentityVault,
)


@pytest.fixture()
def issuer(tmp_path: Path):
    vault = EncryptedIdentityVault(tmp_path / "vault", "passphrase")
    key_entry = vault.ensure_key(chain="bitcoin", account=0, index=0, origin="test")
    issuer_did = key_entry["did"]
    verification_key = vault.get_key_by_did(issuer_did)["verification_public_key_b64"]
    issuer = CredentialIssuer(vault=vault, issuer_did=issuer_did)
    return issuer, verification_key


def _build_attestation(issuer: CredentialIssuer, *, subject_id: str):
    return issuer.issue(
        subject_id=subject_id,
        claims={
            "displayName": "Echo Stewardship Guild",
            "jurisdiction": "US-CA",
            "entityType": "steward",
            "relationship": "recognizes",
            "confidence": 0.92,
            "trustFramework": "Echo-Bridge-v1",
            "trusts": [
                {
                    "target": "did:echo:regulator:world",
                    "relationship": "licensed-by",
                    "confidence": 0.87,
                    "jurisdiction": "GLB",
                    "entityType": "regulator",
                    "displayName": "World Trust Registry",
                },
                {
                    "target": "did:echo:steward:alice",
                    "relationship": "stewarded-by",
                    "confidence": 0.8,
                    "assuranceLevel": "community",
                },
            ],
        },
        types=["CrossJurisdictionTrustAttestation"],
        credential_id="urn:uuid:test-attestation",
    )


def test_trust_fabric_maps_relationships(issuer):
    issuer_obj, verification_key = issuer
    attestation = _build_attestation(issuer_obj, subject_id="did:echo:institution:echo-hospital")

    fabric = CrossJurisdictionTrustFabric(public_key_resolver=lambda did: verification_key)
    links = fabric.ingest(attestation)

    assert len(links) == 3
    issuer_link = links[0]
    assert issuer_link.source == issuer_obj.issuer_did
    assert issuer_link.target == "did:echo:institution:echo-hospital"
    assert issuer_link.relationship == "recognizes"
    assert issuer_link.confidence == pytest.approx(0.92)

    map_links = fabric.interoperability_map()
    assert set(map_links) == {
        issuer_obj.issuer_did,
        "did:echo:institution:echo-hospital",
    }
    subject_links = map_links["did:echo:institution:echo-hospital"]
    targets = {link.target for link in subject_links}
    assert targets == {"did:echo:regulator:world", "did:echo:steward:alice"}

    entity = fabric.entity("did:echo:institution:echo-hospital")
    assert entity is not None
    assert entity.display_name == "Echo Stewardship Guild"
    assert entity.jurisdiction == "US-CA"
    assert entity.entity_type == "steward"


def test_duplicate_attestations_are_ignored(issuer):
    issuer_obj, verification_key = issuer
    attestation = _build_attestation(issuer_obj, subject_id="did:echo:institution:echo-hospital")

    fabric = CrossJurisdictionTrustFabric(public_key_resolver=lambda did: verification_key)
    first = fabric.ingest(attestation)
    second = fabric.ingest(attestation)

    assert len(first) == len(second) == 3
    assert len(fabric.links) == 3


def test_invalid_signature_raises(issuer):
    issuer_obj, verification_key = issuer
    attestation = _build_attestation(issuer_obj, subject_id="did:echo:institution:echo-hospital")

    # Corrupt the proof value to invalidate the signature
    attestation["proof"]["proofValue"] = "invalid"

    fabric = CrossJurisdictionTrustFabric(public_key_resolver=lambda did: verification_key)

    with pytest.raises(CredentialVerificationError):
        fabric.ingest(attestation)


def test_expiration_is_preserved(issuer):
    issuer_obj, verification_key = issuer
    future = datetime.now(timezone.utc).replace(microsecond=0)
    attestation = issuer_obj.issue(
        subject_id="did:echo:institution:echo-hospital",
        claims={"relationship": "verifies"},
        credential_id="urn:uuid:expiring",
        expires_at=future,
    )

    fabric = CrossJurisdictionTrustFabric(public_key_resolver=lambda did: verification_key)
    [link] = fabric.ingest(attestation)

    assert link.expires_at is not None
    assert link.expires_at.tzinfo == future.tzinfo
