"""Generate a drift report between the OpenAPI specification and SDK clients.

This script inspects the Echo Computer Agent OpenAPI document alongside the
client definitions that live in ``clients/`` (and, if present, ``packages/`` and
``sdk_generated/``).  It summarises any schema or route drift in a
human-readable JSON document so that regressions can be spotted without running
the contract tests.
"""

from __future__ import annotations

import ast
import importlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class SchemaInfo:
    """Representation of a schema as defined in the OpenAPI document."""

    required: frozenset[str]
    optional: frozenset[str]
    property_types: Mapping[str, str]


@dataclass(frozen=True)
class ClientSchema:
    """Schema metadata derived from a particular client implementation."""

    required: frozenset[str]
    optional: frozenset[str]
    property_types: Mapping[str, str]


def _find_openapi_specs() -> list[Path]:
    """Return all OpenAPI specifications that can be located in the repository."""

    candidates: list[Path] = []
    search_roots = [
        REPO_ROOT / "schema",
        REPO_ROOT / "schemas",
        REPO_ROOT / "docs" / "api",
    ]
    for root in search_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.suffix.lower() not in {".json", ".yaml", ".yml"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if "\"openapi\"" in text or "openapi:" in text:
                candidates.append(path)
    return sorted(set(candidates))


def _load_openapi_spec(path: Path) -> Mapping[str, Any]:
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    try:
        import yaml  # type: ignore[import-not-found]

        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except ModuleNotFoundError:  # pragma: no cover - defensive branch
        raise RuntimeError(
            f"Unable to parse {path}: YAML support is not available in this environment."
        )


def _resolve_ref_name(ref: str) -> str:
    return ref.split("/")[-1]


def _schema_property_type(schema: Mapping[str, Any]) -> str:
    if "$ref" in schema:
        return _resolve_ref_name(str(schema["$ref"]))

    type_name = schema.get("type")
    if type_name == "array":
        items = schema.get("items")
        if isinstance(items, Mapping):
            inner = _schema_property_type(items)
        else:
            inner = "unknown"
        return f"array[{inner}]"
    if type_name:
        return str(type_name)
    if "anyOf" in schema:
        return "anyOf"
    if "oneOf" in schema:
        return "oneOf"
    if "allOf" in schema:
        return "allOf"
    return "unknown"


def _schemas_from_spec(spec: Mapping[str, Any]) -> Mapping[str, SchemaInfo]:
    components = spec.get("components")
    if not isinstance(components, Mapping):
        return {}
    schemas = components.get("schemas")
    if not isinstance(schemas, Mapping):
        return {}

    result: dict[str, SchemaInfo] = {}
    for name, raw_schema in schemas.items():
        if not isinstance(raw_schema, Mapping):
            continue
        properties = raw_schema.get("properties")
        if not isinstance(properties, Mapping):
            properties = {}
        property_types = {
            str(prop_name): _schema_property_type(prop_schema)
            for prop_name, prop_schema in properties.items()
            if isinstance(prop_schema, Mapping)
        }
        required = raw_schema.get("required")
        required_names = {
            str(item) for item in required if isinstance(item, str)
        } if isinstance(required, Iterable) else set()
        optional_names = set(property_types) - required_names
        result[str(name)] = SchemaInfo(
            required=frozenset(required_names),
            optional=frozenset(optional_names),
            property_types=property_types,
        )
    return result


def _python_type_label(annotation: Any) -> str:
    from collections.abc import MutableMapping
    from typing import Any as TypingAny
    from typing import ForwardRef, get_args, get_origin

    if annotation is TypingAny:
        return "any"
    if isinstance(annotation, str):
        return _normalise_python_annotation(annotation)
    if isinstance(annotation, ForwardRef):
        return _normalise_python_annotation(annotation.__forward_arg__)
    origin = get_origin(annotation)
    if origin in {list, MutableMapping, dict}:
        args = get_args(annotation)
        inner = "unknown"
        if args:
            inner = _python_type_label(args[0])
        if origin in {MutableMapping, dict}:
            return "object"
        return f"array[{inner}]"
    if origin is set:
        args = get_args(annotation)
        inner = _python_type_label(args[0]) if args else "unknown"
        return f"set[{inner}]"
    mapping = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
    }
    if annotation in mapping:
        return mapping[annotation]
    return getattr(annotation, "__name__", str(annotation))


