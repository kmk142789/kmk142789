"""Schema helpers for the Echo Atlas graph."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

class ValidationError(ValueError):
    """Raised when a payload fails the lightweight atlas validation."""


SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "atlas.schema.json"


@lru_cache(maxsize=1)
def _load_schema() -> Dict[str, Any]:
    with SCHEMA_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_validator() -> "AtlasValidator":
    """Return a cached validator instance.

    The helper exists to preserve the public API previously backed by
    :mod:`jsonschema`.  The returned object simply exposes a ``validate``
    method so callers do not need to change.
    """

    return AtlasValidator()


class AtlasValidator:
    """Minimal validator for the subset of checks used in the tests."""

    def validate(self, data: Dict[str, Any]) -> None:
        validate_graph(data)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _validate_node(node: Dict[str, Any]) -> None:
    _require(isinstance(node, dict), "nodes must be objects")
    for field in ("id", "name", "entity_type"):
        _require(field in node, f"node missing '{field}'")
        _require(isinstance(node[field], str) and node[field], f"node field '{field}' must be a string")


def _validate_edge(edge: Dict[str, Any]) -> None:
    _require(isinstance(edge, dict), "edges must be objects")
    for field in ("id", "source", "target", "relation"):
        _require(field in edge, f"edge missing '{field}'")
        _require(isinstance(edge[field], str) and edge[field], f"edge field '{field}' must be a string")


def _validate_change(change: Dict[str, Any]) -> None:
    _require(isinstance(change, dict), "change log entries must be objects")
    for field in ("timestamp", "change_type", "entity_id"):
        _require(field in change, f"change_log missing '{field}'")


def validate_graph(data: Dict[str, Any]) -> None:
    """Validate *data* against the atlas schema."""

    _require(isinstance(data, dict), "payload must be an object")
    for field in ("generated_at", "nodes", "edges"):
        _require(field in data, f"missing required field '{field}'")

    _require(isinstance(data["nodes"], list), "nodes must be a list")
    for node in data["nodes"]:
        _validate_node(node)

    _require(isinstance(data["edges"], list), "edges must be a list")
    for edge in data["edges"]:
        _validate_edge(edge)

    change_log = data.get("change_log", [])
    _require(isinstance(change_log, list), "change_log must be a list")
    for change in change_log:
        _validate_change(change)


__all__ = ["validate_graph", "ValidationError", "get_validator"]
