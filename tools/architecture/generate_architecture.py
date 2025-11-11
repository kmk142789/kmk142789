#!/usr/bin/env python3
"""Generate architecture metadata and visualisations for core subsystems."""
from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------

IGNORE_DIR_NAMES: Set[str] = {
    "__pycache__",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "build",
    "dist",
    "node_modules",
    "out",
    "venv",
    ".venv",
    "env",
    "tmp",
}

MODULE_SUFFIXES: Dict[str, str] = {
    ".py": "python",
    ".pyi": "python-stub",
    ".js": "javascript",
    ".mjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
}

OPENAPI_SUFFIXES: Set[str] = {".json", ".yaml", ".yml"}
SCHEMA_SUFFIXES: Set[str] = {".json", ".yaml", ".yml", ".avsc", ".sql", ".proto"}

RPC_METHODS = ("get", "post", "put", "delete", "patch", "options", "head", "websocket")
RPC_DECORATOR_PATTERN = re.compile(
    r"@(?P<object>\w+)\.(?P<method>{methods})\(\s*[\"\'](?P<route>[^\"\']+)".format(
        methods="|".join(RPC_METHODS)
    )
)
RPC_CALL_PATTERN = re.compile(
    r"(?P<object>(?:app|router|api|client|blueprint|bp|server|application))\.(?P<method>{methods})\(\s*[\"\'](?P<route>[^\"\']+)".format(
        methods="|".join(RPC_METHODS)
    )
)

# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class RPCRoute:
    method: str
    path: str
    file: str
    line: int
    source: str
    signature: str


@dataclass
class DirectoryMetadata:
    path: str
    missing: bool = False
    modules: List[str] = field(default_factory=list)
    rpc_routes: List[Dict[str, str]] = field(default_factory=list)
    openapi_specs: List[str] = field(default_factory=list)
    schema_files: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, object]:
        return {
            "path": self.path,
            "missing": self.missing,
            "modules": sorted(set(self.modules)),
            "rpc_routes": self.rpc_routes,
            "openapi_specs": sorted(set(self.openapi_specs)),
            "schema_files": sorted(set(self.schema_files)),
        }


class GraphBuilder:
    """Builds a simple node/edge graph representation."""

    def __init__(self) -> None:
        self._nodes: Dict[str, Dict[str, object]] = {}
        self._edges: Dict[Tuple[str, str, str], Dict[str, object]] = {}

    def add_node(
        self,
        node_id: str,
        label: str,
        node_type: str,
        metadata: Optional[Dict[str, object]] = None,
    ) -> str:
        if metadata is None:
            metadata = {}
        if node_id not in self._nodes:
            self._nodes[node_id] = {
                "id": node_id,
                "label": label,
                "type": node_type,
                "metadata": metadata,
            }
        else:
            self._nodes[node_id].setdefault("metadata", {}).update(metadata)
        return node_id

    def add_edge(
        self,
        source: str,
        target: str,
        relationship: str,
        metadata: Optional[Dict[str, object]] = None,
    ) -> None:
        if metadata is None:
            metadata = {}
        self._edges[(source, target, relationship)] = metadata

    def to_serialisable(self) -> Dict[str, object]:
        edges = []
        for (source, target, relationship), metadata in sorted(self._edges.items()):
            edge_payload = {"source": source, "target": target, "type": relationship}
            if metadata:
                edge_payload["metadata"] = metadata
            edges.append(edge_payload)
        return {"nodes": list(self._nodes.values()), "edges": edges}


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def is_hidden(name: str) -> bool:
    return name.startswith('.') and name not in {'.env'}


def safe_read_text(path: Path, max_chars: int = 65536) -> str:
    try:
        with path.open('r', encoding='utf-8') as handle:
            return handle.read(max_chars)
    except UnicodeDecodeError:
        with path.open('r', encoding='latin-1', errors='ignore') as handle:
            return handle.read(max_chars)
    except OSError:
        return ""


