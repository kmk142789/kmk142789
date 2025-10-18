#!/usr/bin/env python3
"""Generate a verification summary for the Satoshi puzzle proofs.

This script loads every JSON document under ``puzzle-proofs/`` and verifies
all of the signature segments contained in each file.  The resulting table is
written to ``verification-summary.md`` in the same directory as this script.

The script relies on the ``verify_segments`` helper that powers the
``verifier/verify_puzzle_signature.py`` CLI utility so that the exact same
verification routine is reused in both places.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from verifier.verify_puzzle_signature import SignatureCheckResult, verify_segments


@dataclass(frozen=True)
class PuzzleProof:
    """Structured representation of a single puzzle proof document."""

    puzzle: int
    address: str
    message: str
    signature: str
    source_path: Path

    @classmethod
    def from_path(cls, path: Path) -> "PuzzleProof":
        payload = json.loads(path.read_text())
        return cls(
            puzzle=payload["puzzle"],
            address=payload["address"],
            message=payload["message"],
            signature=payload["signature"],
            source_path=path,
        )


@dataclass(frozen=True)
class VerificationSummary:
    """Aggregated verification metadata for a proof."""

    proof: PuzzleProof
    segments: List[SignatureCheckResult]

    @property
    def valid_segment_count(self) -> int:
        return sum(result.valid for result in self.segments)

    @property
    def total_segment_count(self) -> int:
        return len(self.segments)

    @property
    def is_fully_verified(self) -> bool:
        return self.valid_segment_count > 0 and self.valid_segment_count == self.total_segment_count


def iter_proofs(root: Path) -> Iterable[PuzzleProof]:
    for path in sorted(root.glob("puzzle*.json")):
        yield PuzzleProof.from_path(path)


def generate_summary_rows(proofs: Iterable[PuzzleProof]) -> List[VerificationSummary]:
    rows: List[VerificationSummary] = []
    for proof in proofs:
        segments = verify_segments(proof.address, proof.message, proof.signature)
        rows.append(VerificationSummary(proof=proof, segments=segments))
    return rows


def render_markdown(rows: List[VerificationSummary]) -> str:
    header = [
        "# Verification Summary",
        "",
        "This report enumerates every puzzle proof under `puzzle-proofs/` and runs the",
        "same secp256k1 signature verification routine used by `verifier/verify_puzzle_signature.py`.",
        "A proof is marked as _Fully Valid_ when every extracted signature segment matches",
        "the expected public key for the associated Bitcoin address.",
        "",
        "| Puzzle | Address | Valid Segments | Total Segments | Fully Valid |",
        "| ------ | ------- | -------------- | -------------- | ----------- |",
    ]
    body_lines: List[str] = []
    for row in rows:
        body_lines.append(
            "| {puzzle} | `{address}` | {valid} | {total} | {status} |".format(
                puzzle=row.proof.puzzle,
                address=row.proof.address,
                valid=row.valid_segment_count,
                total=row.total_segment_count,
                status="✅" if row.is_fully_verified else "⚠️",
            )
        )
    footer = [
        "",
        "To regenerate this table run `python satoshi/build_verification_summary.py` from the",
        "repository root. The script rewrites this file in place.",
    ]
    return "\n".join(header + body_lines + footer) + "\n"


def main() -> None:
    root = Path(__file__).resolve().parent
    proofs_dir = root / "puzzle-proofs"
    rows = generate_summary_rows(iter_proofs(proofs_dir))
    output_path = root / "verification-summary.md"
    output_path.write_text(render_markdown(rows))


if __name__ == "__main__":
    main()