def _normalise_python_annotation(text: str) -> str:
    cleaned = text.strip()
    simple = {
        "str": "string",
        "bool": "boolean",
        "int": "integer",
        "float": "number",
        "Any": "any",
        "None": "null",
    }
    if cleaned in simple:
        return simple[cleaned]
    if cleaned.startswith("dict[") or cleaned.startswith("Mapping["):
        return "object"
    if cleaned.startswith("list["):
        inner = cleaned[len("list[") : -1]
        return f"array[{_normalise_python_annotation(inner)}]"
    if cleaned.startswith("set["):
        inner = cleaned[len("set[") : -1]
        return f"set[{_normalise_python_annotation(inner)}]"
    return cleaned


def _python_client_schemas() -> Mapping[str, ClientSchema]:
    package_root = REPO_ROOT / "clients/python/echo_computer_agent_client"
    if not package_root.exists():
        return {}
    sys.path.insert(0, str(package_root.resolve()))
    types_module = importlib.import_module("echo_computer_agent_client.types")
    result: dict[str, ClientSchema] = {}
    for attr_name in dir(types_module):
        attr = getattr(types_module, attr_name)
        if not getattr(attr, "__annotations__", None):
            continue
        annotations: Mapping[str, Any] = attr.__annotations__
        required = set(getattr(attr, "__required_keys__", ()))
        optional = set(annotations) - required
        property_types = {
            key: _python_type_label(annotation)
            for key, annotation in annotations.items()
        }
        result[attr_name] = ClientSchema(
            required=frozenset(required),
            optional=frozenset(optional),
            property_types=property_types,
        )
    return result


def _typescript_client_schemas() -> Mapping[str, ClientSchema]:
    path = REPO_ROOT / "clients/typescript/echo-computer-agent-client/src/index.ts"
    if not path.exists():
        return {}
    source = path.read_text(encoding="utf-8")

    def parse_interface(interface_name: str) -> ClientSchema | None:
        marker = f"export interface {interface_name}"
        start = source.find(marker)
        if start == -1:
            return None
        brace_index = source.find("{", start)
        depth = 1
        position = brace_index + 1
        body: list[str] = []
        while position < len(source) and depth > 0:
            char = source[position]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    break
            body.append(char)
            position += 1
        required: set[str] = set()
        optional: set[str] = set()
        property_types: dict[str, str] = {}
        for raw_line in "".join(body).splitlines():
            line = raw_line.strip().rstrip(";")
            if not line or line.startswith("//"):
                continue
            if ":" not in line:
                continue
            field_part, type_part = line.split(":", 1)
            field_part = field_part.strip()
            is_optional = field_part.endswith("?")
            field_name = field_part[:-1] if is_optional else field_part
            type_name = type_part.strip()
            if type_name.endswith(";"):
                type_name = type_name[:-1]
            (optional if is_optional else required).add(field_name)
            property_types[field_name] = _typescript_type_label(type_name)
        return ClientSchema(
            required=frozenset(required),
            optional=frozenset(optional),
            property_types=property_types,
        )

    schemas: dict[str, ClientSchema] = {}
    for interface_name in ["ChatRequest", "ChatResponse", "FunctionDescription", "FunctionListResponse"]:
        parsed = parse_interface(interface_name)
        if parsed:
            schemas[interface_name] = parsed
    return schemas


def _typescript_type_label(type_name: str) -> str:
    simplified = type_name.strip()
    replacements = {
        "Record<string, unknown>": "object",
        "Record<string, any>": "object",
        "Record<string, never>": "object",
        "Array<string>": "array[string]",
    }
    if simplified in replacements:
        return replacements[simplified]
    if simplified.endswith("[]"):
        inner = simplified[:-2]
        return f"array[{inner}]"
    if simplified.lower() in {"string", "boolean", "number"}:
        return simplified.lower()
    return simplified


def _go_client_schemas() -> Mapping[str, ClientSchema]:
    path = REPO_ROOT / "clients/go/echo_computer_agent_client/client.go"
    if not path.exists():
        return {}
    source = path.read_text(encoding="utf-8")

    def parse_struct(struct_name: str) -> ClientSchema | None:
        marker = f"type {struct_name} struct"
        start = source.find(marker)
        if start == -1:
            return None
        brace_index = source.find("{", start)
        depth = 1
        position = brace_index + 1
        body: list[str] = []
        while position < len(source) and depth > 0:
            char = source[position]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    break
            body.append(char)
            position += 1
        required: set[str] = set()
        optional: set[str] = set()
        property_types: dict[str, str] = {}
        for raw_line in "".join(body).splitlines():
            line = raw_line.strip()
            if not line or "`" not in line:
                continue
            declaration, _, tag_section = line.partition("`")
            parts = declaration.split()
            if len(parts) < 2:
                continue
            go_field_type = parts[1]
            json_tag = _extract_json_tag(tag_section)
            if not json_tag:
                continue
            field_name, *modifiers = [item.strip() for item in json_tag.split(",")]
            is_optional = "omitempty" in modifiers
            (optional if is_optional else required).add(field_name)
            property_types[field_name] = _go_type_label(go_field_type)
        return ClientSchema(
            required=frozenset(required),
            optional=frozenset(optional),
            property_types=property_types,
        )

    schemas: dict[str, ClientSchema] = {}
    for struct_name in ["ChatRequest", "ChatResponse", "FunctionDescription", "FunctionListResponse"]:
        parsed = parse_struct(struct_name)
        if parsed:
            schemas[struct_name] = parsed
    return schemas


