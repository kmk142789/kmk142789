"""Continuum Observatory — repository-scale insight generator.

The Echo monorepo blends runtimes, governance artifacts, and mythic research.
Engineers often need a single diagnostic sweep to understand how active each
lane is, where documentation clusters live, or how many TODO markers remain
unresolved.  The :mod:`echo.continuum_observatory` module provides that view.

It scans a root directory, groups files into the canonical "lanes" used inside
``README.md`` and renders summary reports, ASCII heatmaps, and backlog digests.
The module doubles as a CLI so practitioners can run::

    python -m echo.continuum_observatory summary
    python -m echo.continuum_observatory lanes --json
    python -m echo.continuum_observatory todo --limit 15
    python -m echo.continuum_observatory lanes --sort files --descending
    python -m echo.continuum_observatory heatmap --sort files --limit 5

The observatory intentionally avoids heavyweight dependencies: it relies on the
standard library so it can operate in constrained environments such as CI
pipelines or air-gapped audit laptops.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Mapping, MutableMapping, Optional, Sequence, Tuple

DEFAULT_LANE_MAP: Mapping[str, Tuple[str, ...]] = {
    "execution_stack": (
        "packages/core",
        "packages/bridge",
        "packages/cli",
        "packages/sim",
        "fastapi",
        "services",
        "echo_cli",
    ),
    "interfaces_dashboards": (
        "apps",
        "verifier",
        "viewer",
        "visualizer",
        "pulse_dashboard",
        "public",
        "docs/pulse.html",
    ),
    "governance_policy": (
        "ECHO_",
        "Echo_",
        "GOVERNANCE.md",
        "docs",
    ),
    "proofs_attestations": (
        "proofs",
        "attestations",
        "attestation",
        "genesis_ledger",
        "logs",
        "ledger",
        "registry.json",
        "federated_",
    ),
    "data_research": (
        "data",
        "memory",
        "cognitive_harmonics",
        "harmonic_memory",
        "atlas",
        "atlas_os",
        "wildlight",
    ),
    "automation_ops": (
        "scripts",
        "tools",
        "ops",
        "deploy",
        "docker-compose",
        "Makefile",
        "noxfile.py",
        "run.sh",
    ),
    "distribution_mirrors": (
        "artifacts",
        "public",
        "packages/glyphs",
        "echo_map.json",
        "echo_manifest.json",
    ),
}

DEFAULT_IGNORE_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "out",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
}

DOC_EXTENSIONS = {
    ".md",
    ".rst",
    ".txt",
    ".yaml",
    ".yml",
    ".json",
    ".csv",
    ".toml",
    ".ini",
    ".html",
    ".xml",
}

CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".mjs",
    ".c",
    ".cc",
    ".cpp",
    ".rs",
    ".go",
    ".sh",
    ".ps1",
    ".rb",
}

TODO_KEYWORDS = ("TODO", "FIXME", "HACK")


def _build_todo_pattern(keywords: Sequence[str]) -> re.Pattern[str]:
    normalized = tuple(dict.fromkeys(k.upper() for k in keywords))  # preserve order, deduplicate
    escaped = "|".join(re.escape(keyword) for keyword in normalized)
    return re.compile(
        rf"\b(?P<keyword>{escaped})\b(?:[:\s-]+(?P<text>.*))?",
        re.IGNORECASE,
    )


DEFAULT_TODO_PATTERN = _build_todo_pattern(TODO_KEYWORDS)
TODO_SCAN_LIMIT_BYTES = 1_000_000  # avoid loading massive binaries


@dataclass(slots=True)
class LaneStats:
    """Metrics for an individual lane."""

    lane: str
    directories: Tuple[str, ...]
    file_count: int = 0
    total_bytes: int = 0
    doc_count: int = 0
    code_count: int = 0
    newest_mtime: float = 0.0

    def register(self, path: Path) -> None:
        stat = path.stat()
        self.file_count += 1
        self.total_bytes += stat.st_size
        self.newest_mtime = max(self.newest_mtime, stat.st_mtime)
        suffix = path.suffix.lower()
        if suffix in DOC_EXTENSIONS:
            self.doc_count += 1
        elif suffix in CODE_EXTENSIONS:
            self.code_count += 1

    @property
    def freshness_days(self) -> Optional[float]:
        if self.newest_mtime == 0:
            return None
        now = _dt.datetime.now(tz=_dt.timezone.utc).timestamp()
        delta = max(0.0, now - self.newest_mtime)
        return delta / 86_400

    def to_dict(self) -> Dict[str, object]:
        return {
            "lane": self.lane,
            "directories": self.directories,
            "file_count": self.file_count,
            "total_bytes": self.total_bytes,
            "doc_count": self.doc_count,
            "code_count": self.code_count,
            "newest_mtime": self.newest_mtime,
            "freshness_days": self.freshness_days,
        }


@dataclass(slots=True)
class TodoMatch:
    """Single TODO/FIXME/HACK match."""

    path: Path
    line_no: int
    keyword: str
    line: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "path": str(self.path),
            "line_no": self.line_no,
            "keyword": self.keyword,
            "line": self.line,
        }


@dataclass(slots=True)
class ContinuumSnapshot:
    """Aggregate repository metrics."""

    root: Path
    total_files: int
    total_bytes: int
    latest_mtime: float
    lanes: Mapping[str, LaneStats]
    misc: LaneStats

    def to_dict(self) -> Dict[str, object]:
        return {
            "root": str(self.root),
            "total_files": self.total_files,
            "total_bytes": self.total_bytes,
            "latest_mtime": self.latest_mtime,
            "lanes": {lane: stats.to_dict() for lane, stats in self.lanes.items()},
            "misc": self.misc.to_dict(),
        }


class ContinuumObservatory:
    """Scans repository roots and produces Continuum insights."""

    def __init__(
        self,
        root: Path | str,
        lanes: Mapping[str, Sequence[str]] | None = None,
        ignore_dirs: Iterable[str] | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        if not self.root.exists():
            raise FileNotFoundError(f"Root path does not exist: {self.root}")
        lane_map = lanes or DEFAULT_LANE_MAP
        self.lanes = {
            lane: tuple(paths)
            for lane, paths in lane_map.items()
        }
        self.ignore_dirs = {d.strip() for d in (ignore_dirs or DEFAULT_IGNORE_DIRS)}
        self._snapshot: Optional[ContinuumSnapshot] = None

    # ------------------------------------------------------------------
    # Scanning
    # ------------------------------------------------------------------
    def scan(self) -> ContinuumSnapshot:
        if self._snapshot is not None:
            return self._snapshot

        lane_stats: MutableMapping[str, LaneStats] = {
            lane: LaneStats(lane, directories)
            for lane, directories in self.lanes.items()
        }
        misc = LaneStats("misc", ("<unmapped>",))

        total_files = 0
        total_bytes = 0
        latest_mtime = 0.0

        for current_dir, dirnames, filenames in os.walk(self.root, topdown=True):
            dirnames[:] = sorted(
                d
                for d in dirnames
                if d not in self.ignore_dirs and not d.startswith(".")
            )
            for filename in sorted(filenames):
                path = Path(current_dir, filename)
                try:
                    stat = path.stat()
                except OSError:
                    continue
                total_files += 1
                total_bytes += stat.st_size
                latest_mtime = max(latest_mtime, stat.st_mtime)

                lane = self._lane_for_path(path)
                lane_stats.get(lane, misc).register(path)

        self._snapshot = ContinuumSnapshot(
            root=self.root,
            total_files=total_files,
            total_bytes=total_bytes,
            latest_mtime=latest_mtime,
            lanes=dict(lane_stats),
            misc=misc,
        )
        return self._snapshot

    def scan_todos(self, limit: int = 20, keywords: Sequence[str] | None = None) -> List[TodoMatch]:
        matches: List[TodoMatch] = []
        pattern = DEFAULT_TODO_PATTERN if keywords is None else _build_todo_pattern(keywords)
        for path in self._iter_text_candidates():
            try:
                stat = path.stat()
            except OSError:
                continue
            if stat.st_size > TODO_SCAN_LIMIT_BYTES:
                continue
            try:
                with path.open("r", encoding="utf-8", errors="ignore") as handle:
                    for line_no, line in enumerate(handle, start=1):
                        match = pattern.search(line)
                        if match:
                            keyword = match.group("keyword").upper()
                            text = (match.group("text") or "").strip()
                            content = text if text else line.strip()
                            matches.append(
                                TodoMatch(
                                    path=path,
                                    line_no=line_no,
                                    keyword=keyword,
                                    line=content,
                                )
                            )
                            if len(matches) >= limit:
                                return matches
            except OSError:
                continue
        return matches

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _iter_text_candidates(self) -> Iterator[Path]:
        for current_dir, dirnames, filenames in os.walk(self.root, topdown=True):
            dirnames[:] = sorted(
                d
                for d in dirnames
                if d not in self.ignore_dirs and not d.startswith(".")
            )
            for filename in sorted(filenames):
                path = Path(current_dir, filename)
                if path.suffix.lower() in DOC_EXTENSIONS | CODE_EXTENSIONS:
                    yield path

    def _lane_for_path(self, path: Path) -> str:
        relative = path.relative_to(self.root)
        relative_str = str(relative)
        for lane, directories in self.lanes.items():
            for raw_prefix in directories:
                prefix = raw_prefix[:-1] if raw_prefix.endswith("/") else raw_prefix
                if prefix.endswith("_"):
                    stem = prefix
                    if any(part.startswith(stem) for part in relative.parts):
                        return lane
                    continue
                if relative_str.startswith(prefix):
                    return lane
                parts = prefix.split("/")
                if tuple(parts) == relative.parts[: len(parts)]:
                    return lane
        return "misc"


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def build_default_lane_map() -> Mapping[str, Tuple[str, ...]]:
    """Expose the default lane map to other modules/tests."""

    return dict(DEFAULT_LANE_MAP)


def _human_bytes(num_bytes: int) -> str:
    if num_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    index = 0
    value = float(num_bytes)
    while value >= 1024 and index < len(units) - 1:
        value /= 1024
        index += 1
    return f"{value:.1f} {units[index]}"


def _format_timestamp(ts: float) -> str:
    if ts == 0:
        return "n/a"
    return _dt.datetime.fromtimestamp(ts, tz=_dt.timezone.utc).isoformat()


def _render_summary(snapshot: ContinuumSnapshot) -> str:
    lines = [
        f"Continuum Observatory :: {snapshot.root}",
        "=" * 72,
        f"Files     : {snapshot.total_files:,}",
        f"Footprint : {_human_bytes(snapshot.total_bytes)}",
        f"Updated   : {_format_timestamp(snapshot.latest_mtime)}",
        "",
    ]
    if snapshot.total_files:
        doc_total = sum(stats.doc_count for stats in snapshot.lanes.values())
        code_total = sum(stats.code_count for stats in snapshot.lanes.values())
        lines.append(f"Documents : {doc_total:,}")
        lines.append(f"Code      : {code_total:,}")
        lines.append("")
    return "\n".join(lines)


LANE_SORT_FIELDS: Mapping[str, str] = {
    "lane": "Lane name (A→Z)",
    "files": "Total file count",
    "docs": "Documentation file count",
    "code": "Source file count",
    "footprint": "Total bytes recorded",
    "freshness": "Days since last modification",
}


def _sorted_lane_stats(
    snapshot: ContinuumSnapshot,
    *,
    field: str = "lane",
    descending: bool = False,
    limit: Optional[int] = None,
) -> List[LaneStats]:
    """Return the snapshot's lane stats sorted by ``field``."""

    if field not in LANE_SORT_FIELDS:
        raise ValueError(f"Unknown sort field: {field}")

    def key_lane(stats: LaneStats) -> object:
        if field == "lane":
            return stats.lane
        if field == "files":
            return stats.file_count
        if field == "docs":
            return stats.doc_count
        if field == "code":
            return stats.code_count
        if field == "footprint":
            return stats.total_bytes
        if field == "freshness":
            return stats.freshness_days if stats.freshness_days is not None else float("inf")
        return stats.lane  # pragma: no cover - exhaustive

    ordered = list(snapshot.lanes.values())
    ordered.sort(key=key_lane, reverse=descending)
    if limit is not None and limit > 0:
        ordered = ordered[:limit]
    return ordered


