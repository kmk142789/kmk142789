"""Scan the repository for TODO/FIXME/HACK markers and refresh ``ROADMAP.md``.

The CLI can optionally enforce a maximum number of outstanding TODO/FIXME/HACK
tasks, returning a non-zero exit code to make CI pipelines aware of regressions.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import os
import re
from fnmatch import fnmatch
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Sequence, Set, Tuple
import sys

TASK_PATTERN = re.compile(
    r"^\s*(?:[<*!#/\-]+)?\s*(?P<tag>TODO|FIXME|HACK)(?=(?:[:\s-]|$))(?:[:\s-]+(?P<text>.*))?",
    re.IGNORECASE,
)
BlockCommentPattern = Tuple[re.Pattern[str], Callable[[re.Match[str]], str], str]


BLOCK_COMMENT_PATTERNS: Tuple[BlockCommentPattern, ...] = (
    # pattern, body extractor, leading characters to strip per line
    (
        re.compile(r"/\*.*?\*/", re.DOTALL),
        lambda match: match.group()[2:-2],
        " \t*",
    ),
    (
        re.compile(r"<!--.*?-->", re.DOTALL),
        lambda match: match.group()[4:-3],
        " \t-!*",
    ),
    (
        re.compile(
            r'(?P<prefix>(?:[rubfRUBF]{0,3})?)(?P<quote>"""|\'\'\')(?P<body>.*?)(?P=quote)',
            re.DOTALL,
        ),
        lambda match: match.group("body"),
        " \t",
    ),
)
NO_EXTENSION_LABEL = "<no extension>"

DEFAULT_SKIP_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    "out",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
    ".direnv",
    ".venv",
    "venv",
    "env",
    ".tox",
    ".nox",
}

DEFAULT_HOTSPOT_LIMIT = 5


def _normalize_task_text(text: str) -> str:
    """Return a cleaned representation of comment text."""

    cleaned = text.strip()
    if not cleaned:
        return ""

    first_line = cleaned.splitlines()[0].strip()

    for marker in ("*/", "-->"):
        if first_line.endswith(marker):
            first_line = first_line[: -len(marker)].rstrip()

    return first_line


def _normalise_skip_entries(
    base_path: Path, entries: Optional[Sequence[str]]
) -> tuple[Set[str], List[Tuple[str, ...]]]:
    """Return normalised directory and path filters for skip entries."""

    skip_names = DEFAULT_SKIP_DIRS.copy()
    skip_paths: List[Tuple[str, ...]] = []

    if not entries:
        return skip_names, skip_paths

    for raw in entries:
        if not raw:
            continue
        candidate = raw.strip()
        if not candidate:
            continue

        path_candidate = Path(candidate)
        path_parts: Tuple[str, ...]

        if path_candidate.is_absolute():
            try:
                relative = path_candidate.relative_to(base_path)
            except ValueError:
                # The skip entry points outside the base path. In that case fall back
                # to matching by name so we still honour the intent of the filter.
                tail = path_candidate.name
                path_parts = (tail,) if tail else tuple()
            else:
                path_parts = tuple(part for part in relative.parts if part not in {"", "."})
        else:
            normalised = candidate.replace("\\", "/")
            path_parts = tuple(part for part in normalised.split("/") if part and part != ".")

        if not path_parts:
            continue

        if len(path_parts) == 1:
            skip_names.add(path_parts[0])
        else:
            skip_paths.append(path_parts)

    return skip_names, skip_paths


@dataclass(slots=True)
class Task:
    """Representation of a discovered TODO/FIXME/HACK entry."""

    path: Path
    line: int
    tag: str
    text: str

    def as_markdown(self, base: Path) -> str:
        relative = self.path.relative_to(base)
        return f"- `{relative}:{self.line}` — **{self.tag}** {self.text.strip()}"


