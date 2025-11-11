"""Verifiable credential issuing and verification."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from atlas.core.logging import get_logger


def _canonical(data: Dict[str, object]) -> bytes:
    return json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")


@dataclass
class CredentialIssuer:
    private_key: Ed25519PrivateKey
    did: str

    @classmethod
    def from_seed(cls, seed: bytes, did: str) -> "CredentialIssuer":
        private_key = Ed25519PrivateKey.from_private_bytes(seed)
        return cls(private_key=private_key, did=did)

    def issue(self, subject: str, claims: Dict[str, object]) -> Dict[str, object]:
        issuance_date = datetime.now(timezone.utc).isoformat()
        credential = {
            "@context": ["https://www.w3.org/2018/credentials/v1"],
            "type": ["VerifiableCredential"],
            "issuer": self.did,
            "issuanceDate": issuance_date,
            "credentialSubject": {
                "id": subject,
                "claims": claims,
            },
        }
        proof_payload = {
            "issuer": credential["issuer"],
            "issuanceDate": credential["issuanceDate"],
            "subject": subject,
            "claims": claims,
        }
        signature = self.private_key.sign(_canonical(proof_payload))
        credential["proof"] = {
            "type": "Ed25519Signature2020",
            "created": issuance_date,
            "verificationMethod": f"{self.did}#keys-1",
            "proofPurpose": "assertionMethod",
            "jws": signature.hex(),
        }
        return credential

    def export_public_key(self) -> bytes:
        return self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )


@dataclass
class CredentialVerifier:
    public_key: Ed25519PublicKey

    @classmethod
    def from_bytes(cls, data: bytes) -> "CredentialVerifier":
        return cls(public_key=Ed25519PublicKey.from_public_bytes(data))

    def verify(self, credential: Dict[str, object]) -> bool:
        proof = credential.get("proof")
        if not isinstance(proof, dict):
            return False
        payload = {
            "issuer": credential["issuer"],
            "issuanceDate": credential["issuanceDate"],
            "subject": credential["credentialSubject"]["id"],
            "claims": credential["credentialSubject"]["claims"],
        }
        try:
            signature = bytes.fromhex(proof["jws"])
            self.public_key.verify(signature, _canonical(payload))
            return True
        except Exception:  # pragma: no cover - verification failure path
            return False


__all__ = ["CredentialIssuer", "CredentialVerifier"]
