#!/usr/bin/env python3
"""Lightweight verifier for OP_RETURN claim report artefacts."""

from __future__ import annotations

import argparse
import glob
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping, MutableSequence, Sequence


RECOMMENDATIONS = {
    "no_action",
    "requires_claim_review",
    "eligible_for_authorized_collection",
    "not_applicable",
}


@dataclass(slots=True)
class ValidationIssue:
    path: Path
    message: str

    def format(self) -> str:
        return f"{self.path}: {self.message}"


def _parse_iso8601(value: str, *, field: str, path: Path, issues: MutableSequence[ValidationIssue]) -> None:
    try:
        # ``fromisoformat`` handles the variants produced by the pipeline.
        datetime.fromisoformat(value)
    except ValueError:
        issues.append(ValidationIssue(path, f"invalid ISO-8601 timestamp for '{field}': {value!r}"))


def _ensure(condition: bool, *, path: Path, message: str, issues: MutableSequence[ValidationIssue]) -> None:
    if not condition:
        issues.append(ValidationIssue(path, message))


def _validate_summary(summary: Mapping[str, object], *, path: Path, issues: MutableSequence[ValidationIssue]) -> None:
    required_fields: Mapping[str, type] = {
        "claimant": str,
        "generated_at": str,
        "count": int,
        "window_phrase": str,
        "secondary_phrase": str,
    }
    for key, expected_type in required_fields.items():
        value = summary.get(key)
        _ensure(isinstance(value, expected_type), path=path, message=f"summary.{key} must be {expected_type.__name__}", issues=issues)
        if key == "generated_at" and isinstance(value, str):
            _parse_iso8601(value, field="summary.generated_at", path=path, issues=issues)
    count = summary.get("count")
    if isinstance(count, int) and count < 0:
        issues.append(ValidationIssue(path, "summary.count must be non-negative"))


def _validate_checklist(items: Iterable[object], *, path: Path, issues: MutableSequence[ValidationIssue]) -> None:
    checklist = list(items)
    _ensure(all(isinstance(entry, str) and entry.strip() for entry in checklist), path=path, message="review_checklist must only contain non-empty strings", issues=issues)


def _validate_entities(entities: Iterable[Mapping[str, object]], *, path: Path, issues: MutableSequence[ValidationIssue], base: str) -> None:
    for idx, entity in enumerate(entities):
        prefix = f"{base}[{idx}]"
        _ensure(isinstance(entity.get("index"), int), path=path, message=f"{prefix}.index must be an integer", issues=issues)
        _ensure(isinstance(entity.get("script_type"), str), path=path, message=f"{prefix}.script_type must be a string", issues=issues)
        address = entity.get("address")
        if address is not None:
            _ensure(isinstance(address, str), path=path, message=f"{prefix}.address must be a string or null", issues=issues)
        _ensure(isinstance(entity.get("raw_script"), str), path=path, message=f"{prefix}.raw_script must be a string", issues=issues)
        value = entity.get("value_sats")
        if value is not None:
            _ensure(isinstance(value, int) and value >= 0, path=path, message=f"{prefix}.value_sats must be a positive integer or null", issues=issues)


