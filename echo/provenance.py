from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from typing import Tuple


def canonical_json(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_manifest(manifest: dict, key_env: str = "ECHO_SIGN_KEY") -> Tuple[str, str]:
    """Return a tuple of (algorithm, signature)."""

    payload = canonical_json(manifest)
    key = os.getenv(key_env, "")
    if key.startswith("hmac:"):
        secret = key.split("hmac:", 1)[1].encode("utf-8")
        signature = hmac.new(secret, payload, hashlib.sha256).digest()
        return "hmac-sha256", base64.b64encode(signature).decode()
    signature = hashlib.sha256(payload).digest()
    return "sha256", base64.b64encode(signature).decode()


def verify_signature(
    manifest: dict, signature_b64: str, algo: str, key_env: str = "ECHO_VERIFY_KEY"
) -> bool:
    payload = canonical_json(manifest)
    raw = base64.b64decode(signature_b64.encode())
    if algo == "sha256":
        return hashlib.sha256(payload).digest() == raw
    if algo == "hmac-sha256":
        secret = os.getenv(key_env, "").encode("utf-8")
        expected = hmac.new(secret, payload, hashlib.sha256).digest()
        return hmac.compare_digest(expected, raw)
    return False
