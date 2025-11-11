from __future__ import annotations

import importlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
import pytest

SPEC_PATH = Path("docs/api/echo_computer_agent.openapi.json")
PYTHON_CLIENT_ROOT = Path("clients/python/echo_computer_agent_client")
TYPESCRIPT_CLIENT_PATH = Path("clients/typescript/echo-computer-agent-client/src/index.ts")
GO_CLIENT_PATH = Path("clients/go/echo_computer_agent_client/client.go")


@dataclass(frozen=True)
class SchemaShape:
    required: frozenset[str]
    optional: frozenset[str]


@pytest.fixture(scope="session")
def openapi_spec() -> dict[str, object]:
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


def _schema_shape(schema: dict[str, object]) -> SchemaShape:
    properties = schema.get("properties") or {}
    if not isinstance(properties, dict):
        raise TypeError("Schema properties must be a mapping")
    required_fields = schema.get("required") or []
    if not isinstance(required_fields, list):
        raise TypeError("Schema required fields must be a list")
    keys = {str(key) for key in properties.keys()}
    required = frozenset(str(item) for item in required_fields)
    optional = frozenset(keys - set(required))
    return SchemaShape(required=required, optional=optional)


@pytest.fixture(scope="session")
def python_types_module() -> object:
    sys.path.append(str(PYTHON_CLIENT_ROOT.resolve()))
    return importlib.import_module("echo_computer_agent_client.types")


@pytest.fixture(scope="session")
def python_client_module() -> object:
    sys.path.append(str(PYTHON_CLIENT_ROOT.resolve()))
    return importlib.import_module("echo_computer_agent_client.client")


def _python_shape(module: object, name: str) -> SchemaShape:
    typed_dict = getattr(module, name)
    annotations = getattr(typed_dict, "__annotations__")
    required = getattr(typed_dict, "__required_keys__")
    optional_keys = set(annotations) - set(required)
    return SchemaShape(required=frozenset(required), optional=frozenset(optional_keys))


def _typescript_interface_shape(interface_name: str) -> SchemaShape:
    source = TYPESCRIPT_CLIENT_PATH.read_text(encoding="utf-8")
    marker = f"export interface {interface_name}"
    start = source.find(marker)
    if start == -1:
        raise AssertionError(f"Unable to locate TypeScript interface {interface_name}")
    brace_index = source.find("{", start)
    if brace_index == -1:
        raise AssertionError(f"Interface {interface_name} does not contain an opening brace")
    depth = 1
    position = brace_index + 1
    block: list[str] = []
    while position < len(source) and depth > 0:
        char = source[position]
        if char == "{":
            depth += 1
            block.append(char)
        elif char == "}":
            depth -= 1
            if depth == 0:
                position += 1
                break
            block.append(char)
        else:
            block.append(char)
        position += 1
    if depth != 0:
        raise AssertionError(f"Interface {interface_name} does not terminate with a closing brace")
    body = "".join(block)
    required: set[str] = set()
    optional: set[str] = set()
    for line in body.splitlines():
        stripped = line.strip().rstrip(";")
        if not stripped or stripped.startswith("//"):
            continue
        if ":" not in stripped:
            continue
        field, _ = stripped.split(":", 1)
        field = field.strip()
        is_optional = field.endswith("?")
        field_name = field[:-1] if is_optional else field
        (optional if is_optional else required).add(field_name)
    return SchemaShape(required=frozenset(required), optional=frozenset(optional))


def _go_struct_shape(struct_name: str) -> SchemaShape:
    source = GO_CLIENT_PATH.read_text(encoding="utf-8")
    marker = f"type {struct_name} struct"
    start = source.find(marker)
    if start == -1:
        raise AssertionError(f"Unable to locate Go struct {struct_name}")
    brace_index = source.find("{", start)
    if brace_index == -1:
        raise AssertionError(f"Struct {struct_name} does not contain an opening brace")
    depth = 1
    position = brace_index + 1
    block: list[str] = []
    while position < len(source) and depth > 0:
        char = source[position]
        if char == "{":
            depth += 1
            block.append(char)
        elif char == "}":
            depth -= 1
            if depth == 0:
                position += 1
                break
            block.append(char)
        else:
            block.append(char)
        position += 1
    if depth != 0:
        raise AssertionError(f"Struct {struct_name} does not terminate with a closing brace")
    body = "".join(block)
    required: set[str] = set()
    optional: set[str] = set()
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        parts = stripped.split("`", 1)
        if len(parts) != 2:
            continue
        json_tag_match = re.search(r'json:"([^"]+)"', parts[1])
        if not json_tag_match:
            continue
        tag_value = json_tag_match.group(1)
        field_name, *modifiers = tag_value.split(",")
        is_optional = any(modifier.strip() == "omitempty" for modifier in modifiers)
        (optional if is_optional else required).add(field_name)
    return SchemaShape(required=frozenset(required), optional=frozenset(optional))


@pytest.mark.parametrize(
    "schema_name",
    [
        "ChatRequest",
        "ChatResponse",
        "FunctionDescription",
        "FunctionListResponse",
    ],
)
def test_python_client_matches_openapi_schema(
    schema_name: str, openapi_spec: dict[str, object], python_types_module: object
) -> None:
    schema = openapi_spec["components"]["schemas"][schema_name]  # type: ignore[index]
    expected = _schema_shape(schema)
    actual = _python_shape(python_types_module, schema_name)
    assert actual == expected


@pytest.mark.parametrize(
    "schema_name",
    [
        "ChatRequest",
        "ChatResponse",
        "FunctionDescription",
        "FunctionListResponse",
    ],
)
def test_typescript_client_matches_openapi_schema(schema_name: str, openapi_spec: dict[str, object]) -> None:
    schema = openapi_spec["components"]["schemas"][schema_name]  # type: ignore[index]
    expected = _schema_shape(schema)
    actual = _typescript_interface_shape(schema_name)
    assert actual == expected


@pytest.mark.parametrize(
    "struct_name",
    [
        "ChatRequest",
        "ChatResponse",
        "FunctionDescription",
        "FunctionListResponse",
    ],
)
def test_go_client_matches_openapi_schema(struct_name: str, openapi_spec: dict[str, object]) -> None:
    schema = openapi_spec["components"]["schemas"][struct_name]  # type: ignore[index]
    expected = _schema_shape(schema)
    actual = _go_struct_shape(struct_name)
    assert actual == expected


def test_python_client_operations(python_client_module: object) -> None:
    client_cls = getattr(python_client_module, "EchoComputerAgentClient")
    for attr in ("list_functions", "chat"):
        assert hasattr(client_cls, attr), f"Python client missing method {attr}"


def test_typescript_client_operations() -> None:
    source = TYPESCRIPT_CLIENT_PATH.read_text(encoding="utf-8")
    for signature in ("async listFunctions", "async chat"):
        assert signature in source, f"TypeScript client missing method signature {signature}"


def test_go_client_operations() -> None:
    source = GO_CLIENT_PATH.read_text(encoding="utf-8")
    for signature in ("ListFunctions", "Chat"):
        expected = f"func (c *Client) {signature}("
        assert expected in source, f"Go client missing method {signature}"
