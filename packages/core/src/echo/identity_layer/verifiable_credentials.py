"""Helpers for issuing and verifying W3C-compatible Verifiable Credentials."""

from __future__ import annotations

import base64
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence

from nacl.signing import VerifyKey

from .vault import EncryptedIdentityVault


class CredentialVerificationError(RuntimeError):
    """Raised when a verifiable credential fails validation."""


def _canonical_dumps(payload: Mapping[str, Any]) -> bytes:
    """Return a deterministic JSON representation for signing."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _utc_now() -> str:
    """Return the current UTC time encoded for VC timestamps."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class CredentialIssuer:
    """High level helper that issues Ed25519 signed verifiable credentials."""

    vault: EncryptedIdentityVault
    issuer_did: str
    verification_method: Optional[str] = None
    base_context: Sequence[str] = ("https://www.w3.org/2018/credentials/v1",)
    proof_type: str = "Ed25519Signature2020"

    def __post_init__(self) -> None:
        if self.vault.get_key_by_did(self.issuer_did) is None:
            raise KeyError(f"Unknown issuer DID: {self.issuer_did}")
        if self.verification_method is None:
            self.verification_method = f"{self.issuer_did}#key-1"

    def issue(
        self,
        *,
        subject_id: str,
        claims: Mapping[str, Any],
        types: Optional[Sequence[str]] = None,
        expires_at: Optional[datetime] = None,
        credential_id: Optional[str] = None,
        context: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        """Create and sign a verifiable credential."""

        if self.vault.get_key_by_did(self.issuer_did) is None:
            raise KeyError(f"Unknown issuer DID: {self.issuer_did}")

        credential_types = ["VerifiableCredential"]
        if types:
            for item in types:
                if item not in credential_types:
                    credential_types.append(str(item))

        context_values = list(self.base_context)
        if context:
            for entry in context:
                if entry not in context_values:
                    context_values.append(entry)

        issued_time = _utc_now()
        credential: Dict[str, Any] = {
            "@context": context_values,
            "id": credential_id or f"urn:uuid:{uuid.uuid4()}",
            "type": credential_types,
            "issuer": {"id": self.issuer_did},
            "issuanceDate": issued_time,
            "credentialSubject": {
                "id": subject_id,
                **{key: claims[key] for key in claims},
            },
        }
        if expires_at is not None:
            credential["expirationDate"] = (
                expires_at.astimezone(timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z")
            )

        payload = _canonical_dumps({k: v for k, v in credential.items() if k != "proof"})
        signature = self.vault.sign(self.issuer_did, payload)
        proof_value = base64.b64encode(signature).decode("ascii")
        credential["proof"] = {
            "type": self.proof_type,
            "created": issued_time,
            "proofPurpose": "assertionMethod",
            "verificationMethod": self.verification_method,
            "proofValue": proof_value,
        }
        return credential


def verify_credential(credential: Mapping[str, Any], *, public_key_b64: str) -> bool:
    """Verify the signature on a W3C-style credential."""

    proof = credential.get("proof")
    if not isinstance(proof, Mapping):
        raise CredentialVerificationError("Credential missing proof block")

    proof_value = proof.get("proofValue")
    if not isinstance(proof_value, str):
        raise CredentialVerificationError("Credential proofValue missing or invalid")

    signature = base64.b64decode(proof_value)
    payload = _canonical_dumps({k: v for k, v in credential.items() if k != "proof"})

    try:
        verify_key = VerifyKey(base64.b64decode(public_key_b64))
        verify_key.verify(payload, signature)
    except Exception as exc:  # noqa: BLE001
        raise CredentialVerificationError("Credential signature verification failed") from exc
    return True
