"""Scan Echo-oriented repositories and emit a constellation graph."""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Sequence

from echo.evolver import EchoEvolver

COMMIT_SPLIT = "\x1f"
PR_PATTERN = re.compile(r"#(\d+)")
ECHO_HEADING_PATTERN = re.compile(r"^#+\s+.*echo.*$", re.IGNORECASE)


@dataclass
class Node:
    id: str
    type: str
    data: dict[str, object] = field(default_factory=dict)


@dataclass
class Edge:
    source: str
    target: str
    rel: str
    data: dict[str, object] = field(default_factory=dict)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--roots",
        nargs="*",
        default=["."],
        help="Repository roots to scan.",
    )
    parser.add_argument(
        "--out",
        default="out/constellation/graph.json",
        help="Destination path for the graph JSON.",
    )
    return parser.parse_args(argv)


def resolve_roots(cli_roots: Sequence[str]) -> list[Path]:
    roots: list[Path] = []
    seen: set[Path] = set()

    env_roots = os.environ.get("ECHO_REPO_ROOTS", "").strip()
    if env_roots:
        for raw in env_roots.split(","):
            candidate = Path(raw).expanduser().resolve()
            if candidate not in seen:
                seen.add(candidate)
                roots.append(candidate)

    for raw in cli_roots:
        candidate = Path(raw).expanduser().resolve()
        if candidate not in seen:
            seen.add(candidate)
            roots.append(candidate)

    return roots


def is_git_repo(root: Path) -> bool:
    try:
        subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        return False
    return True


def get_remote_url(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "remote", "get-url", "origin"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return None
    raw = result.stdout.strip()
    if not raw:
        return None
    if raw.startswith("git@github.com:"):
        suffix = raw[len("git@github.com:") :]
        if suffix.endswith(".git"):
            suffix = suffix[:-4]
        return f"https://github.com/{suffix}"
    if raw.startswith("https://") and raw.endswith(".git"):
        return raw[:-4]
    return raw


def iter_commits(root: Path, max_count: int = 200) -> Iterator[dict[str, object]]:
    if not is_git_repo(root):
        return iter(())

    format_str = "%H" + COMMIT_SPLIT + "%an" + COMMIT_SPLIT + "%ad" + COMMIT_SPLIT + "%s"
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "log",
                f"--max-count={max_count}",
                "--date=iso",
                f"--pretty=format:{format_str}",
                "--name-only",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return iter(())

    lines = result.stdout.splitlines()
    index = 0
    while index < len(lines):
        header = lines[index]
        index += 1
        if not header:
            continue
        parts = header.split(COMMIT_SPLIT)
        if len(parts) != 4:
            continue
        sha, author, timestamp, subject = parts
        files: list[str] = []
        while index < len(lines):
            candidate = lines[index]
            if not candidate.strip():
                index += 1
                continue
            if COMMIT_SPLIT in candidate:
                break
            files.append(candidate.strip())
            index += 1
        while index < len(lines) and not lines[index].strip():
            index += 1

        pr_matches = {f"#{match}" for match in PR_PATTERN.findall(subject)}
        yield {
            "id": sha,
            "author": author,
            "timestamp": timestamp,
            "message": subject,
            "files": files,
            "prs": sorted(pr_matches),
        }


def parse_docs(root: Path) -> Iterator[tuple[str, str]]:
    candidates: list[Path] = []
    readme = root / "README.md"
    if readme.exists():
        candidates.append(readme)
    docs_dir = root / "docs"
    if docs_dir.exists():
        candidates.extend(sorted(docs_dir.rglob("*.md")))

    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        rel = path.relative_to(root)
        for line in text.splitlines():
            if ECHO_HEADING_PATTERN.match(line):
                heading = line.strip().lstrip("# ")
                yield (str(rel), heading)


def parse_modules(root: Path) -> dict[str, set[str]]:
    exports: dict[str, set[str]] = defaultdict(set)
    for path in root.glob("echo_*/*.py"):
        if path.name == "__init__.py":
            continue
        module_id = f"{path.parent.name}.{path.stem}"
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, OSError):
            continue

        explicit_all: set[str] | None = None
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        values: set[str] = set()
                        if isinstance(node.value, (ast.List, ast.Tuple)):
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    values.add(elt.value)
                        explicit_all = values
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = node.name
                if not name.startswith("_"):
                    exports[module_id].add(name)
        if explicit_all is not None:
            exports[module_id] = explicit_all
    return exports


