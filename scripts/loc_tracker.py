#!/usr/bin/env python3
"""Summarise line-of-code contributions across key Echo subsystems."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

_SUPPORTED_EXTENSIONS = {
    ".py",
    ".json",
    ".md",
    ".txt",
    ".js",
    ".ts",
    ".tsx",
    ".html",
    ".css",
    ".yml",
    ".yaml",
}


@dataclass(frozen=True)
class CategoryReport:
    """Aggregate statistics for a tracked category."""

    name: str
    files: int
    lines: int

    def as_dict(self) -> dict[str, object]:
        return {"name": self.name, "files": self.files, "lines": self.lines}


_DEFAULT_GROUPS: Mapping[str, Sequence[str]] = {
    "fixtures": ("tests/fixtures",),
    "clients": ("pulse_dashboard/client.py",),
    "tests": (
        "tests/test_pulse_dashboard_builder.py",
        "tests/test_pulse_dashboard_client.py",
    ),
    "dashboard": (
        "pulse_dashboard/builder.py",
        "pulse_dashboard/client.py",
    ),
}


def _iter_files(root: Path, paths: Iterable[str]) -> Iterable[Path]:
    for relative in paths:
        candidate = (root / relative).resolve()
        if candidate.is_dir():
            yield from (path for path in candidate.rglob("*") if path.is_file())
        elif candidate.is_file():
            yield candidate


def _count_lines(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return sum(1 for _ in handle)
    except UnicodeDecodeError:
        return 0


def _collect_group(root: Path, name: str, targets: Sequence[str], *, extensions: set[str]) -> CategoryReport:
    files_seen = set()
    line_total = 0
    for path in _iter_files(root, targets):
        if path.suffix.lower() not in extensions:
            continue
        files_seen.add(path)
        line_total += _count_lines(path)
    return CategoryReport(name=name, files=len(files_seen), lines=line_total)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Project root containing the tracked categories.",
    )
    parser.add_argument(
        "--format",
        choices={"json", "text"},
        default="text",
        help="Output format for the summary report.",
    )
    parser.add_argument(
        "--extensions",
        nargs="*",
        default=sorted(_SUPPORTED_EXTENSIONS),
        help="File extensions to include when counting lines (defaults to a curated set).",
    )
    parser.add_argument(
        "--group",
        action="append",
        metavar="NAME=PATH[,PATH]",
        help=(
            "Override or extend the default groups. Provide NAME=PATH[,PATH] to "
            "specify custom tracking targets."
        ),
    )
    return parser


def _parse_custom_groups(overrides: Sequence[str] | None) -> dict[str, tuple[str, ...]]:
    if not overrides:
        return {}
    groups: dict[str, tuple[str, ...]] = {}
    for item in overrides:
        if "=" not in item:
            raise ValueError(f"Invalid group specification: {item!r}")
        name, paths = item.split("=", 1)
        tokens = tuple(filter(None, (segment.strip() for segment in paths.split(","))))
        if not tokens:
            raise ValueError(f"No paths specified for group {name!r}")
        groups[name.strip()] = tokens
    return groups


def _merge_groups(custom: Mapping[str, Sequence[str]] | None) -> Mapping[str, Sequence[str]]:
    merged: dict[str, Sequence[str]] = dict(_DEFAULT_GROUPS)
    if not custom:
        return merged
    for name, paths in custom.items():
        merged[name] = tuple(paths)
    return merged


def _render_text(reports: Sequence[CategoryReport]) -> str:
    lines = ["Category        Files   LOC"]
    lines.append("---------------------------")
    for report in reports:
        lines.append(f"{report.name:<14} {report.files:>5} {report.lines:>6}")
    grand_total = sum(report.lines for report in reports)
    lines.append("---------------------------")
    lines.append(f"total           {sum(r.files for r in reports):>5} {grand_total:>6}")
    return "\n".join(lines)


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        custom_groups = _parse_custom_groups(args.group)
    except ValueError as exc:  # pragma: no cover - defensive guard for CLI parsing
        parser.error(str(exc))
        return 1

    extensions = {ext if ext.startswith(".") else f".{ext}" for ext in args.extensions}
    reports = [
        _collect_group(args.root, name, paths, extensions=extensions)
        for name, paths in _merge_groups(custom_groups).items()
    ]

    if args.format == "json":
        print(json.dumps([report.as_dict() for report in reports], indent=2))
    else:
        print(_render_text(reports))

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