def _extract_json_tag(tag_section: str) -> str | None:
    start = tag_section.find('json:"')
    if start == -1:
        return None
    start += len('json:"')
    end = tag_section.find('"', start)
    if end == -1:
        return None
    return tag_section[start:end]


def _go_type_label(go_type: str) -> str:
    cleaned = go_type.strip()
    if cleaned.startswith("*"):
        cleaned = cleaned[1:]
    mapping = {
        "string": "string",
        "bool": "boolean",
        "int": "integer",
        "float64": "number",
    }
    if cleaned in mapping:
        return mapping[cleaned]
    if cleaned.startswith("map["):
        return "object"
    if cleaned.startswith("[]"):
        return f"array[{cleaned[2:]}]"
    return cleaned


def _python_client_routes() -> set[tuple[str, str]]:
    path = REPO_ROOT / "clients/python/echo_computer_agent_client/echo_computer_agent_client/client.py"
    if not path.exists():
        return set()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    routes: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            method = node.func.attr.lower()
            if method not in {"get", "post", "delete", "put", "patch"}:
                continue
            url_node: ast.AST | None = None
            if node.args:
                url_node = node.args[0]
            else:
                for keyword in node.keywords:
                    if keyword.arg == "url":
                        url_node = keyword.value
                        break
            if not isinstance(url_node, ast.JoinedStr):
                continue
            suffix = _extract_base_url_suffix(url_node)
            if suffix:
                routes.add((method, suffix))
    return routes


def _extract_base_url_suffix(node: ast.JoinedStr) -> str | None:
    parts: list[str] = []
    for value in node.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            parts.append(value.value)
    suffix = "".join(parts).strip()
    if not suffix.startswith("/"):
        return None
    return suffix


def _typescript_client_routes() -> set[tuple[str, str]]:
    path = REPO_ROOT / "clients/typescript/echo-computer-agent-client/src/index.ts"
    if not path.exists():
        return set()
    source = path.read_text(encoding="utf-8")
    routes: set[tuple[str, str]] = set()
    import re

    pattern = re.compile(
        r"fetch\(`\$\{this\.baseUrl\}(?P<path>/[^`]+)`\s*,\s*\{[^}]*method:\s*'(?P<method>[A-Z]+)'",
        re.DOTALL,
    )
    for match in pattern.finditer(source):
        routes.add((match.group("method").lower(), match.group("path")))
    return routes


def _go_client_routes() -> set[tuple[str, str]]:
    path = REPO_ROOT / "clients/go/echo_computer_agent_client/client.go"
    if not path.exists():
        return set()
    source = path.read_text(encoding="utf-8")
    routes: set[tuple[str, str]] = set()
    import re

    pattern = re.compile(
        r"http\.NewRequestWithContext\([^,]+,\s*http\.(Method[A-Za-z]+),\s*c\.baseURL\+\"(?P<path>/[^\"]+)\"",
    )
    method_map = {
        "MethodGet": "get",
        "MethodPost": "post",
        "MethodPut": "put",
        "MethodDelete": "delete",
        "MethodPatch": "patch",
    }
    for match in pattern.finditer(source):
        method = method_map.get(match.group(1))
        if method:
            routes.add((method, match.group("path")))
    return routes


