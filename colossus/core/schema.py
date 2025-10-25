"""JSON schema helpers for Colossus."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict
import importlib
import json


@dataclass
class SchemaRegistry:
    """Load and cache JSON schema definitions."""

    root: Path

    def load(self, name: str) -> Dict[str, Any]:
        path = self.root / name
        if not path.exists():
            raise FileNotFoundError(f"schema not found: {path}")
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)


class SchemaValidator:
    """Validate JSON documents against their schema definitions."""

    def __init__(self) -> None:
        self._validator = self._load_validator()

    def validate(self, data: Dict[str, Any], schema: Dict[str, Any]) -> None:
        validator = self._validator
        if validator is None:
            raise RuntimeError(
                "jsonschema is required for validation. Install the optional "
                "dependency with `pip install colossus[schemas]`"
            )
        validator(data, schema)

    @staticmethod
    def _load_validator():
        spec = importlib.util.find_spec("jsonschema")
        if spec is None:
            return None
        module = importlib.import_module("jsonschema")
        Draft7Validator = getattr(module, "Draft7Validator")

        def _validate(data: Dict[str, Any], schema: Dict[str, Any]) -> None:
            Draft7Validator(schema).validate(data)

        return _validate


__all__ = ["SchemaRegistry", "SchemaValidator"]