def _validate_record(record: Mapping[str, object], *, index: int, path: Path, issues: MutableSequence[ValidationIssue]) -> None:
    prefix = f"records[{index}]"
    _ensure(isinstance(record.get("txid"), str), path=path, message=f"{prefix}.txid must be a string", issues=issues)
    block_time = record.get("block_time")
    _ensure(isinstance(block_time, str), path=path, message=f"{prefix}.block_time must be an ISO string", issues=issues)
    if isinstance(block_time, str):
        _parse_iso8601(block_time, field=f"{prefix}.block_time", path=path, issues=issues)
    _ensure(isinstance(record.get("op_return_message"), str), path=path, message=f"{prefix}.op_return_message must be a string", issues=issues)
    _ensure(isinstance(record.get("clause_detected"), bool), path=path, message=f"{prefix}.clause_detected must be a boolean", issues=issues)
    clause_variant = record.get("clause_variant")
    if clause_variant is not None:
        _ensure(isinstance(clause_variant, str), path=path, message=f"{prefix}.clause_variant must be a string or null", issues=issues)
    window_days = record.get("inactivity_window_days")
    if window_days is not None:
        _ensure(isinstance(window_days, int) and window_days > 0, path=path, message=f"{prefix}.inactivity_window_days must be a positive integer", issues=issues)
    window_end = record.get("inactivity_window_end")
    if window_end is not None:
        _ensure(isinstance(window_end, str), path=path, message=f"{prefix}.inactivity_window_end must be an ISO string or null", issues=issues)
        if isinstance(window_end, str):
            _parse_iso8601(window_end, field=f"{prefix}.inactivity_window_end", path=path, issues=issues)
    derived_entities = record.get("derived_entities", [])
    if isinstance(derived_entities, list):
        _validate_entities(derived_entities, path=path, issues=issues, base=f"{prefix}.derived_entities")
    else:
        issues.append(ValidationIssue(path, f"{prefix}.derived_entities must be a list"))
    recommendation = record.get("recommendation")
    _ensure(isinstance(recommendation, str) and recommendation in RECOMMENDATIONS, path=path, message=f"{prefix}.recommendation must be one of {sorted(RECOMMENDATIONS)}", issues=issues)
    verification_notes = record.get("verification_notes")
    if verification_notes is not None:
        if isinstance(verification_notes, list):
            _ensure(all(isinstance(note, str) for note in verification_notes), path=path, message=f"{prefix}.verification_notes must be a list of strings", issues=issues)
        else:
            issues.append(ValidationIssue(path, f"{prefix}.verification_notes must be a list"))


def validate_claim_file(path: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [ValidationIssue(path, "file does not exist")]  # pragma: no cover - defensive
    except json.JSONDecodeError as exc:
        return [ValidationIssue(path, f"invalid JSON: {exc}")]

    if not isinstance(payload, Mapping):
        return [ValidationIssue(path, "claim report must be a JSON object")]

    summary = payload.get("summary")
    if isinstance(summary, Mapping):
        _validate_summary(summary, path=path, issues=issues)
    else:
        issues.append(ValidationIssue(path, "summary must be an object"))

    records = payload.get("records")
    if isinstance(records, list):
        for idx, record in enumerate(records):
            if isinstance(record, Mapping):
                _validate_record(record, index=idx, path=path, issues=issues)
            else:
                issues.append(ValidationIssue(path, f"records[{idx}] must be an object"))
    else:
        issues.append(ValidationIssue(path, "records must be an array"))

    checklist = payload.get("review_checklist")
    if isinstance(checklist, Iterable):
        _validate_checklist(checklist, path=path, issues=issues)
    else:
        issues.append(ValidationIssue(path, "review_checklist must be an array"))

    if isinstance(summary, Mapping) and isinstance(records, list):
        declared = summary.get("count")
        if isinstance(declared, int):
            _ensure(declared == len(records), path=path, message="summary.count does not match number of records", issues=issues)

    return issues


def _expand_inputs(patterns: Sequence[str]) -> list[Path]:
    resolved: list[Path] = []
    for pattern in patterns:
        matches = [Path(entry) for entry in glob.glob(pattern)]
        if not matches:
            candidate = Path(pattern)
            if candidate.exists():
                matches.append(candidate)
        resolved.extend(matches)
    return sorted({path.resolve() for path in resolved})


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate OP_RETURN claim reports")
    parser.add_argument("paths", nargs="+", help="Claim JSON files or glob patterns")
    args = parser.parse_args(argv)

    files = _expand_inputs(args.paths)
    if not files:
        print("No claim files matched the provided patterns.")
        return 0

    issues: list[ValidationIssue] = []
    for path in files:
        issues.extend(validate_claim_file(path))

    if issues:
        for issue in issues:
            print(issue.format())
        print(f"Validation failed for {len(issues)} issue(s).")
        return 1

    print(f"Validated {len(files)} claim report(s) with no issues detected.")
    return 0


if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main())