def _render_lane_table(
    snapshot: ContinuumSnapshot,
    *,
    sort_field: str = "lane",
    descending: bool = False,
    limit: Optional[int] = None,
) -> str:
    header = f"{'Lane':25} | {'Files':>8} | {'Docs':>6} | {'Code':>6} | {'Footprint':>10} | {'Freshness (days)':>16}"
    sep = "-" * len(header)
    lines = [header, sep]
    ordered = _sorted_lane_stats(snapshot, field=sort_field, descending=descending, limit=limit)
    for stats in ordered:
        freshness = f"{stats.freshness_days:.1f}" if stats.freshness_days is not None else "n/a"
        lines.append(
            f"{stats.lane:25} | {stats.file_count:8} | {stats.doc_count:6} | {stats.code_count:6} | {_human_bytes(stats.total_bytes):>10} | {freshness:>16}"
        )
    lines.append(sep)
    lines.append(
        f"{'misc':25} | {snapshot.misc.file_count:8} | {snapshot.misc.doc_count:6} | {snapshot.misc.code_count:6} | {_human_bytes(snapshot.misc.total_bytes):>10} | {'n/a':>16}"
    )
    if limit is not None and limit > 0 and limit < len(snapshot.lanes):
        lines.append(f"(showing top {limit} lanes sorted by {sort_field}{' desc' if descending else ''})")
    return "\n".join(lines)


