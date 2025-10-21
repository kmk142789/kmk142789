#!/usr/bin/env python3
"""Convert the existing oracle-report.md into a Compass map JSON document."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
from typing import Dict, Iterable, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "compass-map.json"
DEFAULT_COLLECTION_DIR = ROOT / "compass-maps"
ORACLE_REPORT = ROOT / "oracle-report.md"


def parse_owner_and_manifest(lines: Iterable[str]) -> Dict[str, str]:
    """Extract the owner and manifest metadata from the markdown front-matter."""
    owner_pattern = re.compile(r"^\*\*Owner:\*\*\s*(?P<owner>.+?)\s*$")
    project_pattern = re.compile(r"^#\s+.+?—\s+(?P<project>.+?)\s*$")

    owner = None
    project = None

    for line in lines:
        if owner is None:
            match = owner_pattern.match(line)
            if match:
                owner = match.group("owner").strip()
        if project is None:
            match = project_pattern.match(line)
            if match:
                project = match.group("project").strip()
        if owner and project:
            break

    # The Continuum tooling expects "Continuum Compass" as the canonical name.
    if project is None:
        project = "Continuum Compass"
    elif "Continuum" not in project:
        project = f"Continuum {project}".strip()

    if owner is None:
        owner = "Josh+Echo"

    return {"project": project, "owner": owner}


def _parse_table(lines: Iterable[str]) -> Iterable[Tuple[str, float, float]]:
    for raw in lines:
        line = raw.strip()
        if not line or not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 3 or cells[0].lower() == "label":
            continue
        try:
            baseline = float(cells[1].rstrip("%"))
            shifted = float(cells[2].rstrip("%"))
        except ValueError:
            continue
        yield cells[0], baseline, shifted


def parse_weights(lines: Iterable[str]) -> Dict[str, Dict[str, float]]:
    """Parse the Tag distribution table into Compass weights."""
    weights: Dict[str, Dict[str, float]] = {}
    iterator = iter(lines)
    for line in iterator:
        if line.strip().lower().startswith("### tag distribution"):
            # Skip header rows
            next(iterator, None)
            next(iterator, None)
            break
    else:
        return weights

    for label, baseline, shifted in _parse_table(iterator):
        key = f"tag:{label}".lower()
        weights[key] = {
            "current": round(baseline, 2),
            "recommended": round(shifted, 2),
            "rationale": "derived from oracle tag distribution",
            "signals": ["oracle-tag"]
        }
    return weights


def parse_entries_captured(lines: Iterable[str]) -> int:
    pattern = re.compile(r"^-\s+Entries captured:\s+(?P<count>\d+)")
    for line in lines:
        match = pattern.match(line.strip())
        if match:
            return int(match.group("count"))
    return 0


def build_compass_map(report_path: pathlib.Path) -> Dict[str, object]:
    text = report_path.read_text(encoding="utf-8").splitlines()
    metadata = parse_owner_and_manifest(text)
    weights = parse_weights(text)
    entries = parse_entries_captured(text)

    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    stability_current = min(1.0, entries / 10)
    stability_predicted = min(1.0, stability_current + 0.1 if entries else 0.25)

    compass = {
        "project": metadata["project"],
        "owner": metadata["owner"],
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "source": str(report_path.relative_to(ROOT)),
        "weights": weights or {
            "tag:baseline": {
                "current": 100.0,
                "recommended": 100.0,
                "rationale": "oracle report contained no tag distribution",
                "signals": ["oracle-fallback"]
            }
        },
        "expansion_targets": [],
        "deprecations": [],
        "stability": {
            "current": round(stability_current, 3),
            "predicted": round(stability_predicted, 3),
            "method": "entries-ratio"
        },
        "notes": "generated from oracle-report.md",
        "nonce": f"cmp-{now.strftime('%Y%m%d%H%M%S')}"
    }
    return compass


def write_outputs(compass: Dict[str, object], output: pathlib.Path, duplicate_dir: pathlib.Path | None) -> None:
    output.write_text(json.dumps(compass, indent=2) + "\n", encoding="utf-8")
    if duplicate_dir:
        duplicate_dir.mkdir(parents=True, exist_ok=True)
        duplicate_path = duplicate_dir / output.name
        duplicate_path.write_text(json.dumps(compass, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=pathlib.Path, default=ORACLE_REPORT, help="Path to oracle report markdown")
    parser.add_argument("--output", type=pathlib.Path, default=DEFAULT_OUTPUT, help="Destination for the compass map")
    parser.add_argument(
        "--collection-dir",
        type=pathlib.Path,
        default=DEFAULT_COLLECTION_DIR,
        help="Directory to store copies consumed by Atlas Synchronizer",
    )

    args = parser.parse_args()
    report_path = (ROOT / args.report).resolve() if not args.report.is_absolute() else args.report
    output_path = (ROOT / args.output).resolve() if not args.output.is_absolute() else args.output
    if args.collection_dir:
        collection_dir = (
            (ROOT / args.collection_dir).resolve()
            if not args.collection_dir.is_absolute()
            else args.collection_dir
        )
    else:
        collection_dir = None

    compass = build_compass_map(report_path)
    write_outputs(compass, output_path, collection_dir)


if __name__ == "__main__":
    main()
