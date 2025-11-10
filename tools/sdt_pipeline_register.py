#!/usr/bin/env python3
"""Utility for validating Sovereign Digital Trust funding pipeline sections."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, Tuple


def load_json(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise SystemExit(f"Missing required file: {path}") from exc


def iter_section_files(sections_dir: Path) -> Iterable[Path]:
    if not sections_dir.exists():
        raise SystemExit(f"Sections directory not found: {sections_dir}")
    for path in sorted(sections_dir.glob("section_*.jsonl")):
        if path.is_file():
            yield path


def validate_record(record: dict, schema: dict, *, path: Path, line_no: int) -> None:
    required = schema.get("required", [])
    missing = [field for field in required if not record.get(field)]
    if missing:
        missing_list = ", ".join(missing)
        raise SystemExit(
            f"{path}:{line_no}: missing required field(s): {missing_list}"
        )

    properties = schema.get("properties", {})
    for field, value in record.items():
        if field not in properties:
            raise SystemExit(f"{path}:{line_no}: unexpected field '{field}'")
        spec = properties[field]
        if spec.get("enum") and value not in spec["enum"]:
            allowed = ", ".join(spec["enum"])
            raise SystemExit(
                f"{path}:{line_no}: invalid value '{value}' for '{field}' (allowed: {allowed})"
            )

    if schema.get("additionalProperties", True) is False:
        for field in record:
            if field not in properties:
                raise SystemExit(f"{path}:{line_no}: unexpected field '{field}'")


def load_and_validate_sections(
    base_dir: Path, schema: dict
) -> Tuple[int, list[tuple[Path, int]]]:
    sections_dir = base_dir / "sections"
    total = 0
    section_summaries: list[tuple[Path, int]] = []

    for section_file in iter_section_files(sections_dir):
        section_count = 0
        with section_file.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise SystemExit(
                        f"{section_file}:{line_no}: invalid JSON: {exc}"
                    ) from exc
                validate_record(record, schema, path=section_file, line_no=line_no)
                section_count += 1
        section_summaries.append((section_file, section_count))
        total += section_count

    return total, section_summaries


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Sovereign Digital Trust funding pipeline sections and report totals."
        )
    )
    parser.add_argument(
        "--base-dir",
        default=Path("data/sovereign_digital_trust"),
        type=Path,
        help="Base directory containing metadata.json, schema.json, and a sections/ folder.",
    )
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Exit with an error if the aggregated count does not match metadata.expected_wallet_count.",
    )

    args = parser.parse_args(argv)

    base_dir = args.base_dir
    metadata_path = base_dir / "metadata.json"
    schema_path = base_dir / "schema.json"

    metadata = load_json(metadata_path)
    schema = load_json(schema_path)

    expected_total = metadata.get("expected_wallet_count")
    if expected_total is None:
        raise SystemExit(
            f"metadata.json at {metadata_path} must define 'expected_wallet_count'"
        )

    total, section_summaries = load_and_validate_sections(base_dir, schema)

    if not section_summaries:
        print("No section files discovered. Add section_*.jsonl files to proceed.")
    else:
        for section_path, count in section_summaries:
            print(f"{section_path.name}: {count} entries")

    print(f"Aggregated entries: {total}")
    print(f"Expected entries:   {expected_total}")

    if total != expected_total and args.require_complete:
        print(
            "ERROR: aggregated entry count does not match expected total.",
            file=sys.stderr,
        )
        return 1

    if total != expected_total:
        print(
            "WARNING: dataset incomplete — update sections to reach the expected total."
        )
    else:
        print("SUCCESS: dataset matches the expected total.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