def _render_heatmap(
    snapshot: ContinuumSnapshot,
    *,
    sort_field: str = "lane",
    descending: bool = False,
    limit: Optional[int] = None,
) -> str:
    ordered = _sorted_lane_stats(snapshot, field=sort_field, descending=descending, limit=limit)
    max_files = max((stats.file_count for stats in ordered), default=1)
    lines = ["Lane activity heatmap (relative file counts)", ""]
    for stats in ordered:
        scale = 0 if max_files == 0 else int((stats.file_count / max_files) * 20)
        bar = "█" * max(scale, 1)
        lines.append(f"{stats.lane:25} {bar}")
    if limit is not None and limit > 0 and limit < len(snapshot.lanes):
        lines.append("")
        lines.append(f"(showing top {limit} lanes sorted by {sort_field}{' desc' if descending else ''})")
    return "\n".join(lines)


def _render_todos(matches: Sequence[TodoMatch]) -> str:
    if not matches:
        return "No TODO markers found in scanned files."
    lines = ["Outstanding TODO markers", ""]
    for match in matches:
        rel_path = match.path
        lines.append(f"{rel_path} L{match.line_no}: [{match.keyword}] {match.line.strip()}")
    return "\n".join(lines)


def _render_stats_json(snapshot: ContinuumSnapshot) -> str:
    return json.dumps(snapshot.to_dict(), indent=2)


