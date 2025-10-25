"""Structured access to the solved Bitcoin puzzle dataset."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional

_DATA_PATH = Path(__file__).with_name("puzzle_solutions.json")
_BASE58_ALPHABET = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


@dataclass(frozen=True)
class PuzzleSolution:
    """Record describing a solved Bitcoin puzzle wallet."""

    bits: int
    range_min: str
    range_max: str
    address: str
    btc_value: float
    hash160_compressed: str
    public_key: str
    private_key: str
    solve_date: str

    def _normalised_hash160(self) -> str:
        """Return the validated lowercase HASH160 fingerprint for the entry."""

        payload = self.hash160_compressed.lower()
        if not re.fullmatch(r"[0-9a-f]{40}", payload):
            raise ValueError("puzzle record does not contain a valid HASH160")
        return payload

    def p2pkh_script(self, *, separator: str = " ") -> str:
        """Return the canonical P2PKH locking script for this puzzle wallet.

        Parameters
        ----------
        separator:
            Token separator used when joining the assembly representation.  The
            default yields a single-line script while callers may request a
            newline-delimited variant by passing ``"\n"``.

        Raises
        ------
        ValueError
            If the stored HASH160 payload is not the expected 20-byte hex
            string.  This protects against accidentally emitting malformed
            scripts for incomplete dataset entries.
        """

        payload = self._normalised_hash160()
        parts = [
            "OP_DUP",
            "OP_HASH160",
            payload,
            "OP_EQUALVERIFY",
            "OP_CHECKSIG",
        ]
        return separator.join(parts)

    def p2pkh_script_hex(self) -> str:
        """Return the canonical hexadecimal encoding of the locking script."""

        payload = self._normalised_hash160()
        return f"76a914{payload}88ac"


@lru_cache(maxsize=1)
def _load_raw_dataset() -> tuple[PuzzleSolution, ...]:
    payload = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    return tuple(
        PuzzleSolution(
            bits=int(entry["bits"]),
            range_min=entry["range_min"],
            range_max=entry["range_max"],
            address=entry["address"],
            btc_value=float(entry["btc_value"]),
            hash160_compressed=entry["hash160_compressed"],
            public_key=entry["public_key"],
            private_key=entry["private_key"],
            solve_date=entry["solve_date"],
        )
        for entry in payload
    )


@lru_cache(maxsize=1)
def load_puzzle_solutions() -> tuple[PuzzleSolution, ...]:
    """Return all solved puzzle entries sorted by bit-length."""

    valid: list[PuzzleSolution] = []
    for entry in _load_raw_dataset():
        if entry.bits > 130:
            break

        derived_address = _derive_p2pkh_address(entry.public_key)
        derived_hash160 = _hash160(entry.public_key)

        if derived_address != entry.address:
            continue
        if derived_hash160 != entry.hash160_compressed:
            continue

        valid.append(entry)

    return tuple(valid)


def iter_puzzle_solutions() -> Iterable[PuzzleSolution]:
    """Yield solved puzzle entries in ascending order by difficulty."""

    yield from load_puzzle_solutions()


def get_solution_by_bits(bits: int) -> PuzzleSolution:
    """Return the puzzle solution for the requested bit-length."""

    for entry in load_puzzle_solutions():
        if entry.bits == bits:
            return entry
    raise KeyError(f"No puzzle solution recorded for {bits} bits")


def get_puzzle_metadata(bits: int) -> PuzzleSolution:
    """Return the raw dataset entry for ``bits`` regardless of solve status."""

    for entry in _load_raw_dataset():
        if entry.bits == bits:
            return entry
    raise KeyError(f"No puzzle metadata recorded for {bits} bits")


def find_solution_by_address(address: str) -> Optional[PuzzleSolution]:
    """Return the solution entry corresponding to *address*, if known."""

    address_normalised = address.strip()
    for entry in load_puzzle_solutions():
        if entry.address == address_normalised:
            return entry
    return None


def generate_private_key_sequence(start: int, stop: int, *, width: int = 64) -> list[str]:
    """Return zero-padded hexadecimal private keys for the inclusive range."""

    if width <= 0:
        raise ValueError("width must be positive")
    if start > stop:
        raise ValueError("start must be less than or equal to stop")

    return [format(value, f"0{width}x") for value in range(start, stop + 1)]


def _hash160(public_key_hex: str) -> str:
    """Return the HASH160 digest for the provided compressed public key."""

    pub_bytes = bytes.fromhex(public_key_hex)
    sha = hashlib.sha256(pub_bytes).digest()
    ripe = hashlib.new("ripemd160", sha).digest()
    return ripe.hex()


def _derive_p2pkh_address(public_key_hex: str) -> str:
    """Derive a Base58Check-encoded P2PKH address from *public_key_hex*."""

    ripe = bytes.fromhex(_hash160(public_key_hex))
    payload = b"\x00" + ripe
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    return _base58_encode(payload + checksum)


def _base58_encode(data: bytes) -> str:
    """Encode *data* using the Bitcoin Base58 alphabet."""

    number = int.from_bytes(data, byteorder="big")
    encoded = bytearray()
    while number > 0:
        number, remainder = divmod(number, 58)
        encoded.append(_BASE58_ALPHABET[remainder])
    encoded.reverse()

    pad_length = len(data) - len(data.lstrip(b"\x00"))
    return (_BASE58_ALPHABET[:1] * pad_length + encoded).decode("ascii")
