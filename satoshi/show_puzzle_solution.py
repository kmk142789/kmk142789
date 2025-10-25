"""Utility helpers for inspecting Bitcoin puzzle solutions.

This module exposes a small CLI that makes it easy to look up a
particular entry from ``puzzle_solutions.json`` and display the core
details in a human friendly format.  It also derives the legacy Base58
address and the Wallet Import Format (WIF) encoding for the stored
private key so that the record can be compared against on-chain
metadata such as the provided PkScript.

Example usage:

.. code-block:: console

    $ python -m satoshi.show_puzzle_solution 18
    Puzzle bits   : 18
    Address       : 1GnNTmTVLZiqQfLbAdp9DVdicEnB5GoERE
    Hash160       : ad1e852b08eba53df306ec9daa8c643426953f94
    Public key    : 020ce4a3291b19d2e1a7bf73ee87d30a6bdbc72b20771e7dfff40d0db755cd4af1
    Private key   : 000000000000000000000000000000000000000000000000000000000003080d
    WIF (compressed): KzA4xmBM1SwLk4N3C6grkFuFdEASpnEEa5GmR2v4EJUNvqh7Q6kL

The command accepts either the puzzle ``bits`` value, the Bitcoin
address, the 20-byte hash160 fingerprint, or a canonical P2PKH locking
script.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from tools.decode_pkscript import ScriptDecodeError, decode_p2pkh_script


REPO_ROOT = Path(__file__).resolve().parents[1]
SOLUTIONS_PATH = REPO_ROOT / "satoshi" / "puzzle_solutions.json"


def _double_sha256(data: bytes) -> bytes:
    """Return ``sha256(sha256(data))``."""

    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _b58encode(data: bytes) -> str:
    """Minimal Base58 encoder for Bitcoin serialization needs."""

    # Interpret the payload as a big endian integer.
    num = int.from_bytes(data, "big")
    enc = []
    while num > 0:
        num, rem = divmod(num, 58)
        enc.append(_ALPHABET[rem])
    # Account for leading zeroes which translate to the first Base58 digit.
    stripped = data.lstrip(b"\x00")
    pad = len(data) - len(stripped)
    return "1" * pad + "".join(reversed(enc or ["1"]))


def _hex_priv_to_wif(hex_key: str, *, compressed: bool = True, version: int = 0x80) -> str:
    """Convert a hexadecimal private key into WIF notation."""

    payload = bytes([version]) + bytes.fromhex(hex_key)
    if compressed:
        payload += b"\x01"
    checksum = _double_sha256(payload)[:4]
    return _b58encode(payload + checksum)


def _pubkey_is_compressed(pubkey_hex: str) -> bool:
    """Infer whether the stored public key uses the compressed form."""

    return len(pubkey_hex) == 66 and pubkey_hex[:2] in {"02", "03"}


def _derive_p2pkh_address(pubkey_hex: str) -> str:
    """Compute the legacy address from the provided compressed key."""

    pubkey_bytes = bytes.fromhex(pubkey_hex)
    sha = hashlib.sha256(pubkey_bytes).digest()
    ripe = hashlib.new("ripemd160", sha).digest()
    payload = b"\x00" + ripe
    checksum = _double_sha256(payload)[:4]
    return _b58encode(payload + checksum)


def _load_solutions(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _match_entry(
    entries: Iterable[Dict[str, Any]],
    *,
    bits: Optional[int] = None,
    address: Optional[str] = None,
    hash160: Optional[str] = None,
) -> Dict[str, Any]:
    target_hash = hash160.lower() if hash160 else None
    for entry in entries:
        if bits is not None and entry.get("bits") == bits:
            return entry
        if address and entry.get("address") == address:
            return entry
        if target_hash and entry.get("hash160_compressed", "").lower() == target_hash:
            return entry
    raise SystemExit("Could not locate a matching puzzle entry.")


def _load_pkscript_text(value: str) -> str:
    """Return the textual script from ``value`` or by reading a file."""

    candidate = Path(value)
    if candidate.is_file():
        try:
            return candidate.read_text(encoding="utf-8")
        except OSError as exc:  # pragma: no cover - defensive guard
            raise SystemExit(f"Could not read PkScript file: {exc}")
    return value


def _hash160_from_pkscript(pkscript: str) -> str:
    """Extract the canonical hash160 payload from a textual P2PKH script."""

    decoded = decode_p2pkh_script(pkscript)
    return decoded.pubkey_hash.lower()


def main(argv: Optional[Iterable[str]] = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("bits", type=int, nargs="?", help="Puzzle bits number to look up")
    group.add_argument("--address", help="Bitcoin address to match")
    group.add_argument("--hash160", help="Legacy hash160 fingerprint to match")
    group.add_argument(
        "--pkscript",
        help="Canonical P2PKH script to match (or a path to a file containing the script)",
    )
    parser.add_argument(
        "--solutions",
        type=Path,
        default=SOLUTIONS_PATH,
        help="Path to puzzle_solutions.json (defaults to repository copy)",
    )

    args = parser.parse_args(argv)

    entries = _load_solutions(args.solutions)
    derived_hash160: Optional[str] = None
    if args.pkscript:
        try:
            script_text = _load_pkscript_text(args.pkscript)
            derived_hash160 = _hash160_from_pkscript(script_text)
        except ScriptDecodeError as exc:  # pragma: no cover - defensive guard
            raise SystemExit(f"Could not parse provided PkScript: {exc}")

    entry = _match_entry(
        entries,
        bits=args.bits,
        address=args.address,
        hash160=args.hash160 or derived_hash160,
    )

    pubkey = entry["public_key"]
    derived_address = _derive_p2pkh_address(pubkey)
    compressed = _pubkey_is_compressed(pubkey)
    wif = _hex_priv_to_wif(entry["private_key"], compressed=compressed)

    print(f"Puzzle bits   : {entry['bits']}")
    print(f"Address       : {entry['address']}")
    print(f"Hash160       : {entry['hash160_compressed']}")
    print(f"Public key    : {pubkey}")
    print(f"Private key   : {entry['private_key']}")
    print(f"WIF ({'compressed' if compressed else 'uncompressed'}): {wif}")
    if derived_address != entry["address"]:
        print(f"Derived address mismatch: {derived_address}")


if __name__ == "__main__":  # pragma: no cover - simple CLI wrapper
    main()
