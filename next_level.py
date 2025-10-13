"""Scan the repository for todo/fixme markers and refresh ``ROADMAP.md``."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import os
import re
from pathlib import Path
from typing import Iterable, List, Optional

TASK_PATTERN = re.compile(r"(?P<tag>TODO|FIXME)(?:[:\s-]+(?P<text>.*))?", re.IGNORECASE)
SKIP_DIRS = {".git", "__pycache__", "node_modules", "out", "dist", "build", ".mypy_cache"}


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


def _should_skip(path: Path) -> bool:
    parts = set(path.parts)
    return any(part in SKIP_DIRS for part in parts)


def discover_tasks(base_path: Path) -> List[Task]:
    """Return all TODO/FIXME entries under ``base_path``."""

    tasks: List[Task] = []
    for file_path in base_path.rglob("*"):
        if not file_path.is_file():
            continue
        if _should_skip(file_path):
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
            match = TASK_PATTERN.search(comment)
            if match:
                tasks.append(
                    Task(
                        path=file_path,
                        line=idx,
                        tag=match.group("tag").upper(),
                        text=(match.group("text") or "").strip(),
                    )
                )
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


def build_roadmap(tasks: Iterable[Task], base_path: Path) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    lines = [
        "# Echo Evolution Roadmap\n\n",
        f"_Last updated: {timestamp}_\n\n",
    ]
    entries = list(tasks)
    if not entries:
        lines.append("No TODO or FIXME markers were discovered.\n")
    else:
        lines.append("## Active TODO/FIXME Items\n\n")
        for task in entries:
            lines.append(f"{task.as_markdown(base_path)}\n")
    return "".join(lines)


def update_roadmap(base_path: Path, roadmap_path: Path) -> List[Task]:
    tasks = discover_tasks(base_path)
    roadmap = build_roadmap(tasks, base_path)
    roadmap_path.write_text(roadmap, encoding="utf-8")
    return tasks


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
    args = parser.parse_args()
    update_roadmap(args.base, args.roadmap)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI helper
    raise SystemExit(main())
