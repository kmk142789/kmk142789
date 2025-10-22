"""Core vault implementation."""

from __future__ import annotations

import hashlib
import secrets
import threading
import time
import uuid
from typing import List, Optional, Tuple

from .crypto import decrypt, derive_key, encrypt, random_nonce, zeroize
from .models import VaultPolicy, VaultRecord
from .store import VaultStore

__all__ = ["Vault", "open_vault", "decode_private_key", "sign_payload"]

# ---------------------------------------------------------------------------
# Minimal secp256k1 implementation for signing
# ---------------------------------------------------------------------------

_SECP256K1_P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
_SECP256K1_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
_SECP256K1_GX = 55066263022277343669578718895168534326250603453777594175500187360389116729240
_SECP256K1_GY = 32670510020758816978083085130507043184471273380659243275938904335757337482424
_SECP256K1_G = (_SECP256K1_GX, _SECP256K1_GY)

_BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_BASE58_INDEX = {char: idx for idx, char in enumerate(_BASE58_ALPHABET)}


def _inverse_mod(value: int, modulus: int) -> int:
    return pow(value, -1, modulus)


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
        slope = (3 * point_a[0] * point_a[0]) * _inverse_mod(2 * point_a[1], _SECP256K1_P)
    else:
        slope = (point_b[1] - point_a[1]) * _inverse_mod(point_b[0] - point_a[0], _SECP256K1_P)
    slope %= _SECP256K1_P
    x_r = (slope * slope - point_a[0] - point_b[0]) % _SECP256K1_P
    y_r = (slope * (point_a[0] - x_r) - point_a[1]) % _SECP256K1_P
    return x_r, y_r


def _scalar_multiply(k: int, point: tuple[int, int]) -> Optional[tuple[int, int]]:
    result: Optional[tuple[int, int]] = None
    addend: Optional[tuple[int, int]] = point
    while k:
        if k & 1:
            result = _point_add(result, addend)
        addend = _point_add(addend, addend)
        k >>= 1
    return result


def _ecdsa_sign(priv_key: bytes, payload: bytes, *, rand_nonce: bool = True) -> bytes:
    secret_int = int.from_bytes(priv_key, "big")
    if not (1 <= secret_int < _SECP256K1_N):
        raise ValueError("invalid secp256k1 private key")

    payload_hash = hashlib.sha256(payload).digest()
    payload_int = int.from_bytes(payload_hash, "big")

    if rand_nonce:
        while True:
            k = secrets.randbelow(_SECP256K1_N)
            if k != 0:
                break
    else:
        k_material = hashlib.sha256(priv_key + payload_hash).digest()
        k = int.from_bytes(k_material, "big") % _SECP256K1_N
        if k == 0:
            k = 1

    point = _scalar_multiply(k, _SECP256K1_G)
    if point is None:
        raise ValueError("failed to derive curve point for signature")
    r = point[0] % _SECP256K1_N
    if r == 0:
        raise ValueError("invalid signature parameter r")

    s = (_inverse_mod(k, _SECP256K1_N) * (payload_int + r * secret_int)) % _SECP256K1_N
    if s == 0:
        raise ValueError("invalid signature parameter s")
    if s > _SECP256K1_N // 2:
        s = _SECP256K1_N - s

    return r.to_bytes(32, "big") + s.to_bytes(32, "big")


# ---------------------------------------------------------------------------
# WIF helpers
# ---------------------------------------------------------------------------


def _b58decode(data: str) -> bytes:
    if not data:
        raise ValueError("empty base58 string")
    num = 0
    for char in data:
        try:
            num = num * 58 + _BASE58_INDEX[char]
        except KeyError as exc:  # pragma: no cover - defensive branch
            raise ValueError(f"invalid base58 character: {char}") from exc
    byte_length = (num.bit_length() + 7) // 8
    decoded = num.to_bytes(byte_length, "big") if byte_length else b""
    leading_zeroes = len(data) - len(data.lstrip("1"))
    return b"\x00" * leading_zeroes + decoded


def _decode_wif(wif: str) -> bytes:
    raw = _b58decode(wif.strip())
    if len(raw) < 5:
        raise ValueError("wif payload too small")
    payload, checksum = raw[:-4], raw[-4:]
    calc = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    if checksum != calc:
        raise ValueError("wif checksum mismatch")
    if payload[0] not in {0x80, 0xEF}:
        raise ValueError("unsupported WIF prefix")
    key_bytes = payload[1:]
    if len(key_bytes) == 33 and key_bytes[-1] == 0x01:
        key_bytes = key_bytes[:-1]
    if len(key_bytes) != 32:
        raise ValueError("wif must encode 32 byte keys")
    return key_bytes


