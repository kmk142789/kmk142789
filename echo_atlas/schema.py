"""JSON schema helpers for Echo Atlas."""

from __future__ import annotations

import json
from importlib import resources
from typing import Any, Dict

from jsonschema import Draft202012Validator, ValidationError


_SCHEMA_CACHE: Dict[str, Draft202012Validator] = {}


def load_schema() -> Dict[str, Any]:
    with resources.files("schemas").joinpath("atlas.schema.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_validator() -> Draft202012Validator:
    key = "atlas"
    if key not in _SCHEMA_CACHE:
        schema = load_schema()
        _SCHEMA_CACHE[key] = Draft202012Validator(schema)
    return _SCHEMA_CACHE[key]


def validate_atlas(data: Dict[str, Any]) -> None:
    """Validate atlas payload or raise ``ValidationError``."""

    validator = get_validator()
    validator.validate(data)


__all__ = ["validate_atlas", "get_validator", "ValidationError"]
