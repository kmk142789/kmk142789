"""Regression tests for the high-value Bitcoin puzzle dataset entries."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.update_puzzle_dataset import entries

DATA_PATH = Path(__file__).resolve().parents[1] / "satoshi" / "puzzle_solutions.json"


def test_puzzle_solutions_contains_tracked_entries() -> None:
    """Ensure every curated high-bit puzzle entry is present and accurate."""
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    dataset_by_bits = {item["bits"]: item for item in payload}

    missing_bits = [entry["bits"] for entry in entries if entry["bits"] not in dataset_by_bits]
    assert not missing_bits, f"Missing dataset entries for bit ranges: {missing_bits}"

    for expected in entries:
        dataset_entry = dataset_by_bits[expected["bits"]]
        for field, value in expected.items():
            assert dataset_entry[field] == value, (
                f"Mismatch for puzzle {expected['bits']} field '{field}': "
                f"expected {value!r}, observed {dataset_entry[field]!r}"
            )
