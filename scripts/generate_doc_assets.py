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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Set, Tuple

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


_CAMEL_CASE_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")
_TOKEN_SPLIT_PATTERN = re.compile(r"[\s,;:]+")


@dataclass(slots=True)
class ServiceDefinition:
    """Canonicalised view of a service specification."""

    name: str
    path: Path
    normalized: str
    aliases: Set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.aliases.add(self.normalized)

    def merge_alias(self, alias: str) -> None:
        normalized = _normalize_identifier(alias)
        if normalized:
            self.aliases.add(normalized)


def _normalize_identifier(value: str) -> str:
    """Return a slugified identifier for *value* suitable for comparisons."""

    if not value:
        return ""
    collapsed = value.strip()
    if not collapsed:
        return ""
    collapsed = _CAMEL_CASE_BOUNDARY.sub(" ", collapsed)
    collapsed = collapsed.replace("/", " ").replace(".", " ")
    collapsed = collapsed.replace("_", " ").replace("-", " ")
    collapsed = re.sub(r"[^0-9A-Za-z]+", " ", collapsed)
    parts = [segment for segment in collapsed.lower().split() if segment]
    return "-".join(parts)


def _normalized_candidates(text: str) -> Set[str]:
    """Return the possible canonical identifiers contained within ``text``."""

    candidates: Set[str] = set()
    if not text:
        return candidates

    normalized = _normalize_identifier(text)
    if normalized:
        candidates.add(normalized)

    for fragment in _TOKEN_SPLIT_PATTERN.split(text):
        if not fragment:
            continue
        # Preserve intermediate punctuation (e.g. ``services.foo_bar``) for
        # further splitting to catch nested identifiers.
        tokens = re.split(r"[\\|]+", fragment)
        for token in tokens:
            if not token:
                continue
            normalized_token = _normalize_identifier(token)
            if normalized_token:
                candidates.add(normalized_token)
            for piece in re.split(r"[./]", token):
                normalized_piece = _normalize_identifier(piece)
                if normalized_piece:
                    candidates.add(normalized_piece)
    return candidates


def _iter_yaml_documents(path: Path) -> Iterable[dict]:
    """Yield YAML documents from *path* and ignore parsing failures."""

    try:
        with path.open("r", encoding="utf-8") as handle:
            for document in yaml.safe_load_all(handle):
                if isinstance(document, dict):
                    yield document
    except yaml.YAMLError:
        return


def _discover_service_definitions() -> Dict[str, ServiceDefinition]:
    """Return normalised service definitions keyed by their canonical name."""

    services: Dict[str, ServiceDefinition] = {}

    def register(name: str, path: Path) -> None:
        normalized = _normalize_identifier(name)
        if not normalized:
            return
        definition = services.get(normalized)
        if definition is None:
            services[normalized] = ServiceDefinition(name=name, path=path, normalized=normalized)
        else:
            definition.merge_alias(name)
            if definition.path.is_dir() and path.is_file():
                definition.path = path

    for pattern in SERVICE_FILE_GLOBS:
        for path in REPO_ROOT.glob(pattern):
            for doc in _iter_yaml_documents(path):
                name = doc.get("metadata", {}).get("name")
                if not isinstance(name, str):
                    continue
                register(name, path)

    services_root = REPO_ROOT / "services"
    if services_root.exists():
        for service_dir in services_root.iterdir():
            if service_dir.is_dir():
                display_name = service_dir.name.replace("_", "-")
                register(display_name, service_dir)
                definition = services.get(_normalize_identifier(display_name))
                if definition is not None:
                    definition.merge_alias(service_dir.name)

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


def _extract_edges(services: Mapping[str, ServiceDefinition]) -> Set[Tuple[str, str]]:
    """Infer dependency edges by scanning for explicit name references."""

    edges: Set[Tuple[str, str]] = set()
    alias_map: Dict[str, str] = {}
    for normalized, definition in services.items():
        for alias in definition.aliases:
            alias_map.setdefault(alias, normalized)

    def resolve_targets(text: str, current: str) -> Set[str]:
        matches: Set[str] = set()
        for candidate in _normalized_candidates(text):
            target = alias_map.get(candidate)
            if target and target != current:
                matches.add(target)
        return matches

    for normalized, definition in services.items():
        path = definition.path
        if path.is_file():
            for doc in _iter_yaml_documents(path):
                for value in _walk_values(doc.get("spec", doc)):
                    if not isinstance(value, str):
                        continue
                    edges.update((normalized, target) for target in resolve_targets(value, normalized))
        else:
            for candidate in path.rglob("*"):
                if not candidate.is_file() or candidate.name in IGNORED_SERVICE_FILENAMES:
                    continue
                if candidate.suffix not in {".py", ".md", ".yml", ".yaml", ".json", ".txt"}:
                    continue
                try:
                    content = candidate.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                edges.update((normalized, target) for target in resolve_targets(content, normalized))
    return edges


def _render_mermaid(services: Mapping[str, ServiceDefinition], edges: Set[Tuple[str, str]]) -> str:
    lines = ["```mermaid", "graph TD"]

    def node_id(definition: ServiceDefinition) -> str:
        base = definition.normalized or definition.name
        return base.replace("-", "_")

    if not edges:
        for _normalized, definition in sorted(services.items(), key=lambda item: item[1].name.lower()):
            lines.append(f"  {node_id(definition)}[{definition.name}]")
    else:
        for source, target in sorted(edges):
            source_def = services[source]
            target_def = services[target]
            lines.append(
                f"  {node_id(source_def)}[{source_def.name}] --> {node_id(target_def)}[{target_def.name}]"
            )
        connected = {item for edge in edges for item in edge}
        for normalized, definition in sorted(services.items(), key=lambda item: item[1].name.lower()):
            if normalized not in connected:
                lines.append(f"  {node_id(definition)}[{definition.name}]")

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
