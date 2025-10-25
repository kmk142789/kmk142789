"""Echo Oracle Layer utilities.

Validates puzzle solutions, repairs Base58 gaps, and emits structured
artifacts used by downstream verification and documentation layers.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import time
from dataclasses import dataclass, asdict
from typing import Dict, Iterable, List, Sequence

ROOT = pathlib.Path(__file__).resolve().parents[1]
PUZZLE_DIR = ROOT / "puzzle_solutions"
ORACLE_DIR = ROOT / "build" / "oracle"
PROOF_DIR = ROOT / "build" / "proofs"

ADDRESS_RE = re.compile(r"(?:^|`)((?:[13]|bc1)[0-9A-Za-z]{20,})")
HASH_RE = re.compile(r"hash160\*?:\s*`?([0-9a-fA-F]{40})`?", re.IGNORECASE)

BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


@dataclass
class PuzzleInsight:
    puzzle_id: str
    address: str
    hash160: str | None
    checksum_valid: bool
    repaired_address: str | None
    payload_hex: str | None
    lineage_tag: str


def _iter_puzzles() -> Iterable[pathlib.Path]:
    return sorted(PUZZLE_DIR.glob("*.md"))


def _extract_metadata(path: pathlib.Path) -> Sequence[PuzzleInsight]:
    text = path.read_text(encoding="utf-8")
    addresses = ADDRESS_RE.findall(text)
    hash_match = HASH_RE.search(text)
    hash160 = hash_match.group(1).lower() if hash_match else None
    insights: List[PuzzleInsight] = []
    for address in addresses:
        payload, checksum_valid = _base58check_decode(address)
        repaired = None
        payload_hex = None
        if payload is not None:
            payload_hex = payload.hex()
        elif hash160 is not None:
            repaired = _rebuild_base58(hash160)
        lineage_tag = _lineage_tag(path.stem, address, hash160)
        insights.append(
            PuzzleInsight(
                puzzle_id=path.stem,
                address=address,
                hash160=hash160,
                checksum_valid=checksum_valid,
                repaired_address=repaired,
                payload_hex=payload_hex,
                lineage_tag=lineage_tag,
            )
        )
    return insights


def _base58check_decode(value: str) -> tuple[bytes | None, bool]:
    try:
        num = 0
        leading = 0
        for char in value:
            if char == "1" and num == 0:
                leading += 1
                continue
            num *= 58
            num += BASE58_ALPHABET.index(char)
        combined = num.to_bytes((num.bit_length() + 7) // 8, "big")
        combined = b"\x00" * leading + combined
    except ValueError:
        return None, False
    if len(combined) < 4:
        return None, False
    payload, checksum = combined[:-4], combined[-4:]
    import hashlib

    computed = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    return payload, checksum == computed


def _rebuild_base58(hash160: str) -> str:
    import hashlib

    version = bytes([0x00])
    payload = version + bytes.fromhex(hash160)
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    data = int.from_bytes(payload + checksum, "big")
    digits = []
    while data:
        data, rem = divmod(data, 58)
        digits.append(BASE58_ALPHABET[rem])
    raw = payload + checksum
    leading = 0
    for byte in raw:
        if byte == 0:
            leading += 1
        else:
            break
    prefix = "1" * leading
    return prefix + "".join(reversed(digits or ["1"]))


def _lineage_tag(puzzle_id: str, address: str, hash160: str | None) -> str:
    import hashlib

    components = "|".join(filter(None, [puzzle_id, address, hash160 or "none"]))
    digest = hashlib.sha256(components.encode("utf-8")).hexdigest()
    return digest[:24]


def ensure_directories() -> None:
    ORACLE_DIR.mkdir(parents=True, exist_ok=True)
    PROOF_DIR.mkdir(parents=True, exist_ok=True)


def emit_oracle(insight: PuzzleInsight) -> None:
    record: Dict[str, object] = asdict(insight)
    record["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    artifact_stem = f"{insight.puzzle_id}-{insight.lineage_tag}"
    target = ORACLE_DIR / f"{artifact_stem}.json"
    target.write_text(json.dumps(record, indent=2), encoding="utf-8")


def emit_proof(insight: PuzzleInsight) -> None:
    proof = {
        "puzzle_id": insight.puzzle_id,
        "address": insight.address,
        "hash160": insight.hash160,
        "checksum_valid": insight.checksum_valid,
        "repaired_address": insight.repaired_address,
        "payload_hex": insight.payload_hex,
        "lineage_tag": insight.lineage_tag,
        "oracle_reference": f"oracle/{insight.puzzle_id}-{insight.lineage_tag}.json",
    }
    artifact_stem = f"{insight.puzzle_id}-{insight.lineage_tag}"
    target = PROOF_DIR / f"{artifact_stem}.proof.json"
    target.write_text(json.dumps(proof, indent=2), encoding="utf-8")


def run(repair_only: bool = False) -> List[PuzzleInsight]:
    ensure_directories()
    insights: List[PuzzleInsight] = []
    for path in _iter_puzzles():
        extracted = _extract_metadata(path)
        if not extracted:
            continue
        for insight in extracted:
            if not repair_only:
                emit_oracle(insight)
                emit_proof(insight)
            insights.append(insight)
    return insights


def main() -> None:
    parser = argparse.ArgumentParser(description="Echo Oracle Layer")
    parser.add_argument(
        "--repair-only",
        action="store_true",
        help="Skip writing outputs; useful for CI recovery attempts.",
    )
    args = parser.parse_args()
    insights = run(repair_only=args.repair_only)
    valid = sum(1 for insight in insights if insight.checksum_valid)
    print(f"Oracle scanned {len(insights)} addresses: {valid} valid checksums")


if __name__ == "__main__":
    main()
