"""Utilities to regenerate synthetic puzzle data for tests.

This module provides a compact script that deterministically rebuilds a
representative subset of the puzzle artifacts used in automated tests.  The
real project produces substantially richer data, but the fixtures in CI only
need structured JSON with stable checksums.  Keeping the regeneration logic
small ensures it can be audited quickly while still matching the expected
filesystem layout (``data/puzzles`` and ``build/proofs``).
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Dict, List, Tuple

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def base58(value: int) -> str:
    """Return the Base58 encoding for ``value``.

    The implementation is intentionally tiny and only supports non-negative
    integers because the regeneration script never needs other inputs.
    """

    if value < 0:
        raise ValueError("base58() only supports non-negative integers")

    digits: List[str] = []
    current = value
    while current > 0:
        current, remainder = divmod(current, 58)
        digits.append(ALPHABET[remainder])

    if not digits:
        return "1"

    return "".join(reversed(digits))


def synth_address(hash160_hex: str) -> str:
    """Return a deterministic synthetic Bitcoin address for ``hash160_hex``."""

    payload = bytes.fromhex(hash160_hex)
    checksum_source = hashlib.sha256(payload).hexdigest()
    checksum_value = int(checksum_source, 16)
    return "1" + base58(checksum_value)[:33]


def synth_script(hash160_hex: str) -> str:
    """Return the pay-to-public-key-hash script for ``hash160_hex``."""

    return f"OP_DUP OP_HASH160 {hash160_hex} OP_EQUALVERIFY OP_CHECKSIG"


def _compute_hash160(payload: bytes) -> str:
    """Return the RIPEMD160(SHA256(payload)) digest."""

    sha256_digest = hashlib.sha256(payload).digest()
    return hashlib.new("ripemd160", sha256_digest).hexdigest()


def _puzzle_record(index: int, rnd: random.Random) -> Tuple[Dict[str, object], Dict[str, object]]:
    """Return the puzzle record and its checksum entry for ``index``."""

    payload = f"{index}|{rnd.random()}|{rnd.randrange(10**18)}".encode()
    hash160_hex = _compute_hash160(payload)
    record: Dict[str, object] = {
        "id": index,
        "name": f"Puzzle #{index:05d}",
        "hash160": hash160_hex,
        "address_base58": synth_address(hash160_hex),
        "script": synth_script(hash160_hex),
        "meta": {
            "network": "bitcoin-mainnet",
            "generated_by": "echo_colossus",
            "deterministic": True,
        },
    }
    checksum_blob = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    record["checksum"] = hashlib.sha256(checksum_blob).hexdigest()
    checksum_entry = {"id": index, "checksum": record["checksum"]}
    return record, checksum_entry


def write(root: Path | str, *, seed: int = 424242, count: int = 10_000) -> None:
    """Regenerate synthetic puzzle data rooted at ``root``.

    Parameters
    ----------
    root:
        Directory that contains the project checkout.  The script writes into
        ``data/puzzles`` and ``build/proofs`` relative to this path.
    seed:
        RNG seed that guarantees deterministic output (defaults to ``424242``).
    count:
        Number of puzzle JSON files to produce (defaults to ``10_000``).
    """

    root_path = Path(root)
    puzzle_dir = root_path / "data" / "puzzles"
    puzzle_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(seed)
    checksum_rows: List[Dict[str, object]] = []

    for index in range(1, count + 1):
        record, checksum = _puzzle_record(index, rng)
        target = puzzle_dir / f"puzzle_{index:05d}.json"
        target.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        checksum_rows.append(checksum)

    proof_dir = root_path / "build" / "proofs"
    proof_dir.mkdir(parents=True, exist_ok=True)

    summary = {"count": count, "checksums": checksum_rows}
    summary_path = proof_dir / "verification_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def regenerate_from_repo_root(count: int = 10_000) -> None:
    """Regenerate data using the repository root inferred from this file."""

    root = Path(__file__).resolve().parents[1]
    write(root, count=count)


if __name__ == "__main__":
    regenerate_from_repo_root()
