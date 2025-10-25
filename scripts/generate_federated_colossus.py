#!/usr/bin/env python3
"""Stdlib-only renderer for the federated Colossus dashboard outputs."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, Iterable, List, Sequence

from atlas.schema import CycleTimelineEvent


# ---------- Shared model ----------
class Entry(dict):
    """Normalized federated index entry.

    Required fields:
      - cycle (int)
      - puzzle_id (int)
      - address (str)
      - title (str)          # human label
      - digest (str)         # content hash / checksum / merkle root
      - source (str)         # file/path/uri
    Optional:
      - tags (List[str])
      - lineage (List[int])  # parent cycles or branch ids
      - updated_at (str ISO8601)
      - harmonics (List[float])
    """

    @property
    def key(self) -> tuple[int, str]:
        return (int(self["puzzle_id"]), self["address"].strip().lower())


# ---------- I/O helpers ----------
def _read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


# ---------- Normalisation helpers ----------
def _normalise_harmonics(raw: Any) -> List[float]:
    values: List[float] = []
    if not isinstance(raw, list):
        return values
    for item in raw:
        if isinstance(item, bool):  # bool is a subclass of int
            continue
        if isinstance(item, (int, float)):
            values.append(float(item))
            continue
        if isinstance(item, str):
            text = item.strip()
            if not text:
                continue
            try:
                values.append(float(text))
            except ValueError:
                continue
    return values


def _normalise_values(
    values: Sequence[float], minimum: float | None, maximum: float | None
) -> List[float]:
    if not values or minimum is None or maximum is None:
        return []
    if maximum == minimum:
        return [1.0 for _ in values]
    scale = maximum - minimum
    out: List[float] = []
    for value in values:
        out.append(min(1.0, max(0.0, (value - minimum) / scale)))
    return out


def _sparkline(normalized_values: Sequence[float]) -> str:
    if not normalized_values:
        return ""
    # ASCII-friendly ramp from low to high energy.
    ramp = " .:-=+*#%@"
    last_index = len(ramp) - 1
    chars: List[str] = []
    for value in normalized_values:
        idx = int(round(value * last_index))
        idx = min(max(idx, 0), last_index)
        chars.append(ramp[idx])
    return "".join(chars)


def _cluster_resonance(normalized_values: Sequence[float]) -> Dict[str, int]:
    buckets = [
        ("0.00-0.25", 0.0, 0.25),
        ("0.25-0.50", 0.25, 0.50),
        ("0.50-0.75", 0.50, 0.75),
        ("0.75-1.00", 0.75, 1.0000000001),
    ]
    counts: Dict[str, int] = {label: 0 for label, *_ in buckets}
    for value in normalized_values:
        for label, lower, upper in buckets:
            if lower <= value < upper or (label == "0.75-1.00" and value >= lower):
                counts[label] += 1
                break
    return counts


def _compute_harmonic_stats(values: Sequence[float]) -> Dict[str, Any]:
    if not values:
        return dict(
            count=0,
            average=None,
            minimum=None,
            maximum=None,
            normalized_average=None,
            normalized_min=None,
            normalized_max=None,
            resonance_clusters=_cluster_resonance([]),
        )

    minimum = min(values)
    maximum = max(values)
    total = sum(values)
    count = len(values)
    normalized = _normalise_values(values, minimum, maximum)
    normalized_average = sum(normalized) / len(normalized) if normalized else None
    normalized_min = min(normalized) if normalized else None
    normalized_max = max(normalized) if normalized else None

    return dict(
        count=count,
        average=total / count,
        minimum=minimum,
        maximum=maximum,
        normalized_average=normalized_average,
        normalized_min=normalized_min,
        normalized_max=normalized_max,
        resonance_clusters=_cluster_resonance(normalized),
    )


# ---------- Load federated graph/search data ----------
def load_entries(paths: Iterable[str]) -> List[Entry]:
    """Accept JSON files containing entries or a map with an ``entries`` key."""

    out: List[Entry] = []
    for path in paths:
        if not os.path.exists(path):
            continue
        data = _read_json(path)
        if isinstance(data, dict) and "entries" in data:
            data = data["entries"]
        if not isinstance(data, list):
            continue
        for raw in data:
            raw.setdefault("tags", [])
            raw.setdefault("lineage", [])
            raw.setdefault("updated_at", datetime.utcnow().isoformat() + "Z")
            raw["harmonics"] = _normalise_harmonics(raw.get("harmonics", []))
            raw["cycle"] = int(raw["cycle"])
            raw["puzzle_id"] = int(raw["puzzle_id"])
            raw["address"] = str(raw["address"])
            out.append(Entry(raw))
    return out


# ---------- Dedupe ----------
def dedupe(entries: List[Entry]) -> List[Entry]:
    best: Dict[tuple, Entry] = {}
    for entry in entries:
        key = entry.key
        previous = best.get(key)
        if previous is None or int(entry["cycle"]) > int(previous["cycle"]):
            best[key] = entry
    return list(best.values())


# ---------- Aggregations ----------
def _summarise_harmonics(
    values: Sequence[float], normalized: Sequence[float]
) -> str:
    if not values:
        return "—"
    avg = sum(values) / len(values)
    minimum = min(values)
    maximum = max(values)
    spark = _sparkline(normalized)
    normalized_avg = (
        sum(normalized) / len(normalized) if normalized else None
    )
    normalized_text = (
        f" / norm={normalized_avg:.2f}" if normalized_avg is not None else ""
    )
    spark_text = f" `{spark}`" if spark else ""
    return (
        f"avg={avg:.2f}{normalized_text}"
        f" (min={minimum:.2f}, max={maximum:.2f})" + spark_text
    )


def compute_rollups(entries: List[Entry]) -> Dict[str, Any]:
    by_cycle: Dict[int, List[Entry]] = defaultdict(list)
    by_puzzle: Dict[int, List[Entry]] = defaultdict(list)
    by_address: Dict[str, List[Entry]] = defaultdict(list)

    for entry in entries:
        by_cycle[entry["cycle"]].append(entry)
        by_puzzle[entry["puzzle_id"]].append(entry)
        by_address[entry["address"].lower()].append(entry)

    all_harmonics: List[float] = []
    for entry in entries:
        all_harmonics.extend(entry.get("harmonics", []))
    harmonic_stats = _compute_harmonic_stats(all_harmonics)
    minimum = harmonic_stats["minimum"]
    maximum = harmonic_stats["maximum"]

    timeline: List[CycleTimelineEvent] = []
    for cycle, group in sorted(by_cycle.items()):
        puzzles = sorted({entry["puzzle_id"] for entry in group})
        harmonics: List[float] = []
        for entry in group:
            harmonics.extend(entry.get("harmonics", []))
        normalized = _normalise_values(harmonics, minimum, maximum)
        summary_event: CycleTimelineEvent = CycleTimelineEvent(
            cycle=cycle,
            entry_count=len(group),
            puzzle_ids=puzzles,
            harmonics=harmonics,
        )
        # type: ignore[typeddict-item]
        summary_event["normalized_harmonics"] = normalized  # embed sparkline inputs
        if normalized:
            summary_event["harmonic_average"] = sum(normalized) / len(normalized)
            summary_event["harmonic_min"] = min(normalized)
            summary_event["harmonic_max"] = max(normalized)
        else:
            summary_event["harmonic_average"] = None
            summary_event["harmonic_min"] = None
            summary_event["harmonic_max"] = None
        timeline.append(summary_event)

    return dict(
        totals=dict(
            entries=len(entries),
            cycles=len(by_cycle),
            puzzles=len(by_puzzle),
            addresses=len(by_address),
        ),
        by_cycle={
            str(cycle): sorted(group, key=lambda item: (item["puzzle_id"], item["address"]))
            for cycle, group in sorted(by_cycle.items())
        },
        by_puzzle={
            str(puzzle): sorted(group, key=lambda item: (item["cycle"], item["address"]))
            for puzzle, group in sorted(by_puzzle.items())
        },
        timeline=timeline,
        harmonics_summary=harmonic_stats,
    )


def _filter_entries_by_harmonics(
    entries: List[Entry],
    min_norm: float | None,
    max_norm: float | None,
) -> List[Entry]:
    if min_norm is None and max_norm is None:
        return entries

    all_values: List[float] = []
    for entry in entries:
        all_values.extend(entry.get("harmonics", []))
    stats = _compute_harmonic_stats(all_values)
    minimum = stats["minimum"]
    maximum = stats["maximum"]
    if minimum is None or maximum is None:
        return []

    filtered: List[Entry] = []
    for entry in entries:
        harmonics = entry.get("harmonics", [])
        normalized = _normalise_values(harmonics, minimum, maximum)
        if not normalized:
            continue
        if any(
            (min_norm is None or value >= min_norm)
            and (max_norm is None or value <= max_norm)
            for value in normalized
        ):
            filtered.append(entry)
    return filtered


# ---------- Markdown emitter ----------
def render_markdown(rollups: Dict[str, Any]) -> str:
    totals = rollups["totals"]
    lines: List[str] = []
    lines += [
        "# Federated Colossus Index",
        "",
        f"*Last refreshed:* {datetime.utcnow().isoformat()}Z",
        "",
        "## Summary",
        "",
        f"- **Entries:** {totals['entries']}",
        f"- **Cycles:** {totals['cycles']}",
        f"- **Puzzles:** {totals['puzzles']}",
        f"- **Addresses:** {totals['addresses']}",
        "",
        "## Cycle Timeline",
        "",
        "| Cycle | Entries | Puzzle IDs | Harmonics |",
        "|------:|--------:|------------|-----------|",
    ]
    for event in rollups["timeline"]:
        puzzle_text = ", ".join(map(str, event["puzzle_ids"])) or "—"
        harmonics_text = _summarise_harmonics(
            event["harmonics"], event.get("normalized_harmonics", [])
        )
        lines.append(
            f"| {event['cycle']} | {event['entry_count']} | `{puzzle_text}` | {harmonics_text} |"
        )

    summary = rollups.get("harmonics_summary", {})
    lines += ["", "## Harmonics Overview", ""]
    if summary.get("count"):
        avg = summary.get("normalized_average")
        avg_text = f"{avg:.2f}" if isinstance(avg, float) else "n/a"
        raw_avg = summary.get("average")
        raw_text = f"{raw_avg:.2f}" if isinstance(raw_avg, float) else "n/a"
        min_text = (
            f"{summary['minimum']:.2f}" if isinstance(summary.get("minimum"), float) else "n/a"
        )
        max_text = (
            f"{summary['maximum']:.2f}" if isinstance(summary.get("maximum"), float) else "n/a"
        )
        lines += [
            f"- **Average harmonic (normalized):** {avg_text}",
            f"- **Average harmonic (raw):** {raw_text}",
            f"- **Minimum harmonic:** {min_text}",
            f"- **Maximum harmonic:** {max_text}",
            "",
            "| Resonance Cluster | Count |",
            "|------------------:|------:|",
        ]
        clusters = summary.get("resonance_clusters", {})
        for label, count in clusters.items():
            lines.append(f"| `{label}` | {count} |")
    else:
        lines.append("No harmonic data available.")

    lines += ["", "## Puzzle → Address Table", ""]
    lines += [
        "| Puzzle | Cycle | Address | Title | Digest |",
        "|------:|------:|---------|-------|--------|",
    ]
    for puzzle, entries in rollups["by_puzzle"].items():
        for entry in entries:
            title = (entry.get("title") or "").replace("|", "\\|")
            lines.append(
                f"| {puzzle} | {entry['cycle']} | `{entry['address']}` | {title} | `{entry['digest']}` |"
            )

    lines += [
        "",
        "_Generated by `scripts/generate_federated_colossus.py` (stdlib only)._",
    ]
    return "\n".join(lines)


# ---------- Dashboard JSON (stable shape) ----------
def to_dashboard_json(entries: List[Entry], rollups: Dict[str, Any]) -> Dict[str, Any]:
    return dict(
        schema="io.echo.colossus/federated-index@1",
        refreshed_at=datetime.utcnow().isoformat() + "Z",
        totals=rollups["totals"],
        entries=entries,
        by_cycle=rollups["by_cycle"],
        by_puzzle=rollups["by_puzzle"],
        timeline=rollups["timeline"],
        harmonics_summary=rollups.get("harmonics_summary", {}),
    )


# ---------- CLI ----------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Emit Markdown + JSON for the federated Colossus index."
    )
    parser.add_argument(
        "--in",
        dest="inputs",
        nargs="+",
        required=True,
        help="Input JSON files (lists of entries or {'entries': [...]})",
    )
    parser.add_argument(
        "--md-out", default="docs/federated_colossus_index.md", help="Markdown output path"
    )
    parser.add_argument(
        "--json-out",
        default="build/index/federated_colossus_index.json",
        help="Dashboard JSON output path",
    )
    parser.add_argument(
        "--min-harmonic",
        type=float,
        default=None,
        help="Lower bound for normalized harmonic filtering (0.0-1.0)",
    )
    parser.add_argument(
        "--max-harmonic",
        type=float,
        default=None,
        help="Upper bound for normalized harmonic filtering (0.0-1.0)",
    )
    args = parser.parse_args(argv)

    entries = load_entries(args.inputs)
    entries = dedupe(entries)
    entries = _filter_entries_by_harmonics(entries, args.min_harmonic, args.max_harmonic)
    rollups = compute_rollups(entries)

    if args.min_harmonic is not None or args.max_harmonic is not None:
        print(
            "Applied harmonic filter:",
            f"min={args.min_harmonic if args.min_harmonic is not None else '-'}",
            f"max={args.max_harmonic if args.max_harmonic is not None else '-'}",
            f"=> {len(entries)} entries",
        )

    _write_text(args.md_out, render_markdown(rollups))
    _write_json(args.json_out, to_dashboard_json(entries, rollups))

    print(f"Wrote {args.md_out}")
    print(f"Wrote {args.json_out}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
