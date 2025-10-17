"""Signature helpers for Pulse Weaver and Temporal Ledger services.

The helpers in this module intentionally keep a very small surface area so
components can sign or verify JSON payloads without knowing about the
underlying key representation.  Keys are expected to be stored as JSON files
alongside the existing attestation materials used by other Echo tooling.  The
format is intentionally simple::

    {
        "key_id": "watchdog-local",
        "private_key": "<hex-encoded secp256k1 key>",
        "public_key": "<hex-encoded uncompressed public key>"
    }

The functions accept optional overrides for the key material which allows the
unit tests to operate with ephemeral keys.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import Any, Mapping, MutableMapping, Optional

from echo.vault.vault import sign_payload

DEFAULT_KEY_PATH = Path(os.getenv("ECHO_ATTESTATION_KEY", "proofs/watchdog_attest_key.json"))

_SECP256K1_P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
_SECP256K1_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
_SECP256K1_GX = 55066263022277343669578718895168534326250603453777594175500187360389116729240
_SECP256K1_GY = 32670510020758816978083085130507043184471273380659243275938904335757337482424
_SECP256K1_G = (_SECP256K1_GX, _SECP256K1_GY)


@dataclass(frozen=True)
class SignedPayload:
    """Return type from :func:`sign` providing a consistent envelope."""

    payload: Mapping[str, Any]
    signature: str
    key_id: str


def _load_key_material(path: Path | str | None = None) -> MutableMapping[str, Any]:
    target = Path(path) if path else DEFAULT_KEY_PATH
    if not target.exists():
        raise FileNotFoundError(
            f"Attestation key file not found at {target}. Configure ECHO_ATTESTATION_KEY"
        )
    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, MutableMapping):  # pragma: no cover - defensive
        raise TypeError("Key file must contain an object")
    for field in ("private_key", "public_key", "key_id"):
        if field not in data:
            raise KeyError(f"Key file missing '{field}' field")
    return data


def _scalar_multiply(k: int, point: tuple[int, int]) -> Optional[tuple[int, int]]:
    result: Optional[tuple[int, int]] = None
    addend: Optional[tuple[int, int]] = point
    while k:
        if k & 1:
            result = _point_add(result, addend)
        addend = _point_add(addend, addend)
        k >>= 1
    return result


def _point_add(
    point_a: Optional[tuple[int, int]], point_b: Optional[tuple[int, int]]
) -> Optional[tuple[int, int]]:
    if point_a is None:
        return point_b
    if point_b is None:
        return point_a
    if point_a[0] == point_b[0] and (point_a[1] + point_b[1]) % _SECP256K1_P == 0:
        return None
    if point_a == point_b:
        slope = (3 * point_a[0] * point_a[0]) * pow(2 * point_a[1], -1, _SECP256K1_P)
    else:
        slope = (point_b[1] - point_a[1]) * pow(point_b[0] - point_a[0], -1, _SECP256K1_P)
    slope %= _SECP256K1_P
    x_r = (slope * slope - point_a[0] - point_b[0]) % _SECP256K1_P
    y_r = (slope * (point_a[0] - x_r) - point_a[1]) % _SECP256K1_P
    return x_r, y_r


def _decode_public_key(hex_value: str) -> tuple[int, int]:
    raw = bytes.fromhex(hex_value)
    if len(raw) != 65 or raw[0] != 0x04:
        raise ValueError("Public keys must be 65 byte uncompressed points")
    x = int.from_bytes(raw[1:33], "big")
    y = int.from_bytes(raw[33:], "big")
    return x, y


def _normalise(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {k: _normalise(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalise(item) for item in value]
    return value


def _canonical_payload(payload: Mapping[str, Any]) -> bytes:
    canonical_payload = _normalise(payload)
    return json.dumps(canonical_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign(
    payload: Mapping[str, Any],
    *,
    key_path: Path | str | None = None,
    private_key_hex: str | None = None,
    key_id: str | None = None,
) -> SignedPayload:
    """Create a deterministic secp256k1 signature for ``payload``."""

    if private_key_hex is None or key_id is None:
        key_material = _load_key_material(key_path)
        private_key_hex = private_key_hex or str(key_material["private_key"])
        key_id = key_id or str(key_material["key_id"])
    canonical = _canonical_payload(payload)
    signature = sign_payload(bytes.fromhex(private_key_hex), canonical, rand_nonce=False)
    return SignedPayload(payload=dict(payload), signature=signature.hex(), key_id=key_id)


def verify(
    payload: Mapping[str, Any],
    signature_hex: str,
    *,
    public_key_hex: str | None = None,
    key_path: Path | str | None = None,
) -> bool:
    """Verify a signature against ``payload``.

    If ``public_key_hex`` is omitted the helper attempts to read it from the
    attestation key file.
    """

    if public_key_hex is None:
        key_material = _load_key_material(key_path)
        public_key_hex = str(key_material["public_key"])
    try:
        public_point = _decode_public_key(public_key_hex)
    except ValueError:
        return False

    signature = bytes.fromhex(signature_hex)
    if len(signature) != 64:
        return False
    r = int.from_bytes(signature[:32], "big")
    s = int.from_bytes(signature[32:], "big")
    if not (1 <= r < _SECP256K1_N and 1 <= s < _SECP256K1_N):
        return False

    canonical = _canonical_payload(payload)
    digest_int = int.from_bytes(hashlib.sha256(canonical).digest(), "big")
    w = pow(s, -1, _SECP256K1_N)
    u1 = (digest_int * w) % _SECP256K1_N
    u2 = (r * w) % _SECP256K1_N
    g_component = _scalar_multiply(u1, _SECP256K1_G)
    pub_component = _scalar_multiply(u2, public_point)
    point = _point_add(g_component, pub_component)
    if point is None:
        return False
    return (point[0] % _SECP256K1_N) == r


__all__ = ["SignedPayload", "sign", "verify"]
