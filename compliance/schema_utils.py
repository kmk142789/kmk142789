from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .parser.models import Artifact, ArtifactType


class SchemaValidationError(Exception):
    """Raised when a document fails schema validation."""


class SimpleSchemaValidator:
    """A tiny subset JSON Schema validator used for deterministic checks."""

    def __init__(self, schema: Dict[str, Any]):
        self.schema = schema

    def validate(self, data: Dict[str, Any], path: str = "") -> List[str]:
        errors: List[str] = []
        if self.schema.get("type") == "object":
            errors.extend(self._validate_object(self.schema, data, path))
        elif self.schema.get("type") == "array":
            if not isinstance(data, list):
                errors.append(f"{path or 'document'} must be an array")
            else:
                item_schema = self.schema.get("items", {})
                for index, item in enumerate(data):
                    validator = SimpleSchemaValidator(item_schema)
                    errors.extend(validator.validate(item, f"{path}[{index}]") )
        return errors

    def _validate_object(self, schema: Dict[str, Any], data: Dict[str, Any], path: str) -> List[str]:
        errors: List[str] = []
        if not isinstance(data, dict):
            errors.append(f"{path or 'document'} must be an object")
            return errors
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                errors.append(f"{path or 'document'} missing required field '{field}'")
        properties = schema.get("properties", {})
        for key, value in data.items():
            if key not in properties:
                continue
            sub_schema = properties[key]
            if sub_schema.get("type") == "object":
                validator = SimpleSchemaValidator(sub_schema)
                errors.extend(validator._validate_object(sub_schema, value, f"{path}.{key}" if path else key))
            elif sub_schema.get("type") == "array":
                if not isinstance(value, list):
                    errors.append(f"{path}.{key} must be an array" if path else f"{key} must be an array")
                    continue
                item_schema = sub_schema.get("items", {})
                for index, item in enumerate(value):
                    validator = SimpleSchemaValidator(item_schema)
                    errors.extend(validator.validate(item, f"{path}.{key}[{index}]" if path else f"{key}[{index}]"))
            elif sub_schema.get("type") == "string":
                if not isinstance(value, str):
                    errors.append(f"{path}.{key} must be a string" if path else f"{key} must be a string")
            elif sub_schema.get("type") == "integer":
                if not isinstance(value, int):
                    errors.append(f"{path}.{key} must be an integer" if path else f"{key} must be an integer")
            if "const" in sub_schema and value != sub_schema["const"]:
                errors.append(
                    f"{path}.{key} must equal {sub_schema['const']}"
                    if path
                    else f"{key} must equal {sub_schema['const']}"
                )
        return errors


def load_schema(name: str) -> Dict[str, Any]:
    schema_path = Path(__file__).parent / "schema" / name
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_artifact(artifact: Artifact) -> List[str]:
    schema_map = {
        ArtifactType.CHARTER: "charter.json",
        ArtifactType.TRUST: "trust.json",
        ArtifactType.DAO_OA: "dao_oa.json",
    }
    schema_name = schema_map.get(artifact.artifact_type)
    if not schema_name:
        return []
    schema = load_schema(schema_name)
    validator = SimpleSchemaValidator(schema)
    return validator.validate(artifact.to_dict())


def validate_crosslinks(crosslinks: List[Dict[str, Any]]) -> List[str]:
    schema = load_schema("crosslinks.json")
    validator = SimpleSchemaValidator(schema)
    return validator.validate(crosslinks)