def extract_rpc_routes(path: Path, repo_root: Path) -> List[RPCRoute]:
    routes: List[RPCRoute] = []
    if path.suffix.lower() not in {'.py', '.js', '.ts', '.tsx', '.mjs'}:
        return routes
    try:
        with path.open('r', encoding='utf-8') as handle:
            lines = handle.readlines()
    except UnicodeDecodeError:
        with path.open('r', encoding='latin-1', errors='ignore') as handle:
            lines = handle.readlines()
    except OSError:
        return routes

    rel_file = str(path.relative_to(repo_root))
    for lineno, line in enumerate(lines, start=1):
        match = RPC_DECORATOR_PATTERN.search(line)
        if match:
            routes.append(
                RPCRoute(
                    method=match.group('method').upper(),
                    path=match.group('route'),
                    file=rel_file,
                    line=lineno,
                    source='decorator',
                    signature=line.strip(),
                )
            )
            continue
        match = RPC_CALL_PATTERN.search(line)
        if match:
            routes.append(
                RPCRoute(
                    method=match.group('method').upper(),
                    path=match.group('route'),
                    file=rel_file,
                    line=lineno,
                    source=f"call:{match.group('object')}",
                    signature=line.strip(),
                )
            )
    return routes


def detect_openapi_spec(path: Path) -> bool:
    if path.suffix.lower() not in OPENAPI_SUFFIXES:
        return False
    snippet = safe_read_text(path, max_chars=4096).lower()
    return '"openapi"' in snippet or 'openapi:' in snippet


def detect_schema_file(path: Path) -> bool:
    name = path.name.lower()
    if 'schema' in name or 'schemas' in name:
        return True
    if path.suffix.lower() in SCHEMA_SUFFIXES:
        snippet = safe_read_text(path, max_chars=4096).lower()
        if '$schema' in snippet or ('type' in snippet and 'properties' in snippet):
            return True
    return False


def discover_sdk_directories(repo_root: Path, search_roots: Sequence[Path]) -> List[Path]:
    sdk_dirs: Set[Path] = set()
    for base in search_roots:
        if not base.exists() or not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            current = Path(dirpath)
            rel_current = current.relative_to(repo_root)
            if any(part in IGNORE_DIR_NAMES for part in rel_current.parts):
                dirnames[:] = []
                continue
            dirnames[:] = [d for d in dirnames if not is_hidden(d) and d not in IGNORE_DIR_NAMES]
            if 'sdk' in current.name.lower():
                sdk_dirs.add(current)
            if any('sdk' in filename.lower() for filename in filenames):
                sdk_dirs.add(current)
    filtered = [path for path in sdk_dirs if path.exists() and (repo_root in path.parents or path == repo_root)]
    return sorted(filtered)


def gather_directory_metadata(
    repo_root: Path,
    directory: Path,
    graph: GraphBuilder,
    *,
    sdk_only: bool = False,
) -> DirectoryMetadata:
    rel_dir = directory.relative_to(repo_root)
    directory_node_id = f"dir:{rel_dir}"
    metadata = DirectoryMetadata(path=str(rel_dir), missing=not directory.exists())

    graph.add_node(directory_node_id, label=str(rel_dir), node_type='directory', metadata={'exists': directory.exists()})

    if not directory.exists():
        return metadata

    for dirpath, dirnames, filenames in os.walk(directory):
        current = Path(dirpath)
        rel_current = current.relative_to(repo_root)
        if any(part in IGNORE_DIR_NAMES for part in rel_current.parts if part != rel_current.parts[-1]):
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if not is_hidden(d) and d not in IGNORE_DIR_NAMES]

        for filename in filenames:
            file_path = current / filename
            rel_file = file_path.relative_to(repo_root)
            suffix = file_path.suffix.lower()

            if sdk_only and 'sdk' not in str(rel_file).lower():
                continue

            if suffix in MODULE_SUFFIXES:
                language = MODULE_SUFFIXES[suffix]
                metadata.modules.append(str(rel_file))
                module_node_id = f"module:{rel_file}"
                graph.add_node(
                    module_node_id,
                    label=str(rel_file),
                    node_type='module',
                    metadata={'language': language},
                )
                graph.add_edge(directory_node_id, module_node_id, 'contains')

                for route in extract_rpc_routes(file_path, repo_root):
                    route_id = f"rpc:{route.file}:{route.method}:{route.path}"
                    graph.add_node(
                        route_id,
                        label=f"{route.method} {route.path}",
                        node_type='rpc_route',
                        metadata={
                            'file': route.file,
                            'line': route.line,
                            'source': route.source,
                        },
                    )
                    graph.add_edge(module_node_id, route_id, 'defines')
                    metadata.rpc_routes.append({
                        'method': route.method,
                        'path': route.path,
                        'file': route.file,
                        'line': route.line,
                        'source': route.source,
                    })

            if not sdk_only and detect_openapi_spec(file_path):
                metadata.openapi_specs.append(str(rel_file))
                spec_node_id = f"openapi:{rel_file}"
                graph.add_node(spec_node_id, label=str(rel_file), node_type='openapi_spec')
                graph.add_edge(directory_node_id, spec_node_id, 'contains')

            if detect_schema_file(file_path):
                metadata.schema_files.append(str(rel_file))
                schema_node_id = f"schema:{rel_file}"
                graph.add_node(schema_node_id, label=str(rel_file), node_type='schema')
                graph.add_edge(directory_node_id, schema_node_id, 'contains')

    # Deduplicate RPC routes while preserving order
    seen_routes: Set[Tuple[str, str, str]] = set()
    deduped_routes: List[Dict[str, str]] = []
    for route in metadata.rpc_routes:
        key = (route['method'], route['path'], route['file'])
        if key in seen_routes:
            continue
        seen_routes.add(key)
        deduped_routes.append(route)
    metadata.rpc_routes = deduped_routes

    return metadata


