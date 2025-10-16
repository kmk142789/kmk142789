"""Scan the repository for todo/fixme markers and refresh ``ROADMAP.md``."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import os
import re
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set, Tuple

TASK_PATTERN = re.compile(r"(?P<tag>TODO|FIXME)(?:[:\s-]+(?P<text>.*))?", re.IGNORECASE)
BLOCK_COMMENT_PATTERNS: Tuple[Tuple[re.Pattern[str], int, int, str], ...] = (
    # pattern, prefix trim length, suffix trim length, leading characters to strip per line
    (re.compile(r"/\*.*?\*/", re.DOTALL), 2, 2, " \t*"),
    (re.compile(r"<!--.*?-->", re.DOTALL), 4, 3, " \t-!*"),
)
DEFAULT_SKIP_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    "out",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "venv",
    "env",
    ".tox",
    ".nox",
}


@dataclass(slots=True)
class Task:
    """Representation of a discovered TODO/FIXME entry."""

    path: Path
    line: int
    tag: str
    text: str

    def as_markdown(self, base: Path) -> str:
        relative = self.path.relative_to(base)
        return f"- `{relative}:{self.line}` — **{self.tag}** {self.text.strip()}"


def _should_skip(path: Path, skip_dirs: Set[str]) -> bool:
    parts = set(path.parts)
    return any(part in skip_dirs for part in parts)


def discover_tasks(
    base_path: Path,
    skip_dirs: Optional[Sequence[str]] = None,
    allowed_tags: Optional[Sequence[str]] = None,
) -> List[Task]:
    """Return all TODO/FIXME entries under ``base_path``."""

    skip_lookup = DEFAULT_SKIP_DIRS.copy()
    if skip_dirs:
        for entry in skip_dirs:
            if entry:
                skip_lookup.add(entry)

    tag_filter: Optional[Set[str]] = None
    if allowed_tags:
        tag_filter = {tag.upper() for tag in allowed_tags}

    tasks: List[Task] = []
    seen: Set[Tuple[Path, int, str, str]] = set()

    for file_path in base_path.rglob("*"):
        if not file_path.is_file():
            continue
        if _should_skip(file_path, skip_lookup):
            continue
        if file_path.name.lower() == "roadmap.md":
            continue
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
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
        index += 1
    return None


def _discover_block_comment_tasks(text: str) -> Iterable[Tuple[int, str, str]]:
    """Yield ``(line_no, tag, text)`` for TODO/FIXME entries within block comments."""

    for pattern, prefix_trim, suffix_trim, leading in BLOCK_COMMENT_PATTERNS:
        for match in pattern.finditer(text):
            body = match.group()[prefix_trim:]
            if suffix_trim:
                body = body[: -suffix_trim]
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
    normalized = text.strip()
    key = (file_path, line_no, tag, normalized)
    if key in seen:
        return
    seen.add(key)
    tasks.append(Task(path=file_path, line=line_no, tag=tag, text=normalized))


def build_roadmap(tasks: Iterable[Task], base_path: Path) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    lines = [
        "# Echo Evolution Roadmap\n\n",
        f"_Last updated: {timestamp}_\n\n",
    ]
    entries = list(tasks)
    if entries:
        lines.extend(_build_summary(entries, base_path))
    if not entries:
        lines.append("No TODO or FIXME markers were discovered.\n")
    else:
        lines.append("## Active TODO/FIXME Items\n\n")
        for task in entries:
            lines.append(f"{task.as_markdown(base_path)}\n")
    return "".join(lines)


def update_roadmap(
    base_path: Path,
    roadmap_path: Path,
    skip_dirs: Optional[Sequence[str]] = None,
    allowed_tags: Optional[Sequence[str]] = None,
) -> List[Task]:
    tasks = discover_tasks(base_path, skip_dirs=skip_dirs, allowed_tags=allowed_tags)
    roadmap = build_roadmap(tasks, base_path)
    roadmap_path.write_text(roadmap, encoding="utf-8")
    return tasks


def _build_summary(tasks: Sequence[Task], base_path: Path) -> List[str]:
    tag_counts = Counter(task.tag for task in tasks)
    location_counts: dict[str, int] = defaultdict(int)
    for task in tasks:
        relative = task.path.relative_to(base_path)
        top_level = relative.parts[0] if relative.parts else str(relative)
        location_counts[top_level] += 1

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
    return summary_lines


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
    args = parser.parse_args()
    update_roadmap(args.base, args.roadmap, skip_dirs=args.skip, allowed_tags=args.tag)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI helper
    raise SystemExit(main())
