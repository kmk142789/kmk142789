"""JSON schema helpers for Pulse Weaver."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

class ValidationError(ValueError):
    """Raised when the snapshot payload is malformed."""


SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "pulse_weaver.schema.json"


@lru_cache(maxsize=1)
def _load_schema() -> Dict[str, Any]:
    with SCHEMA_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_validator() -> "PulseWeaverValidator":
    return PulseWeaverValidator()


class PulseWeaverValidator:
    def validate(self, payload: Dict[str, Any]) -> None:
        validate_snapshot(payload)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _validate_summary(summary: Dict[str, Any]) -> None:
    _require(isinstance(summary, dict), "summary must be an object")
    for field in ("total", "by_status", "atlas_links", "phantom_threads"):
        _require(field in summary, f"summary missing '{field}'")
    _require(isinstance(summary["total"], int) and summary["total"] >= 0, "total must be a non-negative integer")
    for map_field in ("by_status", "atlas_links", "phantom_threads"):
        mapping = summary[map_field]
        _require(isinstance(mapping, dict), f"{map_field} must be an object")
        for value in mapping.values():
            _require(isinstance(value, int) and value >= 0, f"{map_field} counts must be non-negative integers")


def _validate_ledger(entries: list[Any]) -> None:
    _require(isinstance(entries, list), "ledger must be a list")
    for entry in entries:
        _require(isinstance(entry, dict), "ledger entries must be objects")
        for field in ("key", "status", "message", "cycle", "created_at"):
            _require(field in entry, f"ledger entry missing '{field}'")


def _validate_links(entries: list[Any]) -> None:
    _require(isinstance(entries, list), "links must be a list")
    for entry in entries:
        _require(isinstance(entry, dict), "link entries must be objects")
        for field in ("key", "created_at"):
            _require(field in entry, f"link entry missing '{field}'")


def _validate_phantom(entries: list[Any]) -> None:
    _require(isinstance(entries, list), "phantom must be a list")
    for entry in entries:
        _require(isinstance(entry, dict), "phantom entries must be objects")
        for field in ("timestamp", "message", "hash"):
            _require(field in entry, f"phantom entry missing '{field}'")


def _validate_glyph_cycle(entry: Dict[str, Any]) -> None:
    _require(isinstance(entry, dict), "glyph_cycle must be an object")
    for field in ("glyph", "title", "mantra", "cycle", "energy", "window"):
        _require(field in entry, f"glyph_cycle missing '{field}'")
    _require(isinstance(entry["energy"], (int, float)), "glyph_cycle energy must be numeric")
    window = entry["window"]
    _require(isinstance(window, dict), "glyph_cycle window must be an object")
    for field in ("start", "end"):
        _require(field in window, f"glyph_cycle window missing '{field}'")


def validate_snapshot(payload: Dict[str, Any]) -> None:
    _require(isinstance(payload, dict), "payload must be an object")
    for field in ("schema", "summary", "ledger", "links", "phantom", "rhyme"):
        _require(field in payload, f"missing required field '{field}'")
    _require(payload["schema"] == "pulse.weaver/snapshot-v1", "schema must be 'pulse.weaver/snapshot-v1'")
    _validate_summary(payload["summary"])
    _validate_ledger(payload["ledger"])
    _validate_links(payload["links"])
    _validate_phantom(payload["phantom"])
    _require(isinstance(payload["rhyme"], str), "rhyme must be a string")
    if "glyph_cycle" in payload:
        _validate_glyph_cycle(payload["glyph_cycle"])


__all__ = ["get_validator", "validate_snapshot", "ValidationError"]
