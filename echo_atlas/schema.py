"""Schema helpers for the Echo Atlas graph."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

from jsonschema import Draft202012Validator, ValidationError


SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "atlas.schema.json"


@lru_cache(maxsize=1)
def _load_schema() -> Dict[str, Any]:
    with SCHEMA_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_validator() -> Draft202012Validator:
    """Return a cached validator instance."""

    schema = _load_schema()
    return Draft202012Validator(schema)


def validate_graph(data: Dict[str, Any]) -> None:
    """Validate *data* against the atlas schema."""

    validator = get_validator()
    validator.validate(data)


__all__ = ["validate_graph", "ValidationError", "get_validator"]
