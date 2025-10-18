#!/usr/bin/env python3
"""Summarise stacked Base64 signatures stored in puzzle proof attestations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from verifier.verify_puzzle_signature import SignatureCheckResult, verify_segments

PUZZLE_PROOF_DIR = Path(__file__).resolve().parent / "puzzle-proofs"


def iter_puzzle_files(root: Path = PUZZLE_PROOF_DIR) -> Iterable[Path]:
    """Yield puzzle proof JSON files sorted by puzzle identifier."""

    for path in sorted(root.glob("puzzle*.json")):
        if path.is_file():
            yield path


def analyse_puzzle_file(path: Path) -> dict[str, object]:
    """Return signature details for a single puzzle proof file."""

    payload = json.loads(path.read_text())
    address = payload["address"]
    message = payload["message"]
    signature_blob = payload["signature"]

    segments: list[SignatureCheckResult] = verify_segments(address, message, signature_blob)
    derived_addresses = sorted({segment.derived_address for segment in segments if segment.derived_address})

    return {
        "puzzle": payload["puzzle"],
        "address": address,
        "message": message,
        "segments": [segment.to_dict() for segment in segments],
        "valid_segment_count": sum(segment.valid for segment in segments),
        "total_segments": len(segments),
        "derived_addresses": derived_addresses,
    }


def build_report(root: Path = PUZZLE_PROOF_DIR) -> dict[str, object]:
    """Aggregate signature analysis for every puzzle proof in *root*."""

    puzzle_reports = [analyse_puzzle_file(path) for path in iter_puzzle_files(root)]
    all_addresses = sorted({addr for report in puzzle_reports for addr in report["derived_addresses"]})

    return {
        "puzzle_count": len(puzzle_reports),
        "total_segments": sum(report["total_segments"] for report in puzzle_reports),
        "unique_derived_addresses": all_addresses,
        "puzzles": puzzle_reports,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect concatenated Base64 signatures across all puzzle proof files.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=PUZZLE_PROOF_DIR,
        help="Directory containing puzzle proof JSON files (default: satoshi/puzzle-proofs)",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional file path for writing the JSON report instead of stdout",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report(args.root)

    json_kwargs: dict[str, object] = {"ensure_ascii": False}
    if args.pretty:
        json_kwargs["indent"] = 2

    output_text = json.dumps(report, **json_kwargs)
    if args.output:
        args.output.write_text(output_text + "\n")
    else:
        print(output_text)


if __name__ == "__main__":
    main()