# ---------------------------------------------------------------------------
# Visualisation helper
# ---------------------------------------------------------------------------


def render_graphviz_dot(graph_data: Dict[str, object], output_path: Path) -> None:
    """Serialise the graph into a Graphviz DOT document."""

    def quote(value: str) -> str:
        return '"' + value.replace('"', '\\"') + '"'

    shape_map = {
        'directory': 'box3d',
        'module': 'box',
        'rpc_route': 'oval',
        'openapi_spec': 'parallelogram',
        'schema': 'note',
    }

    lines: List[str] = [
        'digraph architecture {',
        '  rankdir=LR;',
        '  node [fontname="Helvetica", fontsize=10];',
        '  edge [fontname="Helvetica", fontsize=9];',
    ]

    for node in sorted(graph_data.get('nodes', []), key=lambda item: item.get('id', '')):
        node_id = str(node.get('id', ''))
        label = str(node.get('label', node_id))
        node_type = str(node.get('type', 'unknown'))
        shape = shape_map.get(node_type, 'ellipse')
        attributes = [f'label={quote(label)}', f'shape={shape}']
        lines.append(f"  {quote(node_id)} [{' '.join(attributes)}];")

    for edge in sorted(
        graph_data.get('edges', []),
        key=lambda item: (item.get('source', ''), item.get('target', ''), item.get('type', '')),
    ):
        source = quote(str(edge.get('source', '')))
        target = quote(str(edge.get('target', '')))
        edge_type = edge.get('type')
        attributes: List[str] = []
        if edge_type:
            attributes.append(f'label={quote(str(edge_type))}')
        if edge.get('metadata'):
            attributes.append('color="#4C78A8"')
        attr_payload = f" [{' '.join(attributes)}]" if attributes else ''
        lines.append(f"  {source} -> {target}{attr_payload};")

    lines.append('}')

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text('\n'.join(lines))


