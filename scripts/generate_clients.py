#!/usr/bin/env python3
"""Generate API clients for the Echo Computer Agent from the OpenAPI spec."""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPEC_PATH = REPO_ROOT / "docs" / "api" / "echo_computer_agent.openapi.json"


@dataclass
class SchemaRef:
    """Wrapper for component schemas used during generation."""

    name: str
    schema: Mapping[str, Any]


@dataclass
class Operation:
    """Description of an HTTP operation extracted from the OpenAPI document."""

    operation_id: str
    method: str
    path: str
    request_schema: SchemaRef | None
    response_schema: SchemaRef | None


class OpenAPISpec:
    """Utility wrapper around the OpenAPI document."""

    def __init__(self, raw: Mapping[str, Any]) -> None:
        self.raw = raw
        components = raw.get("components", {})
        self.schemas: Dict[str, Mapping[str, Any]] = components.get("schemas", {})  # type: ignore[assignment]

    def resolve_schema(self, schema: Mapping[str, Any]) -> SchemaRef:
        ref = schema.get("$ref")
        if not ref:
            raise ValueError("Expected $ref for schema resolution")
        name = ref.rsplit("/", 1)[-1]
        resolved = self.schemas.get(name)
        if resolved is None:
            raise KeyError(f"Schema {name!r} not found in components")
        return SchemaRef(name=name, schema=resolved)

    def iter_operations(self) -> Iterable[Operation]:
        for path, methods in self.raw.get("paths", {}).items():
            for method, details in methods.items():
                operation_id = details.get("operationId")
                if not operation_id:
                    raise ValueError(f"operationId missing for {method.upper()} {path}")
                request_schema: SchemaRef | None = None
                request_body = details.get("requestBody")
                if request_body:
                    content = request_body.get("content", {}).get("application/json")
                    if content and "schema" in content:
                        request_schema = self.resolve_schema(content["schema"])
                response_schema: SchemaRef | None = None
                responses = details.get("responses", {})
                success = responses.get("200") or responses.get("201")
                if success:
                    content = success.get("content", {}).get("application/json")
                    if content and "schema" in content:
                        response_schema = self.resolve_schema(content["schema"])
                yield Operation(
                    operation_id=operation_id,
                    method=method.upper(),
                    path=path,
                    request_schema=request_schema,
                    response_schema=response_schema,
                )


# ---------------------------------------------------------------------------
# Helper utilities


def to_snake(value: str) -> str:
    result = []
    for index, char in enumerate(value):
        if char.isupper() and index > 0 and (not value[index - 1].isupper()):
            result.append("_")
        result.append(char.lower())
    return "".join(result)


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


def to_pascal(value: str) -> str:
    return "".join(part.capitalize() for part in value.split("_"))


def python_type_for(schema: Mapping[str, Any]) -> str:
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    schema_type = schema.get("type")
    if schema_type == "string":
        return "str"
    if schema_type == "boolean":
        return "bool"
    if schema_type == "integer":
        return "int"
    if schema_type == "number":
        return "float"
    if schema_type == "array":
        items = schema.get("items", {"type": "object"})
        return f"list[{python_type_for(items)}]"
    return "dict[str, Any]"


def typescript_type_for(schema: Mapping[str, Any]) -> str:
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    schema_type = schema.get("type")
    if schema_type == "string":
        return "string"
    if schema_type == "boolean":
        return "boolean"
    if schema_type in {"integer", "number"}:
        return "number"
    if schema_type == "array":
        items = schema.get("items", {"type": "unknown"})
        return f"{typescript_type_for(items)}[]"
    return "Record<string, unknown>"


def go_type_for(name: str, schema: Mapping[str, Any], optional: bool) -> str:
    if "$ref" in schema:
        base = schema["$ref"].rsplit("/", 1)[-1]
        go_name = to_pascal(to_snake(base))
    else:
        schema_type = schema.get("type")
        if schema_type == "string":
            go_name = "string"
        elif schema_type == "boolean":
            go_name = "bool"
        elif schema_type == "integer":
            go_name = "int"
        elif schema_type == "number":
            go_name = "float64"
        elif schema_type == "array":
            items = schema.get("items", {"type": "any"})
            go_name = f"[]{go_type_for(name, items, False)}"
        else:
            go_name = "map[string]any"
    if optional and not go_name.startswith("[]") and not go_name.startswith("map["):
        return f"*{go_name}"
    return go_name


# ---------------------------------------------------------------------------
# Python client generation


