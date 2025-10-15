"""Manifest provenance utilities for canonical JSON and signatures."""

from __future__ import annotations

import base64
import binascii
import json
import os
from dataclasses import dataclass
from hashlib import sha256
from hmac import compare_digest, new as hmac_new
from typing import Mapping

from nacl import exceptions as nacl_exceptions
from nacl.signing import SigningKey, VerifyKey


def canonical_json(obj: Mapping[str, object] | object) -> bytes:
    """Return canonical JSON bytes for ``obj`` using sorted keys and stable separators."""

    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


@dataclass(frozen=True, slots=True)
class SignatureBundle:
    algorithm: str
    signature: bytes
    public_key: bytes | None = None


def _decode_key(material: str) -> bytes:
    material = material.strip()
    try:
        return base64.b64decode(material)
    except (ValueError, binascii.Error):
        pass
    try:
        return bytes.fromhex(material)
    except ValueError as exc:
        raise ValueError("Key material must be base64 or hex encoded") from exc


def sign_manifest(canonical_bytes: bytes, key_env: str = "ECHO_SIGN_KEY") -> SignatureBundle:
    secret = os.getenv(key_env)
    if not secret:
        raise RuntimeError(f"Signing key missing in environment variable {key_env}")
    key_bytes = _decode_key(secret)
    try:
        signing_key = SigningKey(key_bytes)
    except (ValueError, nacl_exceptions.CryptoError):
        signature = hmac_new(key_bytes, canonical_bytes, sha256).digest()
        return SignatureBundle(algorithm="hmac-sha256", signature=signature, public_key=key_bytes)
    signed = signing_key.sign(canonical_bytes)
    return SignatureBundle(
        algorithm="ed25519",
        signature=signed.signature,
        public_key=signing_key.verify_key.encode(),
    )


def verify_signature(
    manifest: Mapping[str, object],
    signature: bytes,
    pubkey: bytes,
    *,
    algorithm: str,
) -> bool:
    payload = canonical_json(manifest)
    if algorithm == "ed25519":
        try:
            VerifyKey(pubkey).verify(payload, signature)
        except nacl_exceptions.BadSignatureError:
            return False
        return True
    if algorithm == "hmac-sha256":
        expected = hmac_new(pubkey, payload, sha256).digest()
        return compare_digest(expected, signature)
    raise ValueError(f"Unsupported signature algorithm {algorithm}")
