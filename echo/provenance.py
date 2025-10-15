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
    """
    Returns (algo, signature_b64). If ECHO_SIGN_KEY starts with 'hmac:' use HMAC-SHA256 on the bytes
    after the prefix; otherwise do a raw SHA256 digest 'sha256:' (no secret) as a cheap fallback.
    (Swap to ed25519 when libs are available in your env.)
    """

    payload = canonical_json(manifest)
    key = os.getenv(key_env, "")
    if key.startswith("hmac:"):
        secret = key.split("hmac:", 1)[1].encode("utf-8")
        sig = hmac.new(secret, payload, hashlib.sha256).digest()
        return "hmac-sha256", base64.b64encode(sig).decode()
    else:
        sig = hashlib.sha256(payload).digest()
        return "sha256", base64.b64encode(sig).decode()


def verify_signature(manifest: dict, signature_b64: str, algo: str, key_env: str = "ECHO_VERIFY_KEY") -> bool:
    payload = canonical_json(manifest)
    raw = base64.b64decode(signature_b64.encode())
    if algo == "sha256":
        return hashlib.sha256(payload).digest() == raw
    if algo == "hmac-sha256":
        secret = os.getenv(key_env, "").encode("utf-8")
        expect = hmac.new(secret, payload, hashlib.sha256).digest()
        return hmac.compare_digest(expect, raw)
    return False
