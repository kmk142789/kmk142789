"""Auto-maintained manifest system for the Echo repository.

This module implements the ``echo manifest`` CLI described in the
architecture brief.  It discovers engines, states, CLIs, datasets and docs
within the repository, records deterministic metadata for each entry and
persists the canonical manifest JSON at the repository root.

The implementation favours deterministic behaviour to support golden-file
testing and automated verification:

* Discovery routines only inspect files under the provided repository root.
* Content digests are computed with SHA-256.
* Timestamps are derived from ``git log`` so they are stable across checkouts.
* Serialisation uses ``json.dumps`` with ``sort_keys=True`` to ensure
  canonical ordering.

Tests exercise the core helpers using synthetic repositories created under a
temporary directory.  The public helpers accept an optional ``repo_root``
argument so that the tests can operate on those fixtures without touching the
real repository.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Sequence

from .amplify import AmplificationEngine
from .evolver import EchoEvolver
from .tools import forecast as forecast_tools


REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_NAME = "echo_manifest.json"
@dataclass(frozen=True)
class ManifestEntry:
    """Serializable record describing a repository asset."""

    name: str
    path: str
    category: str
    digest: str
    size: int
    version: str
    last_modified: str | None
    owners: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        owners = list(dict.fromkeys(self.owners))
        tags = sorted(dict.fromkeys(self.tags))
        return {
            "name": self.name,
            "path": self.path,
            "category": self.category,
            "digest": self.digest,
            "size": self.size,
            "version": self.version,
            "last_modified": self.last_modified,
            "owners": owners,
            "tags": tags,
        }


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _git_last_modified(repo_root: Path, path: Path) -> str | None:
    try:
        result = subprocess.run(
            [
                "git",
                "log",
                "-1",
                "--format=%cI",
                "--",
                str(path.relative_to(repo_root)),
            ],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, OSError):
        return None
    value = result.stdout.strip()
    return value or None


def _load_codeowners(codeowners_path: Path) -> List[tuple[str, List[str]]]:
    if not codeowners_path.exists():
        return []
    entries: List[tuple[str, List[str]]] = []
    for raw_line in codeowners_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = shlex.split(line)
        if len(parts) < 2:
            continue
        pattern, owners = parts[0], parts[1:]
        entries.append((pattern, owners))
    return entries


def _owners_for_path(path: Path, patterns: Sequence[tuple[str, List[str]]]) -> List[str]:
    if not patterns:
        return []
    relative = path.as_posix()
    matched: List[str] = []
    for pattern, owners in patterns:
        check = pattern.lstrip("/")
        if Path(relative).match(check):
            matched = owners
        elif pattern == "*":
            matched = owners
    return matched


def _python_files(repo_root: Path) -> Iterator[Path]:
    include_prefixes = {
        repo_root / "echo",
        repo_root / "cognitive_harmonics",
        repo_root / "modules",
    }
    for prefix in include_prefixes:
        if not prefix.exists():
            continue
        yield from prefix.rglob("*.py")


def _extract_classes(path: Path) -> List[tuple[str, List[str]]]:
    try:
        module = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    entries: List[tuple[str, List[str]]] = []
    for node in module.body:
        if isinstance(node, ast.ClassDef):
            decorators: List[str] = []
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name):
                    decorators.append(decorator.id)
                elif isinstance(decorator, ast.Attribute):
                    decorators.append(decorator.attr)
            entries.append((node.name, decorators))
    return entries


def _tags_for_path(path: Path, base_tags: Iterable[str]) -> List[str]:
    tags = list(base_tags)
    suffix = path.suffix.lower()
    if suffix:
        tags.append(suffix.lstrip("."))
    if "echo" in path.parts:
        tags.append("echo")
    return tags


def _discover_engines(repo_root: Path, codeowners: Sequence[tuple[str, List[str]]]) -> List[ManifestEntry]:
    entries: List[ManifestEntry] = []
    for file_path in _python_files(repo_root):
        classes = _extract_classes(file_path)
        if not classes:
            continue
        for class_name, _decorators in classes:
            if not class_name.endswith("Engine"):
                continue
            digest = _sha256_file(file_path)
            relative = file_path.relative_to(repo_root)
            stat = file_path.stat()
            entry = ManifestEntry(
                name=class_name,
                path=relative.as_posix(),
                category="engine",
                digest=digest,
                size=stat.st_size,
                version=digest[:12],
                last_modified=_git_last_modified(repo_root, file_path),
                owners=_owners_for_path(relative, codeowners),
                tags=_tags_for_path(relative, ["python", "engine"]),
            )
            entries.append(entry)
    entries.sort(key=lambda item: (item.name, item.path))
    return entries


def _discover_states(repo_root: Path, codeowners: Sequence[tuple[str, List[str]]]) -> List[ManifestEntry]:
    entries: List[ManifestEntry] = []
    for file_path in _python_files(repo_root):
        classes = _extract_classes(file_path)
        if not classes:
            continue
        for class_name, decorators in classes:
            if not class_name.endswith("State") and "dataclass" not in decorators:
                continue
            digest = _sha256_file(file_path)
            relative = file_path.relative_to(repo_root)
            stat = file_path.stat()
            entry = ManifestEntry(
                name=class_name,
                path=relative.as_posix(),
                category="state",
                digest=digest,
                size=stat.st_size,
                version=digest[:12],
                last_modified=_git_last_modified(repo_root, file_path),
                owners=_owners_for_path(relative, codeowners),
                tags=_tags_for_path(relative, ["python", "state"]),
            )
            entries.append(entry)
    entries.sort(key=lambda item: (item.name, item.path))
    return entries


def _load_pyproject(repo_root: Path) -> Mapping[str, Any]:
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.exists():
        return {}
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - Python <3.11 fallback
        import tomli as tomllib  # type: ignore
    try:
        return tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError:
        return {}


def _resolve_module_path(repo_root: Path, module: str) -> Path | None:
    module_path = Path(*module.split("."))
    candidates = [repo_root / (str(module_path) + ".py"), repo_root / module_path / "__init__.py"]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _discover_clis(repo_root: Path, codeowners: Sequence[tuple[str, List[str]]]) -> List[ManifestEntry]:
    config = _load_pyproject(repo_root)
    scripts = (
        config.get("project", {})
        .get("scripts", {})
        if isinstance(config.get("project"), Mapping)
        else {}
    )
    entries: List[ManifestEntry] = []
    for name, target in sorted(scripts.items()):
        if not isinstance(target, str):
            continue
        module = target.split(":", 1)[0]
        file_path = _resolve_module_path(repo_root, module)
        if file_path is None:
            continue
        digest = _sha256_file(file_path)
        relative = file_path.relative_to(repo_root)
        stat = file_path.stat()
        entry = ManifestEntry(
            name=name,
            path=relative.as_posix(),
            category="cli",
            digest=digest,
            size=stat.st_size,
            version=digest[:12],
            last_modified=_git_last_modified(repo_root, file_path),
            owners=_owners_for_path(relative, codeowners),
            tags=_tags_for_path(relative, ["python", "cli"]),
        )
        entries.append(entry)
    entries.sort(key=lambda item: (item.name, item.path))
    return entries


DATASET_DIRECTORIES = (
    "datasets",
    "data",
    "docs/data",
    "federated_pulse",
    "genesis_ledger",
    "ledger",
    "manifest",
)

DATASET_EXTENSIONS = {".json", ".jsonl", ".ndjson", ".csv", ".tsv", ".parquet", ".txt"}


def _discover_datasets(repo_root: Path, codeowners: Sequence[tuple[str, List[str]]]) -> List[ManifestEntry]:
    entries: List[ManifestEntry] = []
    for directory in DATASET_DIRECTORIES:
        base = repo_root / directory
        if not base.exists():
            continue
        for file_path in base.rglob("*"):
            if not file_path.is_file() or file_path.suffix.lower() not in DATASET_EXTENSIONS:
                continue
            digest = _sha256_file(file_path)
            relative = file_path.relative_to(repo_root)
            stat = file_path.stat()
            entry = ManifestEntry(
                name=relative.stem,
                path=relative.as_posix(),
                category="dataset",
                digest=digest,
                size=stat.st_size,
                version=digest[:12],
                last_modified=_git_last_modified(repo_root, file_path),
                owners=_owners_for_path(relative, codeowners),
                tags=_tags_for_path(relative, ["dataset"]),
            )
            entries.append(entry)
    entries.sort(key=lambda item: (item.name, item.path))
    return entries


def _discover_docs(repo_root: Path, codeowners: Sequence[tuple[str, List[str]]]) -> List[ManifestEntry]:
    docs_root = repo_root / "docs"
    entries: List[ManifestEntry] = []
    if not docs_root.exists():
        return entries
    for file_path in docs_root.rglob("*.md"):
        digest = _sha256_file(file_path)
        relative = file_path.relative_to(repo_root)
        stat = file_path.stat()
        entry = ManifestEntry(
            name=relative.stem,
            path=relative.as_posix(),
            category="doc",
            digest=digest,
            size=stat.st_size,
            version=digest[:12],
            last_modified=_git_last_modified(repo_root, file_path),
            owners=_owners_for_path(relative, codeowners),
            tags=_tags_for_path(relative, ["docs"]),
        )
        entries.append(entry)
    entries.sort(key=lambda item: (item.name, item.path))
    return entries


def build_manifest(repo_root: Path | None = None) -> Dict[str, Any]:
    """Collect metadata for the repository and return the manifest payload."""

    root = repo_root or REPO_ROOT
    codeowners = _load_codeowners(root / ".github" / "CODEOWNERS")
    manifest = {
        "schema": "echo.manifest/auto-v1",
        "engines": [entry.to_dict() for entry in _discover_engines(root, codeowners)],
        "states": [entry.to_dict() for entry in _discover_states(root, codeowners)],
        "clis": [entry.to_dict() for entry in _discover_clis(root, codeowners)],
        "datasets": [entry.to_dict() for entry in _discover_datasets(root, codeowners)],
        "docs": [entry.to_dict() for entry in _discover_docs(root, codeowners)],
    }
    return manifest


def _canonical_json(data: Mapping[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def refresh_manifest(
    manifest_path: Path | None = None,
    *,
    repo_root: Path | None = None,
) -> Path:
    root = repo_root or REPO_ROOT
    path = manifest_path or (root / MANIFEST_NAME)
    manifest = build_manifest(repo_root=root)
    text = _canonical_json(manifest)
    if path.exists() and path.read_text(encoding="utf-8") == text:
        print(f"Manifest already up to date at {path}")
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"Manifest written to {path}")
    return path


def _tabulate_category(category: str, entries: Sequence[Mapping[str, Any]]) -> str:
    if not entries:
        return f"## {category}\n(no entries)\n"
    header = f"## {category}\nName                 Path                                      Version     Size\n"
    lines = []
    for entry in entries:
        name = entry["name"]
        path = entry["path"]
        version = entry["version"]
        size = entry["size"]
        lines.append(f"{name:<20} {path:<42} {version:<10} {size:>8}")
    return header + "\n".join(lines) + "\n"


def show_manifest(
    manifest_path: Path | None = None,
    *,
    repo_root: Path | None = None,
) -> Dict[str, Any]:
    root = repo_root or REPO_ROOT
    path = manifest_path or (root / MANIFEST_NAME)
    if path.exists():
        manifest = json.loads(path.read_text(encoding="utf-8"))
    else:
        manifest = build_manifest(repo_root=root)
    for category in ("engines", "states", "clis", "datasets", "docs"):
        section = _tabulate_category(category, manifest.get(category, []))
        print(section.rstrip())
        print()
    print(_canonical_json(manifest), end="")
    return manifest


def verify_manifest(
    manifest_path: Path | None = None,
    *,
    repo_root: Path | None = None,
) -> bool:
    root = repo_root or REPO_ROOT
    path = manifest_path or (root / MANIFEST_NAME)
    if not path.exists():
        print(f"Manifest missing at {path}")
        _append_summary("❌ Manifest verification failed: missing manifest file.")
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Failed to parse manifest {path}: {exc}")
        _append_summary("❌ Manifest verification failed: invalid JSON.")
        return False

    ok = True
    for category in ("engines", "states", "clis", "datasets", "docs"):
        for entry in payload.get(category, []):
            entry_path = root / entry["path"]
            if not entry_path.exists():
                print(f"Missing file for {category} entry: {entry['path']}")
                ok = False
                continue
            digest = _sha256_file(entry_path)
            if digest != entry.get("digest"):
                print(
                    f"Digest mismatch for {entry['path']}: expected {entry.get('digest')}, got {digest}"
                )
                ok = False
                continue
            size = entry_path.stat().st_size
            if size != entry.get("size"):
                print(
                    f"Size mismatch for {entry['path']}: expected {entry.get('size')}, got {size}"
                )
                ok = False
    summary = "✅ Manifest verification passed." if ok else "❌ Manifest verification failed."
    _append_summary(summary)
    if ok:
        print("Manifest verified successfully")
    return ok


def _append_summary(line: str) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    with open(summary_path, "a", encoding="utf-8") as handle:
        handle.write(f"{line}\n")


def _resolve_root(args: argparse.Namespace) -> Path:
    root = getattr(args, "root", None)
    return Path(root).resolve() if root is not None else REPO_ROOT


def _load_amplify_engine(args: argparse.Namespace) -> AmplificationEngine:
    return AmplificationEngine(repo_root=_resolve_root(args))


def _badge_for_index(value: float) -> str:
    if value >= 85:
        return "🔥"
    if value >= 70:
        return "✨"
    if value >= 55:
        return "⚙️"
    return "⚠️"


def _cmd_amplify_now(args: argparse.Namespace) -> int:
    engine = _load_amplify_engine(args)
    snapshot = engine.latest()
    if snapshot is None:
        fallback = EchoEvolver(repo_root=_resolve_root(args))
        total_steps = len(fallback._recommended_sequence())
        snapshot = engine.ensure_snapshot(
            fallback.state,
            cycle_start=None,
            total_steps=total_steps,
            persist=True,
        )

    print(f"Amplify Index: {snapshot.index:.2f}")
    order = [
        "resonance",
        "freshness_half_life",
        "novelty_delta",
        "cohesion",
        "coverage",
        "stability",
        "volatility",
    ]
    for name in order:
        if name not in snapshot.metrics:
            continue
        value = snapshot.metrics[name]
        label = name.replace("_", " ").title()
        print(f"  {label:<20}: {value:.3f}")

    payload = snapshot.to_json()
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    print(f"Digest: {digest}")
    print(payload)

    if getattr(args, "update_manifest", False):
        engine.update_manifest(snapshot, gate=getattr(args, "gate", None))
        print("Manifest amplification section updated.")
    return 0


def _cmd_amplify_log(args: argparse.Namespace) -> int:
    engine = _load_amplify_engine(args)
    history = list(engine.history)
    if not history:
        print("No amplification snapshots recorded yet.")
        return 0

    limit = args.limit
    if limit is not None:
        history = history[-limit:]

    print("Cycle  Index   Δ    Badge  Timestamp")
    print("----- ------ ---- ------ ------------------------")
    previous = None
    for snapshot in history:
        delta = 0.0 if previous is None else snapshot.index - previous.index
        badge = _badge_for_index(snapshot.index)
        print(
            f"{snapshot.cycle:5d} {snapshot.index:6.2f} {delta:+.2f}  {badge:>4}  {snapshot.timestamp}"
        )
        previous = snapshot
    return 0


def _cmd_amplify_gate(args: argparse.Namespace) -> int:
    engine = _load_amplify_engine(args)
    snapshot = engine.latest()
    if snapshot is None:
        print("No amplification snapshot available; run a cycle first.")
        return 1

    threshold = args.minimum
    if threshold is None:
        env_value = os.environ.get("AMPLIFY_MIN")
        threshold = float(env_value) if env_value else 0.0

    print(f"Latest index {snapshot.index:.2f}; required minimum {threshold:.2f}.")
    if snapshot.index >= threshold:
        print("✅ Amplify gate satisfied.")
        return 0

    nudges = engine.generate_nudges(snapshot.metrics)
    if nudges:
        print("Suggested actions:")
        for message in nudges:
            print(f" - {message}")
    print("❌ Amplify gate not met.")
    return 1


def _cmd_forecast(args: argparse.Namespace) -> int:
    engine = _load_amplify_engine(args)
    history = list(engine.history)
    if args.cycles:
        history = history[-args.cycles :]
    indices = [snapshot.index for snapshot in history]
    result = forecast_tools.blend_forecast(indices, horizon=3)
    table = forecast_tools.format_forecast_table(result)
    print(table)
    if args.plot:
        print()
        print(forecast_tools.ascii_sparkline(result.projection))
    return 0

def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="echo", description="Echo manifest utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    manifest_parser = subparsers.add_parser("manifest", help="Manage the Echo manifest")
    manifest_sub = manifest_parser.add_subparsers(dest="subcommand", required=True)

    refresh_parser = manifest_sub.add_parser("refresh", help="Recompute manifest metadata")
    refresh_parser.add_argument("--path", type=Path, help="Optional manifest output path")
    refresh_parser.set_defaults(
        func=lambda args: refresh_manifest(args.path) or 0,
    )

    show_parser = manifest_sub.add_parser("show", help="Display manifest summary and JSON")
    show_parser.add_argument("--path", type=Path, help="Optional manifest path")
    show_parser.set_defaults(func=lambda args: 0 if show_manifest(args.path) else 0)

    verify_parser = manifest_sub.add_parser("verify", help="Validate manifest digests")
    verify_parser.add_argument("--path", type=Path, help="Optional manifest path")
    verify_parser.set_defaults(func=lambda args: 0 if verify_manifest(args.path) else 1)

    amplify_parent = argparse.ArgumentParser(add_help=False)
    amplify_parent.add_argument("--root", type=Path, help="Optional repository root")

    amplify_parser = subparsers.add_parser(
        "amplify", parents=[amplify_parent], help="Amplification engine utilities"
    )
    amplify_sub = amplify_parser.add_subparsers(dest="amplify_command", required=True)

    amplify_now = amplify_sub.add_parser(
        "now", help="Show latest amplification snapshot", parents=[amplify_parent]
    )
    amplify_now.add_argument("--update-manifest", action="store_true", help="Refresh manifest")
    amplify_now.add_argument("--gate", type=float, help="Optional gate target for manifest")
    amplify_now.set_defaults(func=_cmd_amplify_now)

    amplify_log = amplify_sub.add_parser(
        "log", help="Display recent amplification cycles", parents=[amplify_parent]
    )
    amplify_log.add_argument("--limit", type=int, help="Limit number of log entries")
    amplify_log.set_defaults(func=_cmd_amplify_log)

    amplify_gate = amplify_sub.add_parser(
        "gate", help="Verify amplification gate threshold", parents=[amplify_parent]
    )
    amplify_gate.add_argument(
        "--min",
        dest="minimum",
        type=float,
        help="Minimum acceptable amplify index (fallback to AMPLIFY_MIN env)",
    )
    amplify_gate.set_defaults(func=_cmd_amplify_gate)

    forecast_parser = subparsers.add_parser(
        "forecast", parents=[amplify_parent], help="Project amplification trend"
    )
    forecast_parser.add_argument("--cycles", type=int, help="Number of historical cycles to use")
    forecast_parser.add_argument("--plot", action="store_true", help="Render ASCII sparkline")
    forecast_parser.set_defaults(func=_cmd_forecast)

    args = parser.parse_args(list(argv) if argv is not None else None)
    result = getattr(args, "func", None)
    if result is None:
        parser.print_help()
        return 1
    value = result(args)
    return int(value) if isinstance(value, int) else 0


if __name__ == "__main__":  # pragma: no cover - script entry
    raise SystemExit(main())