def render_graph_png(graph_data: Dict[str, object], output_path: Path) -> bool:
    try:
        import math
        from io import BytesIO
        from itertools import cycle

        from PIL import Image  # type: ignore

        import matplotlib.pyplot as plt  # type: ignore
        import networkx as nx  # type: ignore
    except ImportError:
        return False

    graph = nx.DiGraph()
    for node in graph_data.get('nodes', []):
        graph.add_node(node['id'], label=node.get('label', node['id']), type=node.get('type'))
    for edge in graph_data.get('edges', []):
        graph.add_edge(edge['source'], edge['target'], type=edge.get('type', 'contains'))

    if not graph.nodes:
        return False

    width = min(max(9, len(graph.nodes) * 0.25), 18)
    height = min(max(5, len(graph.nodes) * 0.18), 14)
    plt.figure(figsize=(width, height))
    pos = nx.spring_layout(graph, seed=42, k=1 / max(1, math.sqrt(len(graph.nodes))))

    color_cycle = cycle(['#4C78A8', '#F58518', '#E45756', '#72B7B2', '#54A24B', '#EECA3B', '#B279A2'])
    type_to_color: Dict[str, str] = {}
    node_colors = []
    for node, data in graph.nodes(data=True):
        node_type = data.get('type', 'unknown')
        if node_type not in type_to_color:
            type_to_color[node_type] = next(color_cycle)
        node_colors.append(type_to_color[node_type])

    nx.draw_networkx_nodes(graph, pos, node_size=600, node_color=node_colors, alpha=0.9)
    nx.draw_networkx_labels(
        graph,
        pos,
        labels={node: data.get('label', node) for node, data in graph.nodes(data=True)},
        font_size=8,
    )
    nx.draw_networkx_edges(graph, pos, arrows=True, arrowstyle='-|>', arrowsize=12, edge_color='#555555')
    edge_labels = {(u, v): data.get('type', '') for u, v, data in graph.edges(data=True)}
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=6)

    plt.axis('off')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    buffer = BytesIO()
    plt.savefig(buffer, dpi=110, format='png')
    plt.close()
    buffer.seek(0)
    image = Image.open(buffer)
    image.save(output_path, optimize=True, compress_level=9)
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate architecture metadata and DAG visualisation.")
    parser.add_argument(
        "--output-json",
        default="system_architecture/architecture.graph.json",
        help="Output path for the JSON graph (relative to repo root).",
    )
    parser.add_argument(
        "--output-dot",
        default="system_architecture/architecture_DAG.dot",
        help="Output path for the Graphviz DOT visualisation (relative to repo root).",
    )
    parser.add_argument(
        "--output-png",
        default=None,
        help="Optional output path for a PNG visualisation (requires matplotlib/networkx).",
    )
    parser.add_argument(
        "--extra-directory",
        action='append',
        default=[],
        help="Additional directories to include (relative to repo root).",
    )
    parser.add_argument(
        "--no-sdk-auto-discovery",
        action='store_true',
        help="Disable automatic discovery of SDK-related directories.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[2]

    base_directories = [
        repo_root / 'atlas',
        repo_root / 'pulse_dashboard',
        repo_root / 'aster_engine',
        repo_root / 'fixtures',
        repo_root / 'logs',
    ]

    sdk_dirs: List[Path] = []
    if not args.no_sdk_auto_discovery:
        sdk_dirs = discover_sdk_directories(
            repo_root,
            search_roots=[
                repo_root / 'packages',
                repo_root / 'echo',
                repo_root / 'services',
                repo_root / 'sdk',
            ],
        )

    extra_dirs = [repo_root / rel for rel in args.extra_directory]

    ordered_directories: List[Path] = []
    seen: Set[Path] = set()
    for directory in base_directories + sdk_dirs + extra_dirs:
        if directory in seen:
            continue
        seen.add(directory)
        ordered_directories.append(directory)

    builder = GraphBuilder()
    directories_report: Dict[str, Dict[str, object]] = {}
    target_paths: List[str] = []
    sdk_dir_set = set(sdk_dirs)

    for directory in ordered_directories:
        metadata = gather_directory_metadata(
            repo_root,
            directory,
            builder,
            sdk_only=directory in sdk_dir_set,
        )
        directories_report[metadata.path] = metadata.as_dict()
        target_paths.append(metadata.path)

    graph_data = builder.to_serialisable()

    output_json_path = (repo_root / args.output_json).resolve()
    output_json_path.parent.mkdir(parents=True, exist_ok=True)

    stats = {
        'directories_scanned': len(directories_report),
        'modules_found': sum(len(data['modules']) for data in directories_report.values()),
        'rpc_routes_found': sum(len(data['rpc_routes']) for data in directories_report.values()),
        'openapi_specs_found': sum(len(data['openapi_specs']) for data in directories_report.values()),
        'schema_files_found': sum(len(data['schema_files']) for data in directories_report.values()),
    }

    payload = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'repo_root': str(repo_root),
        'targets': target_paths,
        'stats': stats,
        'directories': directories_report,
        'graph': graph_data,
    }

    output_json_path.write_text(json.dumps(payload, indent=2))

    output_dot_path = (repo_root / args.output_dot).resolve()
    render_graphviz_dot(graph_data, output_dot_path)

    png_message = ""
    if args.output_png:
        output_png_path = (repo_root / args.output_png).resolve()
        png_created = render_graph_png(graph_data, output_png_path)
        if png_created:
            png_message = f" and PNG visualisation written to {output_png_path}"
        else:
            png_message = " (PNG rendering skipped: requires matplotlib, networkx, and Pillow)"

    print(
        f"[architecture] Graph JSON written to {output_json_path} and Graphviz DOT written to {output_dot_path}{png_message}.",
        flush=True,
    )

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