def _should_skip(
    path: Path,
    base_path: Path,
    skip_names: Set[str],
    skip_paths: Sequence[Tuple[str, ...]],
) -> bool:
    """Return ``True`` when ``path`` should be ignored during scanning."""

    try:
        relative_parts = path.relative_to(base_path).parts
    except ValueError:
        relative_parts = path.parts

    dir_parts = relative_parts[:-1] if path.is_file() else relative_parts

    if any(part in skip_names for part in dir_parts):
        return True

    for candidate in skip_paths:
        length = len(candidate)
        if len(dir_parts) >= length and tuple(dir_parts[:length]) == candidate:
            return True
        if len(relative_parts) >= length and tuple(relative_parts[:length]) == candidate:
            return True
    return False


def _matches_ignore_pattern(
    path: Path, base_path: Path, patterns: Sequence[str]
) -> bool:
    """Return ``True`` if ``path`` matches any ignore pattern."""

    if not patterns:
        return False

    normalized_path = path.as_posix()
    candidates = {path.name, normalized_path}
    try:
        relative = path.relative_to(base_path).as_posix()
    except ValueError:
        relative = None
    else:
        candidates.add(relative)

    if path.is_dir():
        candidates.add(normalized_path.rstrip("/") + "/")
        if relative is not None:
            candidates.add(relative.rstrip("/") + "/")

    for candidate in candidates:
        for pattern in patterns:
            if fnmatch(candidate, pattern):
                return True
    return False


def discover_tasks(
    base_path: Path,
    skip_dirs: Optional[Sequence[str]] = None,
    allowed_tags: Optional[Sequence[str]] = None,
    max_file_size: Optional[int] = None,
    allowed_extensions: Optional[Sequence[str]] = None,
    ignore_patterns: Optional[Sequence[str]] = None,
) -> List[Task]:
    """Return all TODO/FIXME/HACK entries under ``base_path``.

    When ``max_file_size`` is provided, files larger than the threshold (in bytes)
    are skipped to avoid expensive scans of large artifacts.  ``allowed_extensions``
    can be used to restrict the scan to files whose names end with one of the
    provided extensions (case-insensitive).  Extensions may be passed with or
    without a leading dot.  ``ignore_patterns`` supplies glob-style patterns that
    are matched against both the file name and the path relative to ``base_path``;
    matching files (and entire directories) are skipped, which helps avoid noisy
    generated assets without expanding ``skip_dirs`` manually.
    """

    skip_lookup, skip_paths = _normalise_skip_entries(base_path, skip_dirs)

    tag_filter: Optional[Set[str]] = None
    if allowed_tags:
        tag_filter = {
            tag.upper()
            for tag in (entry.strip() for entry in allowed_tags if entry)
            if tag
        }

    extension_filter: Optional[Set[str]] = None
    if allowed_extensions:
        normalised_extensions = set()
        for entry in allowed_extensions:
            if not entry:
                continue
            candidate = entry.strip().lower()
            if not candidate:
                continue
            if not candidate.startswith("."):
                candidate = "." + candidate
            normalised_extensions.add(candidate)
        if normalised_extensions:
            extension_filter = normalised_extensions

    normalized_patterns: Tuple[str, ...] = tuple(
        cleaned.replace("\\", "/")
        for cleaned in (
            (entry.strip() if entry is not None else "")
            for entry in (ignore_patterns or ())
        )
        if cleaned
    )

    tasks: List[Task] = []
    seen: Set[Tuple[Path, int, str, str]] = set()

    for root, dirnames, filenames in os.walk(base_path, topdown=True, followlinks=False):
        root_path = Path(root)

        if _matches_ignore_pattern(root_path, base_path, normalized_patterns):
            dirnames[:] = []
            continue

        filtered_dirs = []
        for dirname in dirnames:
            dir_path = root_path / dirname
            if dir_path.is_symlink():
                continue
            if _should_skip(dir_path, base_path, skip_lookup, skip_paths):
                continue
            if _matches_ignore_pattern(dir_path, base_path, normalized_patterns):
                continue
            filtered_dirs.append(dirname)
        dirnames[:] = filtered_dirs

        for filename in filenames:
            file_path = root_path / filename
            if file_path.is_symlink():
                continue
            if _should_skip(file_path, base_path, skip_lookup, skip_paths):
                continue
            if _matches_ignore_pattern(file_path, base_path, normalized_patterns):
                continue
            if extension_filter is not None:
                lower_name = file_path.name.lower()
                if not any(lower_name.endswith(ext) for ext in extension_filter):
                    continue
            if max_file_size is not None and max_file_size >= 0:
                try:
                    if file_path.stat().st_size > max_file_size:
                        continue
                except OSError:
                    continue
            if file_path.name.lower() == "roadmap.md":
                continue
            try:
                text = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for idx, line in enumerate(text.splitlines(), start=1):
                comment = _extract_comment(line)
                if comment is None:
                    continue
                for match in TASK_PATTERN.finditer(comment):
                    tag = match.group("tag").upper()
                    if tag_filter and tag not in tag_filter:
                        continue
                    _record_task(
                        tasks,
                        seen,
                        file_path,
                        idx,
                        tag,
                        (match.group("text") or "").strip(),
                    )

            for line_no, tag, text_value in _discover_block_comment_tasks(text):
                if tag_filter and tag not in tag_filter:
                    continue
                _record_task(tasks, seen, file_path, line_no, tag, text_value)
    tasks.sort(key=lambda task: (task.path.as_posix(), task.line))
    return tasks


