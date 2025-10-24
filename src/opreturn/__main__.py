"""Command line entry point for the OP_RETURN claim pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from .claims import (
    parse_claim_records,
    validate_claim_windows,
    write_actionable_report,
)


def _load_transactions(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
        if isinstance(payload, dict):
            return [payload]
        if isinstance(payload, list):
            return payload
    raise ValueError("Unsupported input payload (expected list or dict).")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OP_RETURN claim pipeline")
    parser.add_argument("input", type=Path, help="Path to transaction JSON payload")
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--csv-output", type=Path, required=True)
    parser.add_argument(
        "--as-of",
        type=str,
        default=None,
        help="Optional ISO-8601 timestamp overriding the validation clock.",
    )

    args = parser.parse_args(argv)
    transactions = _load_transactions(args.input)

    claims = parse_claim_records(transactions)
    validated = validate_claim_windows(claims)

    write_actionable_report(
        validated,
        json_path=args.json_output,
        csv_path=args.csv_output,
    )

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI passthrough
    raise SystemExit(main())

