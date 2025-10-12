"""Utilities for validating the 34K Satoshi-era public key dataset.

This script downloads (or reads from disk) the HTML dataset published at
https://bitcoin.oni.su/satoshi_public_keys/34K_2009_50.html and verifies that
each advertised Bitcoin address corresponds to the accompanying uncompressed
public key.  The verification is purely deterministic and does not require
network access beyond the optional dataset download.

Usage examples
--------------

Fetch the dataset directly from the remote host and verify all entries::

    python tools/verify_satoshi_34k_dataset.py

Run against a local snapshot to ensure reproducibility offline::

    python tools/verify_satoshi_34k_dataset.py path/to/local.html

The script prints a concise report that includes the dataset hash, entry
counts, and any mismatches that are discovered.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import html
import re
import sys
import urllib.request
from typing import Iterable, List, Sequence, Tuple


DATASET_URL = "https://bitcoin.oni.su/satoshi_public_keys/34K_2009_50.html"


BASE58_ALPHABET = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


@dataclasses.dataclass(frozen=True)
class DatasetEntry:
    """Container representing a public-key / address pair."""

    public_key_hex: str
    address: str


def parse_arguments(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source",
        nargs="?",
        default=DATASET_URL,
        help="Dataset location (URL or local path). Defaults to the canonical URL.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only validate the first N entries (useful for smoke tests).",
    )
    return parser.parse_args(argv)


def read_source(source: str) -> bytes:
    if re.match(r"^https?://", source):
        with urllib.request.urlopen(source) as response:  # nosec: trusted user input
            return response.read()
    return pathlib_path(source).read_bytes()


def pathlib_path(path: str):
    from pathlib import Path

    return Path(path)


def extract_entries(raw_html: bytes) -> List[DatasetEntry]:
    text = raw_html.decode("utf-8", errors="replace")
    pattern = re.compile(
        r"(?P<pub>04[0-9a-fA-F]{128})\s*<a[^>]+>(?P<addr>[123mn][a-km-zA-HJ-NP-Z1-9]{25,34})<",
        re.MULTILINE,
    )
    entries = []
    for match in pattern.finditer(text):
        pub_key = match.group("pub").lower()
        address = html.unescape(match.group("addr"))
        entries.append(DatasetEntry(pub_key, address))
    return entries


def pubkey_to_p2pkh_address(pubkey_hex: str) -> str:
    pub_bytes = bytes.fromhex(pubkey_hex)
    sha = hashlib.sha256(pub_bytes).digest()
    ripe = hashlib.new("ripemd160", sha).digest()
    payload = b"\x00" + ripe
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    return base58_encode(payload + checksum)


def base58_encode(data: bytes) -> str:
    num = int.from_bytes(data, byteorder="big")
    encoded = bytearray()
    while num > 0:
        num, remainder = divmod(num, 58)
        encoded.append(BASE58_ALPHABET[remainder])
    encoded.reverse()
    # Preserve leading zeroes as Base58's leading '1's.
    pad_length = len(data) - len(data.lstrip(b"\x00"))
    return (BASE58_ALPHABET[0:1] * pad_length + encoded).decode("ascii")


def validate_entries(entries: Iterable[DatasetEntry], limit: int | None = None) -> Tuple[int, List[Tuple[DatasetEntry, str]]]:
    mismatches: List[Tuple[DatasetEntry, str]] = []
    count = 0
    for entry in entries:
        if limit is not None and count >= limit:
            break
        derived_address = pubkey_to_p2pkh_address(entry.public_key_hex)
        if derived_address != entry.address:
            mismatches.append((entry, derived_address))
        count += 1
    return count, mismatches


def sha256_digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main(argv: Sequence[str]) -> int:
    args = parse_arguments(argv)
    raw_html = read_source(args.source)
    dataset_hash = sha256_digest(raw_html)
    entries = extract_entries(raw_html)
    validated_count, mismatches = validate_entries(entries, args.limit)

    print("Dataset source:", args.source)
    print("Dataset SHA-256:", dataset_hash)
    print(f"Parsed entries: {len(entries)}")
    if args.limit is not None:
        print(f"Validated subset: {validated_count} entries (limit={args.limit})")
    else:
        print(f"Validated entries: {validated_count}")

    if mismatches:
        print("\nMISMATCHES DETECTED:")
        for entry, derived in mismatches[:20]:
            print(f"  Address mismatch for {entry.public_key_hex[:16]}…")
            print(f"    Expected: {entry.address}")
            print(f"    Derived : {derived}")
        if len(mismatches) > 20:
            print(f"  … and {len(mismatches) - 20} more")
        return 1

    print("All validated entries match their derived P2PKH addresses.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