def _extract_comment(line: str) -> Optional[str]:
    """Return the comment text from ``line`` if present."""

    stripped = line.lstrip()
    if stripped.startswith("//"):
        return stripped[2:]
    if stripped.startswith("#"):
        return stripped[1:]
    if stripped.startswith("--") and not stripped.startswith("---"):
        return stripped[2:]

    in_single = False
    in_double = False
    index = 0
    length = len(line)
    while index < length:
        char = line[index]
        if char == "\\":
            index += 2
            continue
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return line[index + 1 :]
        elif char == "/" and not in_single and not in_double:
            next_char = line[index + 1 : index + 2]
            if next_char == "/":
                return line[index + 2 :]
            if next_char == "*":
                return line[index + 2 :]
        elif char == "-" and not in_single and not in_double:
            next_char = line[index + 1 : index + 2]
            if next_char == "-":
                third_char = line[index + 2 : index + 3]
                if third_char != "-":
                    prev_char = line[index - 1 : index] if index else ""
                    if prev_char in {"<", "!"}:
                        index += 1
                        continue
                    return line[index + 2 :]
        index += 1
    return None


def _discover_block_comment_tasks(text: str) -> Iterable[Tuple[int, str, str]]:
    """Yield ``(line_no, tag, text)`` for TODO/FIXME/HACK entries within block comments."""

    for pattern, extractor, leading in BLOCK_COMMENT_PATTERNS:
        for match in pattern.finditer(text):
            body = extractor(match)
            start_line = text.count("\n", 0, match.start()) + 1
            lines = body.splitlines() or [body]
            for offset, raw_line in enumerate(lines):
                candidate = raw_line.lstrip(leading)
                for task_match in TASK_PATTERN.finditer(candidate):
                    yield (
                        start_line + offset,
                        task_match.group("tag").upper(),
                        (task_match.group("text") or "").strip(),
                    )


def _record_task(
    tasks: List[Task],
    seen: Set[Tuple[Path, int, str, str]],
    file_path: Path,
    line_no: int,
    tag: str,
    text: str,
) -> None:
    normalized = _normalize_task_text(text)
    key = (file_path, line_no, tag, normalized)
    if key in seen:
        return
    seen.add(key)
    tasks.append(Task(path=file_path, line=line_no, tag=tag, text=normalized))


def _current_timestamp() -> str:
    """Return the canonical timestamp used for generated artifacts."""

    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def build_roadmap(
    tasks: Iterable[Task],
    base_path: Path,
    hotspot_limit: int = DEFAULT_HOTSPOT_LIMIT,
) -> str:
    timestamp = _current_timestamp()
    lines = [
        "# Echo Evolution Roadmap\n\n",
        f"_Last updated: {timestamp}_\n\n",
    ]
    entries = list(tasks)
    if entries:
        lines.extend(_build_summary(entries, base_path, hotspot_limit=hotspot_limit))
    if not entries:
        lines.append("No TODO, FIXME, or HACK markers were discovered.\n")
    else:
        lines.append("## Active TODO/FIXME/HACK Items\n\n")
        for task in entries:
            lines.append(f"{task.as_markdown(base_path)}\n")
    return "".join(lines)


