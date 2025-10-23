"""Minimal MuSig2 coordination helpers built on BIP-0340 Schnorr primitives."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

_SECP256K1_P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
_SECP256K1_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
_SECP256K1_B = 7
_SECP256K1_GX = 55066263022277343669578718895168534326250603453777594175500187360389116729240
_SECP256K1_GY = 32670510020758816978083085130507043184471273380659243275938904335757337482424
_SECP256K1_G = (_SECP256K1_GX, _SECP256K1_GY)


class MuSig2Error(ValueError):
    """Raised when MuSig2 orchestration encounters invalid state."""


def _mod_inverse(value: int, modulus: int) -> int:
    return pow(value, -1, modulus)


def _point_add(
    point_a: Optional[Tuple[int, int]], point_b: Optional[Tuple[int, int]]
) -> Optional[Tuple[int, int]]:
    if point_a is None:
        return point_b
    if point_b is None:
        return point_a
    if point_a[0] == point_b[0] and (point_a[1] + point_b[1]) % _SECP256K1_P == 0:
        return None
    if point_a == point_b:
        slope = (3 * point_a[0] * point_a[0]) * _mod_inverse(
            2 * point_a[1], _SECP256K1_P
        )
    else:
        slope = (point_b[1] - point_a[1]) * _mod_inverse(
            point_b[0] - point_a[0], _SECP256K1_P
        )
    slope %= _SECP256K1_P
    x_r = (slope * slope - point_a[0] - point_b[0]) % _SECP256K1_P
    y_r = (slope * (point_a[0] - x_r) - point_a[1]) % _SECP256K1_P
    return x_r, y_r


def _point_neg(point: Tuple[int, int]) -> Tuple[int, int]:
    return point[0], (-point[1]) % _SECP256K1_P


def _scalar_multiply(k: int, point: Tuple[int, int]) -> Optional[Tuple[int, int]]:
    result: Optional[Tuple[int, int]] = None
    addend: Optional[Tuple[int, int]] = point
    scalar = k % _SECP256K1_N
    while scalar:
        if scalar & 1:
            result = _point_add(result, addend)
        addend = _point_add(addend, addend)
        scalar >>= 1
    return result


def _lift_x(x: int) -> Tuple[int, int]:
    if not 0 <= x < _SECP256K1_P:
        raise MuSig2Error("x coordinate out of field range")
    y_sq = (pow(x, 3, _SECP256K1_P) + _SECP256K1_B) % _SECP256K1_P
    y = pow(y_sq, (_SECP256K1_P + 1) // 4, _SECP256K1_P)
    if pow(y, 2, _SECP256K1_P) != y_sq:
        raise MuSig2Error("point not on curve")
    if y & 1:
        y = (-y) % _SECP256K1_P
    return x, y


def _tagged_hash(tag: str, data: bytes) -> bytes:
    tag_hash = hashlib.sha256(tag.encode()).digest()
    return hashlib.sha256(tag_hash + tag_hash + data).digest()


def _ensure_even(point: Tuple[int, int], scalar: int) -> Tuple[Tuple[int, int], int]:
    if point[1] & 1:
        point = (point[0], (-point[1]) % _SECP256K1_P)
        scalar = (-scalar) % _SECP256K1_N
    return point, scalar


def derive_xonly_public_key(secret_key: bytes) -> Tuple[int, bytes]:
    if len(secret_key) != 32:
        raise MuSig2Error("secret keys must be 32 bytes")
    secret_int = int.from_bytes(secret_key, "big")
    if not 1 <= secret_int < _SECP256K1_N:
        raise MuSig2Error("secret key outside curve order")
    point = _scalar_multiply(secret_int, _SECP256K1_G)
    if point is None:
        raise MuSig2Error("derived point at infinity")
    point, secret_int = _ensure_even(point, secret_int)
    return secret_int, point[0].to_bytes(32, "big")


def _compute_l(pubkeys: Sequence[bytes]) -> bytes:
    packed = b"".join(sorted(pubkeys))
    return _tagged_hash("MuSig/KeyAgg list", packed)


def _coefficient(l_value: bytes, pubkey: bytes) -> int:
    value = int.from_bytes(
        _tagged_hash("MuSig/KeyAgg coefficient", l_value + pubkey), "big"
    ) % _SECP256K1_N
    return value or 1


def _normalise_pubkeys(pubkeys: Iterable[bytes]) -> List[bytes]:
    normalised: List[bytes] = []
    for pubkey in pubkeys:
        if not isinstance(pubkey, (bytes, bytearray)):
            raise MuSig2Error("public keys must be bytes")
        if len(pubkey) != 32:
            raise MuSig2Error("public keys must be 32-byte x-only points")
        normalised.append(bytes(pubkey))
    if not normalised:
        raise MuSig2Error("at least one public key required")
    return normalised


def _aggregate_pubkeys(pubkeys: Sequence[bytes]) -> Tuple[bytes, Dict[str, int], int]:
    if len(pubkeys) == 1:
        point = _lift_x(int.from_bytes(pubkeys[0], "big"))
        return pubkeys[0], {pubkeys[0].hex(): 1}, 0
    l_value = _compute_l(pubkeys)
    coefficients: Dict[str, int] = {}
    accumulated: Optional[Tuple[int, int]] = None
    for pubkey in pubkeys:
        coeff = _coefficient(l_value, pubkey)
        point = _lift_x(int.from_bytes(pubkey, "big"))
        accumulated = _point_add(
            accumulated, _scalar_multiply(coeff, point)
        )
        coefficients[pubkey.hex()] = coeff
    if accumulated is None:
        raise MuSig2Error("aggregated public key is point at infinity")
    parity = accumulated[1] & 1
    if parity:
        accumulated = (accumulated[0], (-accumulated[1]) % _SECP256K1_P)
    return accumulated[0].to_bytes(32, "big"), coefficients, parity


def generate_nonce(
    secret_scalar: int,
    session_id: bytes,
    message: bytes,
    *,
    extra_input: bytes | None = None,
) -> Tuple[int, bytes]:
    if not isinstance(session_id, (bytes, bytearray)) or len(session_id) < 16:
        raise MuSig2Error("session_id must contain at least 16 bytes of entropy")
    seed_material = session_id + secret_scalar.to_bytes(32, "big") + message
    if extra_input:
        seed_material += extra_input
    nonce_int = int.from_bytes(_tagged_hash("MuSig/Nonce", seed_material), "big") % _SECP256K1_N
    if nonce_int == 0:
        raise MuSig2Error("derived nonce is zero")
    point = _scalar_multiply(nonce_int, _SECP256K1_G)
    if point is None:
        raise MuSig2Error("nonce point at infinity")
    point, nonce_int = _ensure_even(point, nonce_int)
    return nonce_int, point[0].to_bytes(32, "big")


def schnorr_sign(
    secret_key: bytes,
    message: bytes,
    *,
    aux_rand: bytes | None = None,
) -> bytes:
    secret_scalar, pubkey = derive_xonly_public_key(secret_key)
    rand = aux_rand if aux_rand is not None else b"\x00" * 32
    if len(rand) != 32:
        raise MuSig2Error("aux_rand must be 32 bytes")
    t = secret_scalar.to_bytes(32, "big")
    rand = bytes(a ^ b for a, b in zip(rand, _tagged_hash("BIP0340/aux", t)))
    k0 = int.from_bytes(
        _tagged_hash("BIP0340/nonce", rand + t + message), "big"
    ) % _SECP256K1_N
    if k0 == 0:
        raise MuSig2Error("nonce generation failed")
    r_point = _scalar_multiply(k0, _SECP256K1_G)
    if r_point is None:
        raise MuSig2Error("nonce point at infinity")
    r_point, k0 = _ensure_even(r_point, k0)
    r_bytes = r_point[0].to_bytes(32, "big")
    e = int.from_bytes(
        _tagged_hash("BIP0340/challenge", r_bytes + pubkey + message), "big"
    ) % _SECP256K1_N
    s = (k0 + e * secret_scalar) % _SECP256K1_N
    return r_bytes + s.to_bytes(32, "big")


def schnorr_verify(public_key: bytes, message: bytes, signature: bytes) -> bool:
    if len(public_key) != 32 or len(signature) != 64:
        return False
    try:
        point = _lift_x(int.from_bytes(public_key, "big"))
    except MuSig2Error:
        return False
    r = int.from_bytes(signature[:32], "big")
    s = int.from_bytes(signature[32:], "big")
    if r >= _SECP256K1_P or s >= _SECP256K1_N:
        return False
    e = int.from_bytes(
        _tagged_hash("BIP0340/challenge", signature[:32] + public_key + message), "big"
    ) % _SECP256K1_N
    s_g = _scalar_multiply(s, _SECP256K1_G)
    e_p = _scalar_multiply(e, point)
    if s_g is None or e_p is None:
        return False
    r_point = _point_add(s_g, _point_neg(e_p))
    if r_point is None or (r_point[1] & 1):
        return False
    return r_point[0] == r


@dataclass
class MuSig2Session:
    """In-memory record describing a MuSig2 signing session."""

    message: bytes
    public_keys: List[bytes]
    aggregated_public_key: bytes
    key_parity: int
    coefficients: Dict[str, int] = field(default_factory=dict)
    nonce_points: Dict[str, Tuple[int, int]] = field(default_factory=dict)
    partial_signatures: Dict[str, int] = field(default_factory=dict)
    aggregated_nonce: Optional[bytes] = None
    nonce_parity: int = 0

    @classmethod
    def create(cls, pubkeys: Sequence[bytes], message: bytes) -> "MuSig2Session":
        normalised = _normalise_pubkeys(pubkeys)
        aggregated, coefficients, parity = _aggregate_pubkeys(normalised)
        return cls(
            message=bytes(message),
            public_keys=list(normalised),
            aggregated_public_key=aggregated,
            key_parity=parity,
            coefficients=coefficients,
        )

    def participant_ids(self) -> List[str]:
        return [pub.hex() for pub in self.public_keys]

    def register_nonce(self, participant: str, nonce: bytes) -> None:
        if participant not in self.coefficients:
            raise MuSig2Error("unknown participant")
        if len(nonce) != 32:
            raise MuSig2Error("public nonce must be 32 bytes")
        point = _lift_x(int.from_bytes(nonce, "big"))
        self.nonce_points[participant] = point
        self._maybe_finalize_nonce()

    def _maybe_finalize_nonce(self) -> None:
        if len(self.nonce_points) != len(self.public_keys):
            return
        combined: Optional[Tuple[int, int]] = None
        for point in self.nonce_points.values():
            combined = _point_add(combined, point)
        if combined is None:
            raise MuSig2Error("aggregated nonce is point at infinity")
        self.nonce_parity = combined[1] & 1
        if self.nonce_parity:
            combined = (combined[0], (-combined[1]) % _SECP256K1_P)
        self.aggregated_nonce = combined[0].to_bytes(32, "big")

    def challenge(self) -> int:
        if self.aggregated_nonce is None:
            raise MuSig2Error("aggregate nonce not established")
        return (
            int.from_bytes(
                _tagged_hash(
                    "BIP0340/challenge",
                    self.aggregated_nonce + self.aggregated_public_key + self.message,
                ),
                "big",
            )
            % _SECP256K1_N
        )

    def add_partial_signature(self, participant: str, signature: bytes) -> None:
        if participant not in self.coefficients:
            raise MuSig2Error("unknown participant")
        if len(signature) != 32:
            raise MuSig2Error("partial signatures must be 32 bytes")
        self.partial_signatures[participant] = int.from_bytes(signature, "big") % _SECP256K1_N

    def final_signature(self) -> bytes:
        if self.aggregated_nonce is None:
            raise MuSig2Error("aggregate nonce not established")
        if len(self.partial_signatures) != len(self.public_keys):
            raise MuSig2Error("missing partial signatures")
        total = sum(self.partial_signatures.values()) % _SECP256K1_N
        return self.aggregated_nonce + total.to_bytes(32, "big")

    def to_dict(self) -> Dict[str, object]:
        return {
            "message": self.message.hex(),
            "public_keys": [pk.hex() for pk in self.public_keys],
            "aggregated_public_key": self.aggregated_public_key.hex(),
            "key_parity": self.key_parity,
            "coefficients": {k: format(v, "064x") for k, v in self.coefficients.items()},
            "nonces": {k: point[0].to_bytes(32, "big").hex() for k, point in self.nonce_points.items()},
            "aggregated_nonce": None
            if self.aggregated_nonce is None
            else self.aggregated_nonce.hex(),
            "nonce_parity": self.nonce_parity,
            "partial_signatures": {
                k: format(v, "064x") for k, v in self.partial_signatures.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "MuSig2Session":
        message = bytes.fromhex(str(data["message"]))
        pubkeys = [bytes.fromhex(entry) for entry in data.get("public_keys", [])]
        session = cls.create(pubkeys, message)
        session.key_parity = int(data.get("key_parity", 0))
        nonces: Mapping[str, str] = data.get("nonces", {})  # type: ignore[assignment]
        for participant, nonce_hex in nonces.items():
            session.nonce_points[participant] = _lift_x(int(nonce_hex, 16))
        aggregated_nonce = data.get("aggregated_nonce")
        if aggregated_nonce:
            session.aggregated_nonce = bytes.fromhex(str(aggregated_nonce))
        session.nonce_parity = int(data.get("nonce_parity", 0))
        partials: Mapping[str, str] = data.get("partial_signatures", {})  # type: ignore[assignment]
        for participant, sig_hex in partials.items():
            session.partial_signatures[participant] = int(sig_hex, 16) % _SECP256K1_N
        return session


def compute_partial_signature(
    session: MuSig2Session,
    participant: str,
    secret_scalar: int,
    secret_nonce: int,
) -> bytes:
    if participant not in session.coefficients:
        raise MuSig2Error("unknown participant")
    if session.aggregated_nonce is None:
        raise MuSig2Error("aggregate nonce not established")
    nonce_value = secret_nonce % _SECP256K1_N
    if session.nonce_parity:
        nonce_value = (-nonce_value) % _SECP256K1_N
    challenge = session.challenge()
    coeff = session.coefficients[participant]
    partial = (nonce_value + challenge * coeff * (secret_scalar % _SECP256K1_N)) % _SECP256K1_N
    return partial.to_bytes(32, "big")


__all__ = [
    "MuSig2Error",
    "MuSig2Session",
    "compute_partial_signature",
    "derive_xonly_public_key",
    "generate_nonce",
    "schnorr_sign",
    "schnorr_verify",
]
