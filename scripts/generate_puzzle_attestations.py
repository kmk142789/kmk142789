#!/usr/bin/env python3
"""Generate Echo attestation documents from Satoshi puzzle proofs."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOFS_DIR = ROOT / "satoshi" / "puzzle-proofs"
ATTEST_DIR = ROOT / "attestations"

_PATTERN = re.compile(r"^puzzle(\d+)([a-z]?)$")


def _format_created_at(path: Path) -> str:
    """Return an ISO-8601 timestamp derived from *path* mtime."""
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return mtime.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _attestation_label(num: int, suffix: str) -> str:
    if suffix:
        return f"#{num:03d}{suffix} authorship"
    return f"#{num:03d} authorship"


def build_attestation(proof_path: Path) -> dict[str, str] | None:
    data = json.loads(proof_path.read_text(encoding="utf-8"))
    message = data.get("message")
    signature = data.get("signature")
    address = data.get("address")
    if not (message and signature and address):
        return None
    if "attestation sha256" not in message:
        return None

    match = _PATTERN.fullmatch(proof_path.stem)
    if not match:
        return None

    num = int(match.group(1))
    suffix = match.group(2)

    return {
        "puzzle": _attestation_label(num, suffix),
        "address": address,
        "message": message,
        "signature": signature,
        "algo": "bitcoin-message-base64",
        "created_at": _format_created_at(proof_path),
        "hash_sha256": hashlib.sha256(signature.encode("utf-8")).hexdigest(),
        "notes": f"Imported from satoshi/puzzle-proofs/{proof_path.name} via scripts/generate_puzzle_attestations.py",
    }


def main() -> None:
    written: list[Path] = []
    for proof_path in sorted(PROOFS_DIR.glob("puzzle*.json")):
        match = _PATTERN.fullmatch(proof_path.stem)
        if not match:
            continue
        attestation_name = f"puzzle-{int(match.group(1)):03d}{match.group(2)}-authorship.json"
        attestation_path = ATTEST_DIR / attestation_name

        attestation = build_attestation(proof_path)
        if not attestation:
            continue

        if attestation_path.exists():
            try:
                existing = json.loads(attestation_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                existing = None
            if existing == attestation:
                continue
            notes = (existing or {}).get("notes", "")
            if "Imported from satoshi/puzzle-proofs" not in notes:
                continue

        attestation_path.write_text(
            json.dumps(attestation, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        written.append(attestation_path)

    if written:
        print(f"Wrote {len(written)} attestation files:")
        for path in written:
            print(f" - {path.relative_to(ROOT)}")
    else:
        print("No new attestations generated.")


if __name__ == "__main__":
    main()