def decode_private_key(fmt: str, key: str) -> bytes:
    fmt_lower = fmt.lower()
    if fmt_lower == "hex":
        cleaned = key.strip().lower()
        if cleaned.startswith("0x"):
            cleaned = cleaned[2:]
        if len(cleaned) != 64:
            raise ValueError("hex keys must be 64 characters (32 bytes)")
        try:
            return bytes.fromhex(cleaned)
        except ValueError as exc:
            raise ValueError("invalid hex key") from exc
    if fmt_lower == "wif":
        return _decode_wif(key)
    raise ValueError("unsupported key format")


def sign_payload(priv_key: bytes, payload: bytes, *, rand_nonce: bool = True) -> bytes:
    """Sign ``payload`` using the provided private key bytes."""

    return _ecdsa_sign(priv_key, payload, rand_nonce=rand_nonce)


# ---------------------------------------------------------------------------
# Vault core
# ---------------------------------------------------------------------------


class Vault:
    """Encrypted key vault with policy enforcement."""

    def __init__(self, store: VaultStore, master_key: bytes) -> None:
        self._store = store
        self._master_key = bytearray(master_key)
        self._lock = threading.RLock()

    @classmethod
    def open(cls, path: str, passphrase: str) -> "Vault":
        store = VaultStore(path)
        key = derive_key(passphrase, store.salt())
        return cls(store, key)

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------
    def close(self) -> None:
        with self._lock:
            zeroize(self._master_key)
            self._store.close()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def import_key(
        self,
        *,
        label: str,
        key: str,
        fmt: str,
        tags: Optional[List[str]] = None,
        policy: Optional[VaultPolicy] = None,
    ) -> VaultRecord:
        fmt = fmt.lower()
        if fmt not in {"hex", "wif"}:
            raise ValueError("fmt must be 'hex' or 'wif'")
        policy_obj = policy or VaultPolicy()
        if fmt not in policy_obj.allow_formats:
            raise ValueError("policy does not allow provided key format")

        key_buffer = self._normalise_key(fmt, key)
        try:
            ciphertext, nonce = encrypt(bytes(self._master_key), bytes(key_buffer), nonce=random_nonce())
        finally:
            zeroize(key_buffer)

        created_at = time.time()
        expires_at: Optional[float] = None
        if policy_obj.max_age_s > 0:
            expires_at = created_at + policy_obj.max_age_s
        record = VaultRecord(
            id=str(uuid.uuid4()),
            label=label,
            fmt=fmt,  # type: ignore[arg-type]
            tags=self._normalise_tags(tags),
            created_at=created_at,
            last_used_at=None,
            use_count=0,
            entropy_hint=secrets.token_hex(4),
            policy=policy_obj,
            status="active",
            expires_at=expires_at,
            last_rotated_at=created_at,
            rotation_count=0,
        )
        self._store.insert_record(record, enc_priv=ciphertext, nonce=nonce)
        return record

    def find(self, *, q: Optional[str] = None, tags: Optional[List[str]] = None) -> List[VaultRecord]:
        records = self._store.list_records()
        if q:
            lowered = q.lower()
            records = [
                record
                for record in records
                if (
                    lowered in record.label.lower()
                    or lowered in record.id.lower()
                    or any(lowered in tag.lower() for tag in record.tags)
                )
            ]
        if tags:
            wanted = {tag.lower() for tag in tags}
            records = [
                record
                for record in records
                if wanted.issubset({tag.lower() for tag in record.tags})
            ]
        return sorted(records, key=lambda rec: rec.created_at)

    def get(self, record_id: str) -> VaultRecord:
        record, _, _ = self._store.fetch_record(record_id)
        return record

    def sign(
        self,
        record_id: str,
        payload: bytes,
        *,
        rand_nonce: bool = True,
    ) -> dict:
        with self._lock:
            record, ciphertext, nonce = self._store.fetch_record(record_id)
            record, ciphertext, nonce = self._ensure_lifecycle(
                record_id, record, ciphertext, nonce
            )
            self._enforce_policy(record)
            secret_bytes = decrypt(bytes(self._master_key), ciphertext, nonce)
            secret_buffer = bytearray(secret_bytes)
            try:
                signature = _ecdsa_sign(secret_buffer, payload, rand_nonce=rand_nonce)
            finally:
                zeroize(secret_buffer)
            ts = time.time()
            entropy_hint: Optional[str] = None
            if record.use_count == 0:
                entropy_hint = hashlib.sha256(signature).hexdigest()[:12]
            updated_record = self._store.update_usage(
                record_id,
                use_count=record.use_count + 1,
                last_used_at=ts,
                entropy_hint=entropy_hint,
            )
            return {
                "sig": signature.hex(),
                "algo": "secp256k1+sha256",
                "record": updated_record,
                "ts": ts,
            }

    def set_policy(self, record_id: str, policy: VaultPolicy) -> VaultRecord:
        return self._store.update_policy(record_id, policy)

    def export_metadata(self) -> List[VaultRecord]:
        return self._store.list_records()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _normalise_tags(self, tags: Optional[List[str]]) -> List[str]:
        if not tags:
            return []
        cleaned = {tag.strip() for tag in tags if tag and tag.strip()}
        return sorted(cleaned)

    def _normalise_key(self, fmt: str, key: str) -> bytearray:
        return bytearray(decode_private_key(fmt, key))

    def _enforce_policy(self, record: VaultRecord) -> None:
        policy = record.policy
        if record.fmt not in policy.allow_formats:
            raise PermissionError("policy disallows signing with this format")
        if policy.max_sign_uses > 0 and record.use_count >= policy.max_sign_uses:
            raise PermissionError("maximum signing uses exceeded")
        if (
            policy.cooldown_s > 0
            and record.last_used_at is not None
            and (time.time() - record.last_used_at) < policy.cooldown_s
        ):
            raise PermissionError("cooldown active for record")

    def _ensure_lifecycle(
        self,
        record_id: str,
        record: VaultRecord,
        ciphertext: bytes,
        nonce: bytes,
    ) -> Tuple[VaultRecord, bytes, bytes]:
        now = time.time()
        if record.status != "active":
            raise PermissionError(f"record is {record.status}")
        policy = record.policy
        reference_ts = record.last_rotated_at or record.created_at
        expires_at = record.expires_at
        expired = expires_at is not None and now >= expires_at
        interval_due = (
            policy.rotation_interval_s > 0
            and now - reference_ts >= policy.rotation_interval_s
        )
        if not expired and not interval_due:
            return record, ciphertext, nonce

        if not policy.auto_rotate:
            self._store.mark_status(
                record_id, status="expired", expires_at=expires_at or now
            )
            raise PermissionError("record requires manual rotation")

        rotated_record, new_ciphertext, new_nonce = self._rotate_record(
            record_id,
            record,
            ciphertext,
            nonce,
            rotation_ts=now,
        )
        return rotated_record, new_ciphertext, new_nonce

    def _rotate_record(
        self,
        record_id: str,
        record: VaultRecord,
        ciphertext: bytes,
        nonce: bytes,
        *,
        rotation_ts: float,
    ) -> Tuple[VaultRecord, bytes, bytes]:
        secret_bytes = decrypt(bytes(self._master_key), ciphertext, nonce)
        secret_buffer = bytearray(secret_bytes)
        try:
            new_ciphertext, new_nonce = encrypt(
                bytes(self._master_key), bytes(secret_buffer), nonce=random_nonce()
            )
        finally:
            zeroize(secret_buffer)
        new_entropy = secrets.token_hex(4)
        expires_at: Optional[float] = None
        if record.policy.max_age_s > 0:
            expires_at = rotation_ts + record.policy.max_age_s
        updated_record = self._store.rotate_record(
            record_id,
            enc_priv=new_ciphertext,
            nonce=new_nonce,
            rotation_ts=rotation_ts,
            expires_at=expires_at,
            entropy_hint=new_entropy,
            rotation_count=record.rotation_count + 1,
        )
        return updated_record, new_ciphertext, new_nonce

    def rotate(self, record_id: str) -> VaultRecord:
        """Force a rotation cycle for the given record."""

        with self._lock:
            record, ciphertext, nonce = self._store.fetch_record(record_id)
            rotated_record, _, _ = self._rotate_record(
                record_id, record, ciphertext, nonce, rotation_ts=time.time()
            )
            return rotated_record


def open_vault(path: str, passphrase: str) -> Vault:
    """Convenience wrapper around :meth:`Vault.open`."""

    return Vault.open(path, passphrase)