def build_graph(roots: Sequence[Path]) -> dict[str, object]:
    nodes: dict[str, Node] = {}
    edges: list[Edge] = []

    def add_node(node: Node) -> None:
        nodes.setdefault(node.id, node)

    for root in roots:
        if not root.exists():
            continue
        repo_name = root.name
        repo_node_id = f"repo:{repo_name}"
        remote_url = get_remote_url(root) if is_git_repo(root) else None
        repo_data = {"path": str(root)}
        if remote_url:
            repo_data["remote"] = remote_url
        add_node(Node(id=repo_node_id, type="repo", data=repo_data))

        for commit in iter_commits(root):
            commit_id = f"commit:{commit['id']}"
            add_node(
                Node(
                    id=commit_id,
                    type="commit",
                    data={
                        "hash": commit["id"],
                        "author": commit["author"],
                        "timestamp": commit["timestamp"],
                        "message": commit["message"],
                        "files": commit["files"],
                    },
                )
            )
            edges.append(Edge(source=repo_node_id, target=commit_id, rel="contains"))

            for file_path in commit["files"]:
                artifact_id = f"artifact:{file_path}"
                add_node(Node(id=artifact_id, type="artifact", data={"path": file_path}))
                edges.append(Edge(source=commit_id, target=artifact_id, rel="touches"))

            for pr_tag in commit["prs"]:
                pr_id = f"pr:{pr_tag}"
                pr_data: dict[str, object] = {"label": pr_tag, "status": "merged"}
                if remote_url:
                    number = pr_tag.lstrip("#")
                    pr_data["url"] = f"{remote_url}/pull/{number}"
                add_node(Node(id=pr_id, type="pr", data=pr_data))
                edges.append(Edge(source=pr_id, target=commit_id, rel="includes"))
                edges.append(Edge(source=repo_node_id, target=pr_id, rel="tracks"))

        module_exports = parse_modules(root)
        for module_name, names in module_exports.items():
            module_id = f"mod:{module_name}"
            module_path = module_name.replace(".", "/") + ".py"
            add_node(
                Node(
                    id=module_id,
                    type="module",
                    data={"module": module_name, "path": module_path},
                )
            )
            edges.append(Edge(source=repo_node_id, target=module_id, rel="contains"))
            for symbol in sorted(names):
                symbol_id = f"symbol:{module_name}.{symbol}"
                add_node(
                    Node(
                        id=symbol_id,
                        type="symbol",
                        data={"name": symbol, "module": module_name},
                    )
                )
                edges.append(Edge(source=module_id, target=symbol_id, rel="exports"))

        for rel_path, heading in parse_docs(root):
            doc_id = f"artifact:{rel_path}#{heading.lower().replace(' ', '-')}"
            add_node(
                Node(
                    id=doc_id,
                    type="artifact",
                    data={"path": rel_path, "heading": heading},
                )
            )
            edges.append(Edge(source=repo_node_id, target=doc_id, rel="documents"))

    generated_at = datetime.now(timezone.utc).isoformat()
    evolver = EchoEvolver()
    next_step = evolver.next_step_recommendation(persist_artifact=False)

    payload = {
        "nodes": [node.__dict__ for node in nodes.values()],
        "edges": [edge.__dict__ for edge in edges],
        "meta": {
            "generated_at": generated_at,
            "next_step": next_step,
        },
    }
    return payload


def write_graph(graph: dict[str, object], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(graph, handle, indent=2, ensure_ascii=False)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    roots = resolve_roots(args.roots)
    graph = build_graph(roots)
    write_graph(graph, Path(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
