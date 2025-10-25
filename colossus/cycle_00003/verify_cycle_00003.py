"""Verification script for COLOSSUS cycle 00003."""

from __future__ import annotations

import json
from pathlib import Path


def load_dataset() -> dict:
    path = Path(__file__).resolve().with_name("dataset_cycle_00003.json")
    return json.loads(path.read_text(encoding="utf-8"))


def check_checksum(payload: dict) -> bool:
    harmonics = payload.get("harmonics", [])
    checksum = payload.get("checksum")
    return sum(harmonics) == checksum


def main() -> None:
    payload = load_dataset()
    if not check_checksum(payload):
        raise SystemExit("Checksum mismatch detected.")

    lineage_path = Path(__file__).resolve().with_name("lineage_map_00003.json")
    if not lineage_path.exists():
        raise SystemExit("Lineage map missing for this cycle.")

    print("Cycle 00003 verification successful.")


if __name__ == "__main__":
    main()
