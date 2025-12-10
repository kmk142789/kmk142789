from datetime import datetime, timedelta, timezone

import pytest

from echo.identity_layer import CredentialIssuer, EncryptedIdentityVault, verify_credential


@pytest.fixture()
def issuer_vault(tmp_path):
    vault = EncryptedIdentityVault(tmp_path, "passphrase")
    record = vault.ensure_key(chain="bitcoin", account=0, index=0, change=0, origin="pytest")
    return vault, record


def test_issue_and_verify_verifiable_credential(issuer_vault):
    vault, issuer_record = issuer_vault
    issuer = CredentialIssuer(vault=vault, issuer_did=issuer_record["did"])

    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    credential = issuer.issue(
        subject_id="did:echo:subject",
        claims={"role": "guarantor", "trustScore": 0.98},
        types=["EchoCredential"],
        expires_at=expires_at,
        context=["https://w3id.org/security/suites/ed25519-2020/v1"],
    )

    assert credential["issuer"]["id"] == issuer_record["did"]
    assert "proof" in credential
    assert "credentialSubject" in credential
    assert credential["credentialSubject"]["role"] == "guarantor"
    assert "EchoCredential" in credential["type"]
    assert credential["@context"][0] == "https://www.w3.org/ns/credentials/v2"

    public_key_b64 = issuer_record["verification_public_key_b64"]
    assert verify_credential(credential, public_key_b64=public_key_b64) is True


def test_issue_rejects_unknown_issuer(tmp_path):
    vault = EncryptedIdentityVault(tmp_path, "passphrase")
    with pytest.raises(KeyError):
        CredentialIssuer(vault=vault, issuer_did="did:echo:missing")
