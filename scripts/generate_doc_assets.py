#!/usr/bin/env python3
"""Generate derived documentation assets.

This script builds two outputs under ``docs/generated``:

* ``service_dependency_graph.md`` renders a Mermaid diagram describing
  relationships between the services defined in ``ops`` and ``services``.
* ``api_index.md`` summarises every OpenAPI description stored in ``docs/api``.

The script is intentionally lightweight so it can run inside CI prior to
building the MkDocs site.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

try:
    import yaml
except ModuleNotFoundError as exc:  # pragma: no cover - handled in CI
    raise SystemExit(
        "PyYAML is required to generate documentation assets. Install it with "
        "`pip install pyyaml`."
    ) from exc

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPO_ROOT / "docs"
GENERATED_ROOT = DOCS_ROOT / "generated"

SERVICE_FILE_GLOBS = (
    "ops/**/*.yml",
    "ops/**/*.yaml",
    "services/**/*.yml",
    "services/**/*.yaml",
)

IGNORED_SERVICE_FILENAMES = {"__init__.py"}


def _iter_yaml_documents(path: Path) -> Iterable[dict]:
    """Yield YAML documents from *path* and ignore parsing failures."""

    try:
        with path.open("r", encoding="utf-8") as handle:
            for document in yaml.safe_load_all(handle):
                if isinstance(document, dict):
                    yield document
    except yaml.YAMLError:
        return


def _discover_service_definitions() -> Dict[str, Path]:
    """Return a mapping of service names to their defining file/directory."""

    services: Dict[str, Path] = {}

    for pattern in SERVICE_FILE_GLOBS:
        for path in REPO_ROOT.glob(pattern):
            for doc in _iter_yaml_documents(path):
                name = doc.get("metadata", {}).get("name")
                if not name:
                    continue
                services[name] = path

    services_root = REPO_ROOT / "services"
    if services_root.exists():
        for service_dir in services_root.iterdir():
            if service_dir.is_dir():
                services.setdefault(service_dir.name.replace("_", "-"), service_dir)

    return services


def _walk_values(node: object) -> Iterable[str]:
    """Yield all string values nested within *node*."""

    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from _walk_values(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_values(item)


def _extract_edges(services: Dict[str, Path]) -> Set[Tuple[str, str]]:
    """Infer dependency edges by scanning for explicit name references."""

    edges: Set[Tuple[str, str]] = set()
    compiled_patterns: Dict[str, re.Pattern[str]] = {
        name: re.compile(rf"\b{re.escape(name)}\b") for name in services
    }

    for name, path in services.items():
        if path.is_file():
            for doc in _iter_yaml_documents(path):
                for value in _walk_values(doc.get("spec", doc)):
                    if not isinstance(value, str):
                        continue
                    for target, pattern in compiled_patterns.items():
                        if target == name:
                            continue
                        if pattern.search(value):
                            edges.add((name, target))
        else:
            # Scan selected file types within the directory for references.
            for candidate in path.rglob("*"):
                if not candidate.is_file() or candidate.name in IGNORED_SERVICE_FILENAMES:
                    continue
                if candidate.suffix not in {".py", ".md", ".yml", ".yaml", ".json", ".txt"}:
                    continue
                try:
                    content = candidate.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                for target, pattern in compiled_patterns.items():
                    if target == name:
                        continue
                    if pattern.search(content):
                        edges.add((name, target))
    return edges


def _render_mermaid(services: Dict[str, Path], edges: Set[Tuple[str, str]]) -> str:
    lines = ["```mermaid", "graph TD"]
    if not edges:
        for name in sorted(services):
            lines.append(f"  {name.replace('-', '_')}[{name}]")
    else:
        for source, target in sorted(edges):
            src_id = source.replace("-", "_")
            tgt_id = target.replace("-", "_")
            lines.append(f"  {src_id}[{source}] --> {tgt_id}[{target}]")
        # Ensure isolated services still appear
        connected = {s for edge in edges for s in edge}
        for name in sorted(set(services) - connected):
            lines.append(f"  {name.replace('-', '_')}[{name}]")
    lines.append("```")
    return "\n".join(lines)


def write_service_graph(output_path: Path) -> None:
    services = _discover_service_definitions()
    edges = _extract_edges(services)
    mermaid = _render_mermaid(services, edges)

    output = "\n".join(
        [
            "# Service Dependency Graph",
            "",
            "The diagram below is automatically generated from the declarative",
            "service specifications in the repository. Dependencies are inferred",
            "by searching for explicit references between services.",
            "",
            mermaid,
            "",
            "_Generated by `scripts/generate_doc_assets.py`._",
            "",
        ]
    )

    output_path.write_text(output, encoding="utf-8")


def write_api_index(output_path: Path) -> None:
    api_dir = DOCS_ROOT / "api"
    sections: List[str] = ["# API Index", ""]

    if not api_dir.exists():
        sections.append("No OpenAPI descriptions were found in `docs/api`.")
        output_path.write_text("\n".join(sections), encoding="utf-8")
        return

    json_files = sorted(api_dir.glob("*.json"))
    if not json_files:
        sections.append("No OpenAPI descriptions were found in `docs/api`.")
        output_path.write_text("\n".join(sections), encoding="utf-8")
        return

    for json_path in json_files:
        with json_path.open("r", encoding="utf-8") as handle:
            try:
                spec = json.load(handle)
            except json.JSONDecodeError:
                continue
        title = spec.get("info", {}).get("title") or json_path.stem.replace("_", " ")
        sections.append(f"## {title}")
        sections.append("")
        sections.append(f"Source: `{json_path.relative_to(REPO_ROOT)}`")
        sections.append("")
        sections.append("| Method | Path | Summary |")
        sections.append("| --- | --- | --- |")

        paths = spec.get("paths", {})
        for route in sorted(paths):
            methods: Dict[str, dict] = paths[route] or {}
            for method, details in sorted(methods.items()):
                summary = (details or {}).get("summary") or ""
                summary = summary.replace("|", "\|")
                sections.append(f"| {method.upper()} | `{route}` | {summary} |")
        sections.append("")

    sections.append("_Generated by `scripts/generate_doc_assets.py`._")
    sections.append("")

    output_path.write_text("\n".join(sections), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    GENERATED_ROOT.mkdir(parents=True, exist_ok=True)
    write_service_graph(GENERATED_ROOT / "service_dependency_graph.md")
    write_api_index(GENERATED_ROOT / "api_index.md")


if __name__ == "__main__":
    main()
