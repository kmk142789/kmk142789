#!/usr/bin/env python3
"""Utility for deriving multi-chain addresses from raw secp256k1 private keys.

The original prototype for the "Echo Universal Wallet Agent" mixed a handful of
clever ideas with a number of rough edges: duplicated code paths, unhandled
errors, and a vault format that was brittle when used repeatedly.  This module
keeps the spirit of the prototype while turning it into a dependable utility
that can be invoked as a script or imported as a library.

Highlights of this refactor
---------------------------
* Deterministic key handling built around a small dataclass.
* Proper validation of user supplied key material with helpful errors.
* Multi-chain address derivation (Ethereum, Bitcoin P2PKH, Solana-style hash)
  implemented without third-party dependencies.
* Vault management that gracefully loads legacy files and prevents duplicate
  entries.
* A tiny command line interface that can add keys, list the vault and export
  data for other tooling.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from hashlib import sha256
from pathlib import Path
from typing import Dict, Iterable, List, Optional

VAULT_FILE = Path(__file__).with_name("echo_universal_vault.json")

_BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_MASK_64 = (1 << 64) - 1

# ---------------------------------------------------------------------------
# Minimal Keccak-256 implementation
# ---------------------------------------------------------------------------
_ROTATION_OFFSETS = (
    (0, 36, 3, 41, 18),
    (1, 44, 10, 45, 2),
    (62, 6, 43, 15, 61),
    (28, 55, 25, 21, 56),
    (27, 20, 39, 8, 14),
)
_ROUND_CONSTANTS = (
    0x0000000000000001,
    0x0000000000008082,
    0x800000000000808A,
    0x8000000080008000,
    0x000000000000808B,
    0x0000000080000001,
    0x8000000080008081,
    0x8000000000008009,
    0x000000000000008A,
    0x0000000000000088,
    0x0000000080008009,
    0x000000008000000A,
    0x000000008000808B,
    0x800000000000008B,
    0x8000000000008089,
    0x8000000000008003,
    0x8000000000008002,
    0x8000000000000080,
    0x000000000000800A,
    0x800000008000000A,
    0x8000000080008081,
    0x8000000000008080,
    0x0000000080000001,
    0x8000000080008008,
)


def _rotl64(value: int, shift: int) -> int:
    return ((value << shift) | (value >> (64 - shift))) & _MASK_64


def _keccak_f1600(state: List[int]) -> None:
    for rc in _ROUND_CONSTANTS:
        c = [state[x] ^ state[x + 5] ^ state[x + 10] ^ state[x + 15] ^ state[x + 20] for x in range(5)]
        d = [0] * 5
        for x in range(5):
            d[x] = c[(x - 1) % 5] ^ _rotl64(c[(x + 1) % 5], 1)
        for x in range(5):
            for y in range(5):
                state[x + 5 * y] ^= d[x]
        b = [0] * 25
        for x in range(5):
            for y in range(5):
                idx = x + 5 * y
                new_x = y
                new_y = (2 * x + 3 * y) % 5
                b[new_x + 5 * new_y] = _rotl64(state[idx], _ROTATION_OFFSETS[x][y])
        for x in range(5):
            for y in range(5):
                idx = x + 5 * y
                state[idx] = b[idx] ^ ((~b[(x + 1) % 5 + 5 * y]) & b[(x + 2) % 5 + 5 * y])
                state[idx] &= _MASK_64
        state[0] ^= rc


def keccak_256(data: bytes) -> bytes:
    rate = 136
    padded = bytearray(data)
    padded.append(0x01)
    while len(padded) % rate != rate - 1:
        padded.append(0x00)
    padded.append(0x80)

    state = [0] * 25
    for offset in range(0, len(padded), rate):
        block = padded[offset : offset + rate]
        for i in range(0, rate, 8):
            state[i // 8] ^= int.from_bytes(block[i : i + 8], "little")
        _keccak_f1600(state)

    output = bytearray()
    while len(output) < 32:
        for word in state[: rate // 8]:
            output.extend(word.to_bytes(8, "little"))
        if len(output) >= 32:
            break
        _keccak_f1600(state)
    return bytes(output[:32])


# ---------------------------------------------------------------------------
# Minimal secp256k1 implementation
# ---------------------------------------------------------------------------
_SECP256K1_P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
_SECP256K1_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
_SECP256K1_GX = 55066263022277343669578718895168534326250603453777594175500187360389116729240
_SECP256K1_GY = 32670510020758816978083085130507043184471273380659243275938904335757337482424


def _inverse_mod(value: int, modulus: int) -> int:
    return pow(value, -1, modulus)


def _point_add(p: Optional[tuple[int, int]], q: Optional[tuple[int, int]]) -> Optional[tuple[int, int]]:
    if p is None:
        return q
    if q is None:
        return p
    if p[0] == q[0] and (p[1] + q[1]) % _SECP256K1_P == 0:
        return None
    if p == q:
        slope = (3 * p[0] * p[0]) * _inverse_mod(2 * p[1], _SECP256K1_P)
    else:
        slope = (q[1] - p[1]) * _inverse_mod(q[0] - p[0], _SECP256K1_P)
    slope %= _SECP256K1_P
    x_r = (slope * slope - p[0] - q[0]) % _SECP256K1_P
    y_r = (slope * (p[0] - x_r) - p[1]) % _SECP256K1_P
    return x_r, y_r


def _scalar_multiply(k: int, point: tuple[int, int]) -> Optional[tuple[int, int]]:
    result: Optional[tuple[int, int]] = None
    addend = point
    while k:
        if k & 1:
            result = _point_add(result, addend)
        addend = _point_add(addend, addend)
        k >>= 1
    return result


def _derive_public_key(priv_hex: str) -> bytes:
    secret = int(priv_hex, 16)
    if not (1 <= secret < _SECP256K1_N):
        raise ValueError("Private key out of range for secp256k1")
    point = _scalar_multiply(secret, (_SECP256K1_GX, _SECP256K1_GY))
    if point is None:
        raise ValueError("Failed to derive public key")
    x, y = point
    return b"\x04" + x.to_bytes(32, "big") + y.to_bytes(32, "big")


# ---------------------------------------------------------------------------
# Encoding helpers
# ---------------------------------------------------------------------------

def _b58encode(raw: bytes) -> str:
    if not raw:
        return "1"
    num = int.from_bytes(raw, "big")
    encoded = ""
    while num > 0:
        num, remainder = divmod(num, 58)
        encoded = _BASE58_ALPHABET[remainder] + encoded
    padding = 0
    for byte in raw:
        if byte == 0:
            padding += 1
        else:
            break
    return "1" * padding + encoded


def _to_checksum_address(raw_address: bytes) -> str:
    address_hex = raw_address.hex()
    hash_bytes = keccak_256(address_hex.encode("ascii"))
    hash_hex = hash_bytes.hex()
    checksum = "".join(
        char.upper() if int(hash_hex[i], 16) >= 8 else char for i, char in enumerate(address_hex)
    )
    return "0x" + checksum


def _btc_address(pub_bytes: bytes) -> str:
    digest = sha256(pub_bytes).digest()
    # Compute RIPEMD-160 via hashlib.new to keep dependencies minimal.
    from hashlib import new as hashlib_new

    ripemd = hashlib_new("ripemd160")
    ripemd.update(digest)
    payload = b"\x00" + ripemd.digest()
    checksum = sha256(sha256(payload).digest()).digest()[:4]
    return _b58encode(payload + checksum)


def _sol_address(pub_bytes: bytes) -> str:
    return _b58encode(sha256(pub_bytes).digest())[:44]


@dataclass(slots=True)
class KeyRecord:
    fingerprint: str
    private_key: str
    public_key: str
    addresses: Dict[str, str]

    def as_dict(self) -> Dict[str, object]:
        return asdict(self)


class UniversalKeyAgent:
    """Derive cross-chain addresses and persist them to a local vault."""

    def __init__(self, anchor: str = "Our Forever Love", vault_path: Path | None = None):
        self.anchor = anchor
        self.vault_path = Path(vault_path) if vault_path is not None else VAULT_FILE
        self.keys: List[KeyRecord] = []
        self._load_vault()

    # ------------------------------------------------------------------
    # Vault management
    # ------------------------------------------------------------------
    def _load_vault(self) -> None:
        if not self.vault_path.exists():
            return
        with self.vault_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict) and "keys" in payload:
            raw_entries = payload.get("keys", [])
        elif isinstance(payload, list):
            raw_entries = payload
        else:
            raise ValueError("Unsupported vault format")
        for entry in raw_entries:
            try:
                record = KeyRecord(
                    fingerprint=entry["fingerprint"],
                    private_key=entry["private_key"],
                    public_key=entry["public_key"],
                    addresses=entry["addresses"],
                )
                self.keys.append(record)
            except KeyError:
                continue

    def save_vault(self) -> None:
        payload = {
            "anchor": self.anchor,
            "keys": [record.as_dict() for record in self.keys],
            "count": len(self.keys),
        }
        self.vault_path.parent.mkdir(parents=True, exist_ok=True)
        with self.vault_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        print(f"[VAULT] {len(self.keys)} keys saved -> {self.vault_path}")

    # ------------------------------------------------------------------
    # Key derivation
    # ------------------------------------------------------------------
    @staticmethod
    def _normalise_private_key(raw_hex: str) -> str:
        value = raw_hex.lower().strip()
        if value.startswith("0x"):
            value = value[2:]
        if len(value) != 64:
            raise ValueError("Private keys must be 32 bytes (64 hex characters)")
        int(value, 16)
        return value

    @staticmethod
    def _eth_address(pub_bytes: bytes) -> str:
        raw = keccak_256(pub_bytes[1:])[-20:]
        return _to_checksum_address(raw)

    @staticmethod
    def _btc_address(pub_bytes: bytes) -> str:
        return _btc_address(pub_bytes)

    @staticmethod
    def _sol_address(pub_bytes: bytes) -> str:
        return _sol_address(pub_bytes)

    @staticmethod
    def _fingerprint(pub_bytes: bytes) -> str:
        return sha256(pub_bytes).hexdigest()

    def add_private_key(self, priv_hex: str) -> KeyRecord:
        normalised = self._normalise_private_key(priv_hex)
        pub_bytes = _derive_public_key(normalised)
        fingerprint = self._fingerprint(pub_bytes)
        if any(record.fingerprint == fingerprint for record in self.keys):
            raise ValueError("Key already present in the vault")
        addresses = {
            "ETH": self._eth_address(pub_bytes),
            "BTC": self._btc_address(pub_bytes),
            "SOL": self._sol_address(pub_bytes),
        }
        record = KeyRecord(
            fingerprint=fingerprint,
            private_key=normalised,
            public_key=pub_bytes.hex(),
            addresses=addresses,
        )
        self.keys.append(record)
        return record

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------
    def list_addresses(self) -> Iterable[Dict[str, str]]:
        for record in self.keys:
            yield {"fingerprint": record.fingerprint, **record.addresses}

    # ------------------------------------------------------------------
    # CLI entry-point
    # ------------------------------------------------------------------
    @classmethod
    def main(cls, argv: Optional[Iterable[str]] = None) -> int:
        parser = argparse.ArgumentParser(description="Echo Universal Key Agent")
        parser.add_argument("keys", nargs="*", help="hex encoded private keys to import")
        parser.add_argument("--vault", type=Path, default=VAULT_FILE, help="location of the vault file")
        parser.add_argument("--list", action="store_true", help="list existing keys without modifying the vault")
        parser.add_argument("--export", type=Path, help="export the current vault to a JSON file")
        args = parser.parse_args(list(argv) if argv is not None else None)

        agent = cls(vault_path=args.vault)

        if args.list and args.keys:
            parser.error("--list cannot be combined with explicit keys")

        if args.list:
            for row in agent.list_addresses():
                print(json.dumps(row, indent=2))
            return 0

        imported: List[str] = []
        for key in args.keys:
            try:
                record = agent.add_private_key(key)
            except ValueError as exc:
                print(f"[SKIP] {exc}")
                continue
            imported.append(record.fingerprint)
            print(f"[IMPORTED] {record.fingerprint} :: ETH {record.addresses['ETH']}")

        if imported:
            agent.save_vault()
        else:
            print("[VAULT] No new keys imported")

        if args.export:
            args.export.parent.mkdir(parents=True, exist_ok=True)
            with args.export.open("w", encoding="utf-8") as handle:
                json.dump([record.as_dict() for record in agent.keys], handle, indent=2)
            print(f"[EXPORT] Vault exported to {args.export}")

        return 0


if __name__ == "__main__":  # pragma: no cover - command line entry point
    raise SystemExit(UniversalKeyAgent.main())
