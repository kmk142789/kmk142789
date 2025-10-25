"""Checksum oracle for recovering Base58 fragments."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from puzzle_data import load_puzzles

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
ALPHABET_INDEX = {char: index for index, char in enumerate(ALPHABET)}

USAGE = """\
Echo Expansion — Checksum Oracle
================================
Reconstruct Base58Check-encoded addresses when prefix/suffix fragments are
known.  Examples:

  python scripts/checksum_oracle.py --prefix 12JzYkkN7 --suffix 6w2LAgsJg --hash160 0e5f3c406397442996825fd395543514fd06f207
  python scripts/checksum_oracle.py --prefix 1KCgMv8fo --suffix ne9uSNJ5F --hash160 c7a7b23f6bd98b8aaf527beb724dda9460b1bc6e
  python scripts/checksum_oracle.py --prefix 1FM --suffix isa --max-missing 3
"""


def b58decode(value: str) -> bytes:
    acc = 0
    for char in value:
        try:
            acc = acc * 58 + ALPHABET_INDEX[char]
        except KeyError as exc:  # pragma: no cover - defensive guard
            raise ValueError(f"invalid Base58 character: {char!r}") from exc
    raw = acc.to_bytes((acc.bit_length() + 7) // 8, "big") if acc else b""
    leading = 0
    for char in value:
        if char == "1":
            leading += 1
        else:
            break
    return b"\x00" * leading + raw


def b58encode(raw: bytes) -> str:
    acc = int.from_bytes(raw, "big")
    encoded = ""
    while acc:
        acc, mod = divmod(acc, 58)
        encoded = ALPHABET[mod] + encoded
    for byte in raw:
        if byte == 0:
            encoded = "1" + encoded
        else:
            break
    return encoded or "1"


def checksum(payload: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]


def expand_with_hash(prefix: str, suffix: str, hash160: str, version: int) -> Optional[str]:
    payload = bytes.fromhex(f"{version:02x}" + hash160)
    encoded = b58encode(payload + checksum(payload))
    if not encoded.startswith(prefix) or not encoded.endswith(suffix):
        return None
    return encoded


def enumerate_candidates(prefix: str, suffix: str, total_length: Optional[int], missing_len: int) -> Iterable[str]:
    if total_length is not None and len(prefix) + len(suffix) + missing_len != total_length:
        return []
    for combo in itertools.product(ALPHABET, repeat=missing_len):
        middle = "".join(combo)
        yield prefix + middle + suffix


def score_candidate(candidate: str, prefix: str, suffix: str) -> float:
    prefix_score = len(prefix) / len(candidate) if candidate else 0
    suffix_score = len(suffix) / len(candidate) if candidate else 0
    return round(prefix_score + suffix_score, 4)


def brute(prefix: str, suffix: str, checksum_hex: Optional[str], hash160: Optional[str], version: int, max_missing: int, total_length: Optional[int], limit: int) -> List[dict]:
    results: List[dict] = []
    if hash160:
        expanded = expand_with_hash(prefix, suffix, hash160, version)
        if expanded:
            results.append(
                {
                    "candidate": expanded,
                    "score": 1.0,
                    "source": "hash160",
                }
            )
            return results

    checksum_bytes = bytes.fromhex(checksum_hex) if checksum_hex else None
    for missing_len in range(0, max_missing + 1):
        for candidate in enumerate_candidates(prefix, suffix, total_length, missing_len):
            try:
                decoded = b58decode(candidate)
            except ValueError:
                continue
            if len(decoded) < 5:
                continue
            payload, check = decoded[:-4], decoded[-4:]
            if checksum_bytes and check != checksum_bytes:
                continue
            if check != checksum(payload):
                continue
            if version is not None and payload[0] != version:
                continue
            results.append(
                {
                    "candidate": candidate,
                    "score": score_candidate(candidate, prefix, suffix),
                    "source": f"brute_len_{missing_len}",
                }
            )
            if 0 < limit <= len(results):
                return results
    return results


def write_output(output_dir: Path, payload: dict) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = output_dir / f"oracle_{timestamp}.json"
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Recover Base58 fragments using checksum validation.")
    parser.add_argument("--prefix", required=True, help="Known prefix segment of the Base58 string.")
    parser.add_argument("--suffix", required=True, help="Known suffix segment of the Base58 string.")
    parser.add_argument("--checksum", help="Optional checksum bytes (8 hex characters).")
    parser.add_argument("--hash160", help="Optional HASH160 fingerprint to rebuild directly.")
    parser.add_argument("--version", type=lambda v: int(v, 0), default=0, help="Version byte (default 0 for P2PKH).")
    parser.add_argument("--max-missing", type=int, default=4, help="Maximum number of characters to brute force.")
    parser.add_argument("--length", type=int, help="Total expected length of the Base58 string.")
    parser.add_argument("--limit", type=int, default=25, help="Limit the number of candidates to keep.")
    parser.add_argument("--output", type=Path, default=Path("build/oracle"), help="Output directory for JSON artifacts.")
    args = parser.parse_args()

    print(USAGE)

    puzzles = load_puzzles()
    known_addresses = {p.address for p in puzzles}

    candidates = brute(
        prefix=args.prefix,
        suffix=args.suffix,
        checksum_hex=args.checksum,
        hash160=args.hash160,
        version=args.version,
        max_missing=args.max_missing,
        total_length=args.length,
        limit=args.limit,
    )

    payload = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "prefix": args.prefix,
            "suffix": args.suffix,
            "checksum": args.checksum,
            "hash160": args.hash160,
            "version": args.version,
            "max_missing": args.max_missing,
            "length": args.length,
            "limit": args.limit,
        },
        "candidates": candidates,
        "matches_repository": [item for item in candidates if item["candidate"] in known_addresses],
    }

    output_path = write_output(args.output, payload)
    print(f"[oracle] wrote {output_path} with {len(candidates)} candidate(s).")
    if not candidates:
        print("[oracle] No candidates found. Consider increasing --max-missing or providing --hash160.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