def _render_todos_json(matches: Sequence[TodoMatch]) -> str:
    return json.dumps([match.to_dict() for match in matches], indent=2)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Continuum Observatory CLI")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root to scan")
    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        help="Additional directory names to ignore during scans",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text tables")

    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = False

    subparsers.add_parser("summary", help="Print overall repository metrics")
    lanes_parser = subparsers.add_parser("lanes", help="Render per-lane statistics")
    lanes_parser.add_argument(
        "--sort",
        choices=tuple(LANE_SORT_FIELDS.keys()),
        default="lane",
        help="Sort lane table by the specified metric",
    )
    lanes_parser.add_argument("--descending", action="store_true", help="Sort in descending order")
    lanes_parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Show only the first N lanes after sorting",
    )

    heatmap_parser = subparsers.add_parser("heatmap", help="Render ASCII heatmap for lane activity")
    heatmap_parser.add_argument(
        "--sort",
        choices=tuple(LANE_SORT_FIELDS.keys()),
        default="lane",
        help="Sort heatmap lanes by the specified metric",
    )
    heatmap_parser.add_argument("--descending", action="store_true", help="Sort in descending order")
    heatmap_parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Show only the first N lanes after sorting",
    )
    todo_parser = subparsers.add_parser("todo", help="List outstanding TODO/FIXME markers")
    todo_parser.add_argument("--limit", type=int, default=20, help="Maximum TODO markers to display")
    todo_parser.add_argument(
        "--keyword",
        action="append",
        default=[],
        metavar="WORD",
        help="Additional TODO-like keywords to scan (defaults to TODO/FIXME/HACK)",
    )

    args = parser.parse_args(argv)
    command = args.command or "summary"

    observatory = ContinuumObservatory(root=args.root, ignore_dirs=DEFAULT_IGNORE_DIRS | set(args.ignore))
    snapshot = observatory.scan()

    if command == "summary":
        output = _render_stats_json(snapshot) if args.json else _render_summary(snapshot)
    elif command == "lanes":
        if args.json:
            output = _render_stats_json(snapshot)
        else:
            output = _render_lane_table(
                snapshot,
                sort_field=args.sort,
                descending=args.descending,
                limit=args.limit,
            )
    elif command == "heatmap":
        output = _render_heatmap(
            snapshot,
            sort_field=args.sort,
            descending=args.descending,
            limit=args.limit,
        )
    elif command == "todo":
        keywords = TODO_KEYWORDS + tuple(args.keyword)
        matches = observatory.scan_todos(limit=args.limit, keywords=keywords)
        output = _render_todos_json(matches) if args.json else _render_todos(matches)
    else:
        parser.error(f"Unknown command: {command}")
        return 2

    print(output)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
