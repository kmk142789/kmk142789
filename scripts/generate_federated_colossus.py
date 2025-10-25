#!/usr/bin/env python3
"""Stdlib-only renderer for the federated Colossus dashboard outputs."""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, Iterable, List, Sequence

from atlas.schema import CycleTimelineEvent
from atlas.search import presence_harmonics, safety_notices


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
      - harmonics (List[int])
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
def _normalise_harmonics(raw: Any) -> List[int]:
    values: List[int] = []
    if not isinstance(raw, list):
        return values
    for item in raw:
        if isinstance(item, bool):  # bool is a subclass of int
            continue
        if isinstance(item, (int, float)):
            values.append(int(item))
            continue
        if isinstance(item, str):
            text = item.strip()
            if not text:
                continue
            try:
                values.append(int(text))
            except ValueError:
                continue
    return values


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
def _summarise_harmonics(values: Sequence[int]) -> str:
    if not values:
        return "—"
    return f"{len(values)} values (min={min(values)}, max={max(values)})"


def compute_rollups(entries: List[Entry]) -> Dict[str, Any]:
    by_cycle: Dict[int, List[Entry]] = defaultdict(list)
    by_puzzle: Dict[int, List[Entry]] = defaultdict(list)
    by_address: Dict[str, List[Entry]] = defaultdict(list)

    for entry in entries:
        by_cycle[entry["cycle"]].append(entry)
        by_puzzle[entry["puzzle_id"]].append(entry)
        by_address[entry["address"].lower()].append(entry)

    timeline: List[CycleTimelineEvent] = []
    for cycle, group in sorted(by_cycle.items()):
        puzzles = sorted({entry["puzzle_id"] for entry in group})
        harmonics: List[int] = []
        for entry in group:
            candidate = entry.get("harmonics", [])
            if candidate:
                harmonics = list(candidate)
                break
        timeline.append(
            CycleTimelineEvent(
                cycle=cycle,
                entry_count=len(group),
                puzzle_ids=puzzles,
                harmonics=harmonics,
            )
        )

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
    )


# ---------- Markdown emitter ----------
def _format_markdown_table_row(cells: Sequence[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def render_markdown(
    rollups: Dict[str, Any],
    harmonics_data: Sequence[Dict[str, Any]],
    safety_data: Sequence[Dict[str, Any]],
) -> str:
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
        harmonics_text = _summarise_harmonics(event["harmonics"])
        lines.append(
            f"| {event['cycle']} | {event['entry_count']} | `{puzzle_text}` | {harmonics_text} |"
        )

    lines += ["", "## Harmonic Expansions", ""]
    lines.append("| Cycle | Expansion | Thread | Resonance | Harmonics | Notes |")
    lines.append("|------:|-----------|--------|----------:|-----------|-------|")
    for row in harmonics_data:
        harmonics_text = ", ".join(row.get("harmonics", [])) or "—"
        notes = (row.get("notes") or "—").replace("|", "\\|")
        lines.append(
            _format_markdown_table_row(
                [
                    str(row.get("cycle", "—")),
                    (row.get("expansion") or "—").replace("|", "\\|"),
                    (row.get("thread") or "—").replace("|", "\\|"),
                    f"{float(row.get('resonance', 0.0)):.2f}",
                    f"`{harmonics_text}`" if harmonics_text != "—" else "—",
                    notes,
                ]
            )
        )

    lines += ["", "## Safety Notices", ""]
    lines.append("| Notice | Severity | Summary | Flags | Active Flag | Guidance |")
    lines.append("|--------|----------|---------|-------|-------------|----------|")
    for notice in safety_data:
        summary = (notice.get("summary") or "—").replace("|", "\\|")
        guidance = (notice.get("guidance") or "—").replace("|", "\\|")
        flags = ", ".join(notice.get("flags", [])) or "—"
        active_flag = "Yes" if notice.get("flagged") else "No"
        lines.append(
            _format_markdown_table_row(
                [
                    (notice.get("title") or notice.get("id") or "—").replace("|", "\\|"),
                    (notice.get("severity") or "info").title(),
                    summary,
                    f"`{flags}`" if flags != "—" else "—",
                    active_flag,
                    guidance,
                ]
            )
        )

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
def to_dashboard_json(
    entries: List[Entry],
    rollups: Dict[str, Any],
    harmonics_data: Sequence[Dict[str, Any]],
    safety_data: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    safety_flags = [notice["id"] for notice in safety_data if notice.get("flagged")]
    return dict(
        schema="io.echo.colossus/federated-index@1",
        refreshed_at=datetime.utcnow().isoformat() + "Z",
        totals=rollups["totals"],
        entries=entries,
        by_cycle=rollups["by_cycle"],
        by_puzzle=rollups["by_puzzle"],
        timeline=rollups["timeline"],
        harmonics=list(harmonics_data),
        safety=dict(notices=list(safety_data), flags=safety_flags),
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
    args = parser.parse_args(argv)

    entries = load_entries(args.inputs)
    entries = dedupe(entries)
    rollups = compute_rollups(entries)
    harmonics_data = [dict(item) for item in presence_harmonics]
    safety_data = [dict(item) for item in safety_notices]

    _write_text(args.md_out, render_markdown(rollups, harmonics_data, safety_data))
    _write_json(
        args.json_out,
        to_dashboard_json(entries, rollups, harmonics_data, safety_data),
    )

    print(f"Wrote {args.md_out}")
    print(f"Wrote {args.json_out}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