def _compare_schema(expected: SchemaInfo, actual: ClientSchema | None) -> Mapping[str, Any]:
    if actual is None:
        return {"schema_present": False}

    expected_fields = set(expected.property_types.keys())
    actual_fields = set(actual.property_types.keys())
    missing_fields = sorted(expected_fields - actual_fields)
    extra_fields = sorted(actual_fields - expected_fields)
    type_mismatches: list[Mapping[str, str]] = []
    for field in expected_fields & actual_fields:
        spec_type = expected.property_types[field]
        client_type = actual.property_types[field]
        if spec_type != client_type:
            type_mismatches.append(
                {"field": field, "spec_type": spec_type, "client_type": client_type}
            )
    missing_required = sorted(expected.required - actual.required)
    extra_required = sorted(actual.required - expected.required)
    optional_mismatches = sorted(
        (expected.optional - actual.optional)
        | (actual.optional - expected.optional)
    )
    return {
        "schema_present": True,
        "missing_fields": missing_fields,
        "extra_fields": extra_fields,
        "type_mismatches": type_mismatches,
        "missing_required_fields": missing_required,
        "unexpected_optional_differences": optional_mismatches,
    }


def _compare_routes(
    spec: Mapping[str, Any],
    client_routes: set[tuple[str, str]],
) -> Mapping[str, Any]:
    spec_routes: set[tuple[str, str]] = set()
    paths = spec.get("paths")
    if isinstance(paths, Mapping):
        for path_name, operations in paths.items():
            if not isinstance(operations, Mapping):
                continue
            for method_name in operations.keys():
                spec_routes.add((str(method_name).lower(), str(path_name)))
    missing = sorted(spec_routes - client_routes)
    undocumented = sorted(client_routes - spec_routes)
    return {
        "missing_from_client": missing,
        "undocumented_in_client": undocumented,
    }


def _packages_client_note() -> str | None:
    packages_root = REPO_ROOT / "packages"
    if not packages_root.exists():
        return None
    candidate_suffixes = {".ts", ".tsx", ".py", ".go"}
    probes = ("EchoComputerAgent", "/chat", "/functions")
    matches: list[str] = []
    for path in packages_root.rglob("*"):
        if path.suffix.lower() not in candidate_suffixes:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if any(token in text for token in probes):
            matches.append(str(path.relative_to(REPO_ROOT)))
    if matches:
        return (
            "packages/ directory contains potential API references that may need "
            "manual inspection: " + ", ".join(sorted(matches))
        )
    return "packages/ directory scanned; no Echo Computer Agent client references found."


def _sdk_generated_note() -> str | None:
    sdk_dir = REPO_ROOT / "sdk_generated"
    if not sdk_dir.exists():
        return "sdk_generated/ directory is absent; no generated SDKs to audit."
    return None


def main() -> None:
    spec_paths = _find_openapi_specs()
    reports: list[Mapping[str, Any]] = []
    for spec_path in spec_paths:
        spec = _load_openapi_spec(spec_path)
        schemas = _schemas_from_spec(spec)
        python_schemas = _python_client_schemas()
        typescript_schemas = _typescript_client_schemas()
        go_schemas = _go_client_schemas()
        clients = []
        if python_schemas:
            clients.append(
                {
                    "name": "python",
                    "client_sources": [
                        "clients/python/echo_computer_agent_client/echo_computer_agent_client/types.py",
                        "clients/python/echo_computer_agent_client/echo_computer_agent_client/client.py",
                    ],
                    "schema_diffs": {
                        schema: _compare_schema(expected, python_schemas.get(schema))
                        for schema, expected in schemas.items()
                    },
                    "route_diffs": _compare_routes(spec, _python_client_routes()),
                }
            )
        if typescript_schemas:
            clients.append(
                {
                    "name": "typescript",
                    "client_sources": [
                        "clients/typescript/echo-computer-agent-client/src/index.ts",
                    ],
                    "schema_diffs": {
                        schema: _compare_schema(expected, typescript_schemas.get(schema))
                        for schema, expected in schemas.items()
                    },
                    "route_diffs": _compare_routes(spec, _typescript_client_routes()),
                }
            )
        if go_schemas:
            clients.append(
                {
                    "name": "go",
                    "client_sources": [
                        "clients/go/echo_computer_agent_client/client.go",
                    ],
                    "schema_diffs": {
                        schema: _compare_schema(expected, go_schemas.get(schema))
                        for schema, expected in schemas.items()
                    },
                    "route_diffs": _compare_routes(spec, _go_client_routes()),
                }
            )
        reports.append(
            {
                "spec_path": str(spec_path.relative_to(REPO_ROOT)),
                "spec_title": spec.get("info", {}).get("title"),
                "spec_version": spec.get("info", {}).get("version"),
                "client_reports": clients,
            }
        )

    notes = [note for note in (_packages_client_note(), _sdk_generated_note()) if note]

    output = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "spec_reports": reports,
        "notes": notes,
    }
    destination = REPO_ROOT / "system_architecture" / "interface_drift.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

