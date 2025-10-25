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
address, or the 20-byte hash160 fingerprint.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from . import puzzle_dataset


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


def _hash160_to_p2pkh_address(hash160_hex: str, *, version: int = 0x00) -> str:
    """Encode a ``hash160`` fingerprint into a legacy Base58 address."""

    payload = bytes([version]) + bytes.fromhex(hash160_hex)
    checksum = _double_sha256(payload)[:4]
    return _b58encode(payload + checksum)


def _derive_p2pkh_address(pubkey_hex: str) -> str:
    """Compute the legacy address from the provided compressed key."""

    pubkey_bytes = bytes.fromhex(pubkey_hex)
    sha = hashlib.sha256(pubkey_bytes).digest()
    ripe = hashlib.new("ripemd160", sha).digest()
    return _hash160_to_p2pkh_address(ripe.hex())


def _hash160_from_pubkey(pubkey_hex: str) -> str:
    pubkey_bytes = bytes.fromhex(pubkey_hex)
    sha = hashlib.sha256(pubkey_bytes).digest()
    return hashlib.new("ripemd160", sha).hexdigest()


def _compress_pubkey_hex(pubkey_hex: str) -> Optional[str]:
    cleaned = pubkey_hex.lower().strip()
    if len(cleaned) != 130 or not cleaned.startswith("04"):
        return None
    x = cleaned[2:66]
    y = int(cleaned[66:], 16)
    prefix = "02" if y % 2 == 0 else "03"
    return prefix + x


def _decode_script(script: str) -> "decode_pkscript.DecodedScript":
    """Decode a canonical script string into its structured representation."""

    script = script.strip()
    if not script:
        raise ValueError("Empty script provided")

    try:
        from tools import decode_pkscript
    except ImportError as exc:  # pragma: no cover - defensive guard
        raise ValueError("Unable to import decoder utilities") from exc

    try:
        return decode_pkscript.decode_p2pkh_script(script, network="mainnet")
    except decode_pkscript.ScriptDecodeError as exc:
        raise ValueError(str(exc)) from exc


def _load_solutions(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _match_entry(
    entries: Iterable[Dict[str, Any]],
    *,
    bits: Optional[int] = None,
    address: Optional[str] = None,
    hash160: Optional[str] = None,
    pubkey: Optional[str] = None,
) -> Dict[str, Any]:
    target_hashes = set()
    if hash160:
        target_hashes.add(hash160.lower())

    pubkey_candidates = set()
    if pubkey:
        cleaned = pubkey.lower()
        pubkey_candidates.add(cleaned)
        compressed = _compress_pubkey_hex(cleaned)
        if compressed:
            pubkey_candidates.add(compressed)
            target_hashes.add(_hash160_from_pubkey(compressed))
        target_hashes.add(_hash160_from_pubkey(cleaned))

    for entry in entries:
        if bits is not None and entry.get("bits") == bits:
            return entry
        if address and entry.get("address") == address:
            return entry
        entry_hash = entry.get("hash160_compressed", "").lower()
        if target_hashes and entry_hash in target_hashes:
            return entry
        entry_pubkey = entry.get("public_key", "").strip().lower()
        if pubkey_candidates and entry_pubkey in pubkey_candidates:
            return entry
    raise SystemExit("Could not locate a matching puzzle entry.")


def _entry_to_solution(entry: Dict[str, Any]) -> puzzle_dataset.PuzzleSolution:
    """Hydrate a :class:`PuzzleSolution` from a raw JSON dataset entry."""

    return puzzle_dataset.PuzzleSolution(
        bits=int(entry["bits"]),
        range_min=str(entry["range_min"]),
        range_max=str(entry["range_max"]),
        address=str(entry["address"]),
        btc_value=float(entry["btc_value"]),
        hash160_compressed=str(entry["hash160_compressed"]),
        public_key=str(entry["public_key"]),
        private_key=str(entry["private_key"]),
        solve_date=str(entry["solve_date"]),
    )


def main(argv: Optional[Iterable[str]] = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("bits", type=int, nargs="?", help="Puzzle bits number to look up")
    group.add_argument("--address", help="Bitcoin address to match")
    group.add_argument("--hash160", help="Legacy hash160 fingerprint to match")
    group.add_argument("--pkscript", help="Decode a canonical P2PKH script and match the entry")
    parser.add_argument(
        "--solutions",
        type=Path,
        default=SOLUTIONS_PATH,
        help="Path to puzzle_solutions.json (defaults to repository copy)",
    )
    parser.add_argument(
        "--show-script",
        action="store_true",
        help="Display the canonical P2PKH script for the matched puzzle entry",
    )

    args = parser.parse_args(argv)

    entries = _load_solutions(args.solutions)
    decoded_script = None
    decoded_hash = None
    decoded_address = None
    decoded_pubkey = None
    if args.pkscript:
        decoded_script = _decode_script(args.pkscript)
        decoded_hash = decoded_script.pubkey_hash
        decoded_pubkey = decoded_script.pubkey
        if decoded_script.script_type in {"p2pkh", "p2pk"}:
            decoded_address = decoded_script.address

    entry = _match_entry(
        entries,
        bits=args.bits,
        address=args.address or decoded_address,
        hash160=args.hash160 or decoded_hash,
        pubkey=decoded_pubkey,
    )

    pubkey = entry["public_key"].strip()
    private_key = entry["private_key"].strip()

    derived_address = None
    compressed: Optional[bool] = None
    if pubkey:
        derived_address = _derive_p2pkh_address(pubkey)
        compressed = _pubkey_is_compressed(pubkey)

    print(f"Puzzle bits   : {entry['bits']}")
    print(f"Address       : {entry['address']}")
    print(f"Hash160       : {entry['hash160_compressed']}")
    print(f"Public key    : {pubkey or '(unavailable)'}")
    print(f"Private key   : {private_key or '(unavailable)'}")

    if private_key:
        wif_compressed = compressed if compressed is not None else True
        wif = _hex_priv_to_wif(private_key, compressed=wif_compressed)
        label = "compressed" if wif_compressed else "uncompressed"
        print(f"WIF ({label}): {wif}")
    else:
        if compressed is None:
            print("WIF           : (unavailable)")
        else:
            label = "compressed" if compressed else "uncompressed"
            print(f"WIF ({label}): (unavailable)")

    if derived_address and derived_address != entry["address"]:
        print(f"Derived address mismatch: {derived_address}")
    if decoded_script:
        print("\nDecoded from PkScript:")
        print(f"  Script type : {decoded_script.script_type}")
        if decoded_script.pubkey:
            print(f"  Public key  : {decoded_script.pubkey}")
        if decoded_script.pubkey_hash:
            label = "Hash160" if decoded_script.script_type in {"p2pk", "p2pkh"} else "Witness prog"
            print(f"  {label:<12}: {decoded_script.pubkey_hash}")
        print(f"  Address     : {decoded_script.address}")

    if args.show_script:
        solution = _entry_to_solution(entry)
        script_asm = solution.p2pkh_script()
        script_hex = solution.p2pkh_script_hex()
        print("\nCanonical P2PKH script:")
        print(f"  ASM : {script_asm}")
        print(f"  HEX : {script_hex}")


if __name__ == "__main__":  # pragma: no cover - simple CLI wrapper
    main()
