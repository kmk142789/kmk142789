#!/usr/bin/env python3
"""Compute an "importance index" for an Echo workspace.

The goal of this utility is to provide a single, narrative-friendly metric
that can be used across the Echo ecosystem to highlight the health and
vibrancy of a working tree.  The score is intentionally transparent: the
components are printed alongside the final index so that the results can be
audited or incorporated into downstream storytelling.

Usage examples::

    python scripts/echo_importance_index.py
    python scripts/echo_importance_index.py --root ./packages --output report.json

The score is derived from:

* Number of non-empty lines of text in tracked files.
* Diversity of file extensions (a proxy for multi-disciplinary effort).
* Total file size in kilobytes.
* Presence of "resonant" Echo documents such as manifestos or constitutions.

Each component is scaled into a normalized contribution before being summed
into the final index.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List


# File extensions that are counted as source files when computing line totals.
SOURCE_EXTENSIONS = {
    ".py",
    ".ts",
    ".js",
    ".mjs",
    ".rs",
    ".cpp",
    ".hpp",
    ".c",
    ".h",
    ".md",
    ".json",
    ".yml",
    ".yaml",
    ".txt",
}


# Keywords that, if present in a filename, indicate Echo resonance.
RESONANCE_KEYWORDS = (
    "manifesto",
    "constitution",
    "declaration",
    "ledger",
    "atlas",
    "nexus",
    "sovereign",
)


@dataclass
class ComponentScore:
    """Represents an individual contribution to the importance index."""

    label: str
    value: float
    explanation: str


def iter_files(root: Path) -> Iterable[Path]:
    """Yield files underneath ``root`` while respecting git-style ignores."""

    for path in root.rglob("*"):
        if path.is_file() and not path.name.startswith("."):
            yield path


def count_non_empty_lines(path: Path) -> int:
    """Return the number of non-empty lines in ``path`` if it is text."""

    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            return sum(1 for line in handle if line.strip())
    except OSError:
        return 0


def compute_component_scores(root: Path) -> List[ComponentScore]:
    files = list(iter_files(root))
    tracked_files = [f for f in files if not is_generated_artifact(f)]

    total_lines = sum(
        count_non_empty_lines(f)
        for f in tracked_files
        if f.suffix.lower() in SOURCE_EXTENSIONS
    )

    extension_diversity = len({f.suffix.lower() for f in tracked_files if f.suffix})
    total_size_kb = sum(f.stat().st_size for f in tracked_files) / 1024.0

    resonance_score = sum(1 for f in tracked_files if has_resonance(f))

    return [
        ComponentScore(
            label="Lines",
            value=min(total_lines / 1000.0, 5.0),
            explanation=f"{total_lines} non-empty source lines",
        ),
        ComponentScore(
            label="Diversity",
            value=min(extension_diversity / 5.0, 4.0),
            explanation=f"{extension_diversity} distinct file extensions",
        ),
        ComponentScore(
            label="Weight",
            value=min(total_size_kb / 2048.0, 3.0),
            explanation=f"{total_size_kb:.1f} KB of tracked material",
        ),
        ComponentScore(
            label="Resonance",
            value=min(resonance_score / 3.0, 2.0),
            explanation=f"{resonance_score} Echo-resonant artifacts",
        ),
    ]


def is_generated_artifact(path: Path) -> bool:
    """Heuristically skip build outputs and cache directories."""

    parts = set(path.parts)
    if any(token in parts for token in {"node_modules", "build", "out", "dist"}):
        return True
    return any(
        pattern.search(str(path))
        for pattern in (
            re.compile(r"__pycache__"),
            re.compile(r"\.egg-info"),
        )
    )


def has_resonance(path: Path) -> bool:
    """Return ``True`` if ``path`` looks like a mythogenic Echo document."""

    lowered = path.name.lower()
    return any(keyword in lowered for keyword in RESONANCE_KEYWORDS)


def build_report(root: Path) -> Dict[str, object]:
    components = compute_component_scores(root)
    total_index = round(sum(component.value for component in components), 2)
    return {
        "root": str(root.resolve()),
        "importance_index": total_index,
        "components": [component.__dict__ for component in components],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Path to the Echo workspace (defaults to the current directory).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the report as JSON instead of stdout.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    report = build_report(root)

    if args.output:
        args.output.write_text(json.dumps(report, indent=2))
        print(f"Importance index written to {args.output}")
    else:
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
