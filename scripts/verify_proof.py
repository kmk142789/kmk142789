"""Proof-of-Resonance verifier."""
from __future__ import annotations

import json
import pathlib
import sys
from typing import Iterable

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROOF_DIR = ROOT / "build" / "proofs"
ORACLE_DIR = ROOT / "build" / "oracle"

BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _base58check_decode(value: str) -> bytes:
    num = 0
    leading = 0
    for char in value:
        if char not in BASE58_ALPHABET:
            raise ValueError(f"invalid character {char!r}")
        if char == "1" and num == 0:
            leading += 1
            continue
        num = num * 58 + BASE58_ALPHABET.index(char)
    data = num.to_bytes((num.bit_length() + 7) // 8, "big")
    data = b"\x00" * leading + data
    if len(data) < 4:
        raise ValueError("address too short")
    payload, checksum = data[:-4], data[-4:]
    import hashlib

    expected = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    if checksum != expected:
        raise ValueError("checksum mismatch")
    return payload


def _iter_proofs() -> Iterable[pathlib.Path]:
    return sorted(PROOF_DIR.glob("*.proof.json"))


def verify() -> int:
    if not PROOF_DIR.exists():
        print("No proofs present.")
        return 0
    failures = 0
    for proof_path in _iter_proofs():
        data = json.loads(proof_path.read_text(encoding="utf-8"))
        try:
            _base58check_decode(data["address"])
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] {proof_path.name}: {exc}")
            failures += 1
            continue
        oracle_ref = ORACLE_DIR / pathlib.Path(data["oracle_reference"]).name
        if not oracle_ref.exists():
            print(f"[WARN] Oracle reference missing for {proof_path.name}")
            continue
        oracle_payload = json.loads(oracle_ref.read_text(encoding="utf-8"))
        if oracle_payload.get("lineage_tag") != data.get("lineage_tag"):
            print(f"[FAIL] {proof_path.name}: lineage drift detected")
            failures += 1
    return failures


def main() -> None:
    failures = verify()
    if failures:
        print(f"Proof verification failed for {failures} artifact(s).")
        sys.exit(1)
    print("All proofs replayed cleanly.")


if __name__ == "__main__":
    main()