def generate_python_client(spec: OpenAPISpec, output_dir: Path, operations: Iterable[Operation]) -> None:
    package_name = "echo_computer_agent_client"
    package_dir = output_dir / package_name
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True)

    # pyproject metadata
    pyproject = f"""[build-system]\nrequires = [\"setuptools>=64\", \"wheel\"]\nbuild-backend = \"setuptools.build_meta\"\n\n[project]\nname = \"echo-computer-agent-client\"\nversion = \"{spec.raw['info']['version']}\"\ndescription = \"{spec.raw['info'].get('description', '').strip()}\"\nrequires-python = \">=3.10\"\ndependencies = [\"requests>=2.31.0\"]\n"""
    (output_dir / "pyproject.toml").write_text(pyproject, encoding="utf-8")

    readme = """# Echo Computer Agent Python Client\n\nThis package provides a minimal HTTP client for the Echo Computer Agent API.\nRegenerate it with `python scripts/generate_clients.py`.\n"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")

    types_lines = [
        "from __future__ import annotations",
        "",
        "from typing import Any, TypedDict",
        "",
    ]
    for name, schema in spec.schemas.items():
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        doc = schema.get("description", "")
        if doc:
            types_lines.append(f"class {name}Doc:\n    \"\"\"{doc}\"\"\"")
            types_lines.append("")
        required_props = {k: v for k, v in properties.items() if k in required}
        optional_props = {k: v for k, v in properties.items() if k not in required}

        types_lines.append(f"class {name}Required(TypedDict):")
        if required_props:
            for prop, definition in required_props.items():
                types_lines.append(f"    {prop}: {python_type_for(definition)}")
        else:
            types_lines.append("    pass")
        types_lines.append("")
        types_lines.append(f"class {name}Optional(TypedDict, total=False):")
        if optional_props:
            for prop, definition in optional_props.items():
                types_lines.append(f"    {prop}: {python_type_for(definition)}")
        else:
            types_lines.append("    pass")
        types_lines.append("")
        types_lines.append(f"class {name}({name}Required, {name}Optional):")
        types_lines.append("    \"\"\"Typed mapping generated from the OpenAPI schema.\"\"\"")
        types_lines.append("    pass")
        types_lines.append("")

    (package_dir / "types.py").write_text("\n".join(types_lines).rstrip() + "\n", encoding="utf-8")

    client_py = '''from __future__ import annotations

from typing import Any, Mapping, MutableMapping

import requests

from .types import ChatRequest, ChatResponse, FunctionListResponse


class EchoComputerAgentClient:
    """Requests-based client for the Echo Computer Agent API."""

    def __init__(
        self,
        base_url: str,
        *,
        session: requests.Session | None = None,
        default_headers: Mapping[str, str] | None = None,
    ) -> None:
        self._base_url = base_url.rstrip('/')
        self._session = session or requests.Session()
        self._headers: MutableMapping[str, str] = dict(default_headers or {})

    def close(self) -> None:
        """Close the underlying HTTP session."""

        self._session.close()

    def list_functions(self, *, timeout: float | None = None) -> FunctionListResponse:
        """Return the available function specifications."""

        response = self._session.get(
            f"{self._base_url}/functions",
            headers=dict(self._headers),
            timeout=timeout,
        )
        response.raise_for_status()
        payload: FunctionListResponse = response.json()  # type: ignore[assignment]
        return payload

    def chat(
        self,
        message: str,
        *,
        inputs: Mapping[str, Any] | None = None,
        execute: bool | None = None,
        timeout: float | None = None,
    ) -> ChatResponse:
        """Send a chat request to the agent and return the structured response."""

        payload: ChatRequest = {"message": message}
        if inputs is not None:
            payload["inputs"] = dict(inputs)
        if execute is not None:
            payload["execute"] = execute
        headers = {"Content-Type": "application/json", **self._headers}
        response = self._session.post(
            f"{self._base_url}/chat",
            json=payload,
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()
        chat_response: ChatResponse = response.json()  # type: ignore[assignment]
        return chat_response
'''
    (package_dir / "client.py").write_text(client_py, encoding="utf-8")

    init_lines = [
        "from .client import EchoComputerAgentClient",
        "from .types import ChatRequest, ChatResponse, FunctionDescription, FunctionListResponse",
        "",
        "__all__ = [",
        "    \"EchoComputerAgentClient\",",
        "    \"ChatRequest\",",
        "    \"ChatResponse\",",
        "    \"FunctionDescription\",",
        "    \"FunctionListResponse\",",
        "]",
    ]
    (package_dir / "__init__.py").write_text("\n".join(init_lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# TypeScript client generation


def generate_typescript_client(spec: OpenAPISpec, output_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    (output_dir / "src").mkdir(parents=True)

    package_json = {
        "name": "echo-computer-agent-client",
        "version": spec.raw["info"]["version"],
        "description": spec.raw["info"].get("description", ""),
        "type": "module",
        "scripts": {
            "build": "tsc -p .",
            "lint": "tsc -p . --noEmit"
        },
        "devDependencies": {
            "typescript": "^5.4.0"
        }
    }
    (output_dir / "package.json").write_text(json.dumps(package_json, indent=2) + "\n", encoding="utf-8")

    tsconfig = {
        "compilerOptions": {
            "target": "ES2022",
            "module": "ES2022",
            "moduleResolution": "node",
            "declaration": True,
            "outDir": "dist",
            "strict": True,
            "esModuleInterop": True,
            "skipLibCheck": True,
            "lib": ["es2023", "dom"]
        },
        "include": ["src/**/*"]
    }
    (output_dir / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2) + "\n", encoding="utf-8")

    types_lines = ["// Auto-generated by scripts/generate_clients.py", ""]
    for name, schema in spec.schemas.items():
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        types_lines.append(f"export interface {name} {{")
        for prop, definition in properties.items():
            optional = "?" if prop not in required else ""
            types_lines.append(f"  {prop}{optional}: {typescript_type_for(definition)};")
        types_lines.append("}")
        types_lines.append("")

    class_lines = [
        "export class EchoComputerAgentClient {",
        "  private readonly baseUrl: string;",
        "  private readonly defaultHeaders: Record<string, string>;",
        "",
        "  constructor(baseUrl: string, defaultHeaders: Record<string, string> = {}) {",
        "    this.baseUrl = baseUrl.replace(/\\/+$|\\s+$/g, '').replace(/\\/+$/, '');",
        "    this.defaultHeaders = { ...defaultHeaders };",
        "  }",
        "",
        "  async listFunctions(signal?: AbortSignal): Promise<FunctionListResponse> {",
        "    const response = await fetch(`${this.baseUrl}/functions`, {",
        "      method: 'GET',",
        "      headers: { ...this.defaultHeaders },",
        "      signal,",
        "    });",
        "    if (!response.ok) {",
        "      throw new Error(`Request failed with status ${response.status}`);",
        "    }",
        "    return (await response.json()) as FunctionListResponse;",
        "  }",
        "",
        "  async chat(request: ChatRequest, signal?: AbortSignal): Promise<ChatResponse> {",
        "    const response = await fetch(`${this.baseUrl}/chat`, {",
        "      method: 'POST',",
        "      headers: { 'content-type': 'application/json', ...this.defaultHeaders },",
        "      body: JSON.stringify(request),",
        "      signal,",
        "    });",
        "    if (!response.ok) {",
        "      throw new Error(`Request failed with status ${response.status}`);",
        "    }",
        "    return (await response.json()) as ChatResponse;",
        "  }",
        "}",
    ]
    (output_dir / "src" / "index.ts").write_text("\n".join(types_lines + class_lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Go client generation


def generate_go_client(spec: OpenAPISpec, output_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    (output_dir / "cmd" / "smoke").mkdir(parents=True)

    go_mod = """module echo_computer_agent_client\n\ngo 1.21\n"""
    (output_dir / "go.mod").write_text(go_mod, encoding="utf-8")

    struct_lines = [
        "package echo_computer_agent_client",
        "",
        "import (",
        "    \"bytes\"",
        "    \"context\"",
        "    \"encoding/json\"",
        "    \"fmt\"",
        "    \"net/http\"",
        "    \"strings\"",
        ")",
        "",
    ]

    for name, schema in spec.schemas.items():
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        struct_lines.append(f"type {to_pascal(to_snake(name))} struct {{")
        for prop, definition in properties.items():
            go_field_name = to_pascal(to_snake(prop))
            optional = prop not in required
            go_type = go_type_for(prop, definition, optional)
            tag = f'`json:"{prop}"`'
            if optional:
                tag = f'`json:"{prop},omitempty"`'
            struct_lines.append(f"    {go_field_name} {go_type} {tag}")
        struct_lines.append("}")
        struct_lines.append("")

    client_code = """type Client struct {\n    baseURL string\n    httpClient *http.Client\n    defaultHeaders map[string]string\n}\n\nfunc NewClient(baseURL string, httpClient *http.Client) *Client {\n    trimmed := strings.TrimRight(baseURL, "/")\n    if httpClient == nil {\n        httpClient = http.DefaultClient\n    }\n    return &Client{\n        baseURL: trimmed,\n        httpClient: httpClient,\n        defaultHeaders: map[string]string{},\n    }\n}\n\nfunc (c *Client) SetDefaultHeader(key, value string) {\n    c.defaultHeaders[key] = value\n}\n\nfunc (c *Client) ListFunctions(ctx context.Context) (*FunctionListResponse, error) {\n    req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.baseURL+"/functions", nil)\n    if err != nil {\n        return nil, err\n    }\n    for k, v := range c.defaultHeaders {\n        req.Header.Set(k, v)\n    }\n    resp, err := c.httpClient.Do(req)\n    if err != nil {\n        return nil, err\n    }\n    defer resp.Body.Close()\n    if resp.StatusCode >= 400 {\n        return nil, fmt.Errorf("request failed with status %d", resp.StatusCode)\n    }\n    var payload FunctionListResponse\n    if err := json.NewDecoder(resp.Body).Decode(&payload); err != nil {\n        return nil, err\n    }\n    return &payload, nil\n}\n\nfunc (c *Client) Chat(ctx context.Context, request ChatRequest) (*ChatResponse, error) {\n    body, err := json.Marshal(request)\n    if err != nil {\n        return nil, err\n    }\n    req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+"/chat", bytes.NewReader(body))\n    if err != nil {\n        return nil, err\n    }\n    req.Header.Set("Content-Type", "application/json")\n    for k, v := range c.defaultHeaders {\n        req.Header.Set(k, v)\n    }\n    resp, err := c.httpClient.Do(req)\n    if err != nil {\n        return nil, err\n    }\n    defer resp.Body.Close()\n    if resp.StatusCode >= 400 {\n        return nil, fmt.Errorf("request failed with status %d", resp.StatusCode)\n    }\n    var payload ChatResponse\n    if err := json.NewDecoder(resp.Body).Decode(&payload); err != nil {\n        return nil, err\n    }\n    return &payload, nil\n}\n"""
    struct_lines.append(client_code)
    (output_dir / "client.go").write_text("\n".join(struct_lines).rstrip() + "\n", encoding="utf-8")

    smoke = """package main\n\nimport (\n    \"context\"\n    \"flag\"\n    \"log\"\n    \"time\"\n\n    client \"echo_computer_agent_client\"\n)\n\nfunc main() {\n    baseURL := flag.String(\"base-url\", \"http://127.0.0.1:8000\", \"Echo Computer Agent base URL\")\n    flag.Parse()\n\n    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)\n    defer cancel()\n\n    c := client.NewClient(*baseURL, nil)\n    functions, err := c.ListFunctions(ctx)\n    if err != nil {\n        log.Fatal(err)\n    }\n    if len(functions.Functions) == 0 {\n        log.Fatal(\"no functions returned\")\n    }\n\n    chat, err := c.Chat(ctx, client.ChatRequest{Message: \"launch echo.bank\"})\n    if err != nil {\n        log.Fatal(err)\n    }\n    if chat.Function == \"\" {\n        log.Fatal(\"empty function name\")\n    }\n\n    log.Printf(\"chat response: %s\", chat.Message)\n}\n"""
    (output_dir / "cmd" / "smoke" / "main.go").write_text(smoke, encoding="utf-8")


# ---------------------------------------------------------------------------
# Entry point


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate API clients from the Echo OpenAPI specification")
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC_PATH, help="Path to the OpenAPI specification")
    parser.add_argument("--python-out", type=Path, default=REPO_ROOT / "clients" / "python" / "echo_computer_agent_client", help="Directory for the Python client")
    parser.add_argument("--typescript-out", type=Path, default=REPO_ROOT / "clients" / "typescript" / "echo-computer-agent-client", help="Directory for the TypeScript client")
    parser.add_argument("--go-out", type=Path, default=REPO_ROOT / "clients" / "go" / "echo_computer_agent_client", help="Directory for the Go client")
    args = parser.parse_args()

    spec_data = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    spec = OpenAPISpec(spec_data)
    operations = list(spec.iter_operations())

    generate_python_client(spec, args.python_out, operations)
    generate_typescript_client(spec, args.typescript_out)
    generate_go_client(spec, args.go_out)

    print("Generated Python, TypeScript, and Go clients from", args.spec)


if __name__ == "__main__":
    main()