def update_roadmap(
    base_path: Path,
    roadmap_path: Path,
    skip_dirs: Optional[Sequence[str]] = None,
    allowed_tags: Optional[Sequence[str]] = None,
    max_file_size: Optional[int] = None,
    allowed_extensions: Optional[Sequence[str]] = None,
    ignore_patterns: Optional[Sequence[str]] = None,
    json_output_path: Optional[Path] = None,
    hotspot_limit: int = DEFAULT_HOTSPOT_LIMIT,
) -> List[Task]:
    tasks = discover_tasks(
        base_path,
        skip_dirs=skip_dirs,
        allowed_tags=allowed_tags,
        max_file_size=max_file_size,
        allowed_extensions=allowed_extensions,
        ignore_patterns=ignore_patterns,
    )
    roadmap = build_roadmap(tasks, base_path, hotspot_limit=hotspot_limit)
    roadmap_path.write_text(roadmap, encoding="utf-8")
    if json_output_path is not None:
        payload = build_summary_payload(tasks, base_path, hotspot_limit=hotspot_limit)
        rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        if str(json_output_path) == "-":
            sys.stdout.write(rendered)
        else:
            json_output_path.write_text(rendered, encoding="utf-8")
    return tasks


def _build_summary(
    tasks: Sequence[Task],
    base_path: Path,
    *,
    hotspot_limit: int = DEFAULT_HOTSPOT_LIMIT,
) -> List[str]:
    tag_counts = Counter(task.tag for task in tasks)
    location_counts: dict[str, int] = defaultdict(int)
    extension_counts: dict[str, int] = defaultdict(int)
    file_counts: dict[str, int] = defaultdict(int)
    for task in tasks:
        relative = task.path.relative_to(base_path)
        top_level = relative.parts[0] if relative.parts else str(relative)
        location_counts[top_level] += 1
        suffix = relative.suffix.lower()
        key = suffix if suffix else NO_EXTENSION_LABEL
        extension_counts[key] += 1
        file_counts[relative.as_posix()] += 1

    summary_lines = ["## Summary\n\n", "| Category | Count |\n", "| --- | ---: |\n"]
    for tag, count in sorted(tag_counts.items()):
        summary_lines.append(f"| {tag} | {count} |\n")
    summary_lines.append("\n")
    summary_lines.append("### Top-Level Locations\n\n")
    summary_lines.append("| Path | Count |\n")
    summary_lines.append("| --- | ---: |\n")
    for location, count in sorted(location_counts.items()):
        summary_lines.append(f"| {location} | {count} |\n")
    summary_lines.append("\n")
    summary_lines.append("### File Types\n\n")
    summary_lines.append("| Extension | Count |\n")
    summary_lines.append("| --- | ---: |\n")
    for extension, count in sorted(extension_counts.items()):
        summary_lines.append(f"| {extension} | {count} |\n")
    summary_lines.append("\n")

    hotspots = _rank_hotspots(file_counts, limit=hotspot_limit)
    if hotspots:
        summary_lines.append("### Hotspots\n\n")
        summary_lines.append("| File | Count |\n")
        summary_lines.append("| --- | ---: |\n")
        for path, count in hotspots:
            summary_lines.append(f"| {path} | {count} |\n")
        summary_lines.append("\n")
    return summary_lines


def _rank_hotspots(
    file_counts: dict[str, int], *, limit: int = DEFAULT_HOTSPOT_LIMIT
) -> List[Tuple[str, int]]:
    """Return top files with the highest task counts."""

    if limit is not None and limit < 0:
        limit = 0

    ordered = sorted(
        file_counts.items(),
        key=lambda entry: (-entry[1], entry[0]),
    )
    if limit:
        return ordered[:limit]
    return ordered


def build_summary_payload(
    tasks: Sequence[Task],
    base_path: Path,
    hotspot_limit: int = DEFAULT_HOTSPOT_LIMIT,
) -> dict[str, object]:
    """Return a JSON-friendly payload describing the current TODO landscape."""

    entries = list(tasks)
    per_tag = Counter(task.tag for task in entries)
    per_location: dict[str, int] = defaultdict(int)
    per_extension: dict[str, int] = defaultdict(int)
    per_file: dict[str, int] = defaultdict(int)
    serialised_tasks = []

    for task in entries:
        try:
            relative_path = task.path.relative_to(base_path)
        except ValueError:
            relative_path = task.path
        per_location[relative_path.parts[0] if relative_path.parts else str(relative_path)] += 1
        suffix = relative_path.suffix.lower()
        key = suffix if suffix else NO_EXTENSION_LABEL
        per_extension[key] += 1
        per_file[relative_path.as_posix()] += 1
        serialised_tasks.append(
            {
                "path": relative_path.as_posix(),
                "line": task.line,
                "tag": task.tag,
                "text": task.text,
            }
        )

    return {
        "generated_at": _current_timestamp(),
        "totals": {
            "overall": len(entries),
            "per_tag": dict(sorted(per_tag.items())),
            "per_location": dict(sorted(per_location.items())),
            "per_extension": dict(sorted(per_extension.items())),
        },
        "hotspots": [
            {"path": path, "count": count}
            for path, count in _rank_hotspots(per_file, limit=hotspot_limit)
        ],
        "tasks": serialised_tasks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base",
        type=Path,
        default=Path(os.getcwd()),
        help="Base directory to scan",
    )
    parser.add_argument(
        "--roadmap",
        type=Path,
        default=Path(os.getcwd()) / "ROADMAP.md",
        help="Target roadmap file",
    )
    parser.add_argument(
        "--skip",
        action="append",
        default=None,
        metavar="DIR",
        help="Additional directory name to skip (can be passed multiple times)",
    )
    parser.add_argument(
        "--tag",
        action="append",
        default=None,
        metavar="NAME",
        help="Only include tasks with the specified tag (case-insensitive, repeatable)",
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=None,
        metavar="N",
        help="Skip files larger than N bytes when scanning",
    )
    parser.add_argument(
        "--ext",
        action="append",
        default=None,
        metavar="EXT",
        help="Only include files with the given extension (repeatable)",
    )
    parser.add_argument(
        "--ignore",
        action="append",
        default=None,
        metavar="GLOB",
        help="Glob pattern for paths to ignore (repeatable)",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        metavar="PATH",
        help="Optional path to store a machine-readable summary (JSON)",
    )
    parser.add_argument(
        "--hotspots",
        type=int,
        default=DEFAULT_HOTSPOT_LIMIT,
        metavar="N",
        help="Number of hotspot files to include (set to 0 to omit the table)",
    )
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=None,
        metavar="N",
        help=(
            "Exit with a non-zero status if more than N tasks are discovered (use 0 to"
            " forbid TODOs entirely)"
        ),
    )
    parser.add_argument(
        "--fail-on-tasks",
        action="store_true",
        help="Shortcut for --max-tasks=0, useful for CI enforcement",
    )
    args = parser.parse_args()
    max_bytes = args.max_bytes if args.max_bytes and args.max_bytes > 0 else None
    max_tasks = 0 if args.fail_on_tasks else args.max_tasks
    if max_tasks is not None and max_tasks < 0:
        max_tasks = None
    tasks = update_roadmap(
        args.base,
        args.roadmap,
        skip_dirs=args.skip,
        allowed_tags=args.tag,
        max_file_size=max_bytes,
        allowed_extensions=args.ext,
        ignore_patterns=args.ignore,
        json_output_path=args.json_out,
        hotspot_limit=args.hotspots,
    )
    if max_tasks is not None and len(tasks) > max_tasks:
        print(
            f"Discovered {len(tasks)} TODO/FIXME/HACK tasks which exceeds the allowed maximum of"
            f" {max_tasks}.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI helper
    raise SystemExit(main())
