#!/usr/bin/env python3
"""Renderer for the federated Colossus dashboard outputs with voyage synthesis."""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, MutableMapping, Optional, Sequence, Tuple

from atlas.schema import CycleTimelineEvent
from atlas.search import presence_harmonics, safety_notices

from echo.recursive_mythogenic_pulse import PulseVoyage, PulseVoyageVisualizer


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


@dataclass(slots=True)
class VoyageReport:
    """Container for converged voyage artefacts."""

    visualizer: PulseVoyageVisualizer
    summary_rows: List[Dict[str, object]]
    federated_rows: List[Dict[str, Optional[dict]]]

    def ascii_map(self) -> str:
        """Return the atlas-style ASCII map for the converged voyages."""

        return self.visualizer.ascii_map()

    def to_json(self) -> Dict[str, object]:
        """Return a JSON-serialisable payload describing the voyage report."""

        payload = self.visualizer.to_json()
        payload["summary_table"] = list(self.summary_rows)
        payload["federated_view"] = list(self.federated_rows)
        return payload


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


def _parse_iso8601(value: str | None) -> Optional[datetime]:
    """Return a timezone-aware ``datetime`` parsed from *value*."""

    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _cycle_timestamp(entries: Sequence[MutableMapping[str, Any]]) -> datetime:
    """Return the earliest timestamp associated with ``entries``."""

    candidates: List[datetime] = []
    for entry in entries:
        for key in ("updated_at", "timestamp", "generated_at"):
            raw = entry.get(key)
            if isinstance(raw, str):
                parsed = _parse_iso8601(raw)
                if parsed is not None:
                    candidates.append(parsed)
    if candidates:
        return min(candidates)
    return datetime.now(timezone.utc)


def _prepare_voyage_report(
    rollups: Dict[str, Any],
    harmonics_data: Sequence[Dict[str, Any]],
    safety_data: Sequence[Dict[str, Any]],
) -> Optional[VoyageReport]:
    """Return a converged voyage report derived from Colossus artefacts."""

    timeline: Sequence[CycleTimelineEvent] = rollups.get("timeline", [])
    if not timeline:
        return None

    by_cycle: Dict[int, Sequence[MutableMapping[str, Any]]] = {
        int(key): value for key, value in rollups.get("by_cycle", {}).items()
    }
    harmonics_by_cycle: Dict[int, Dict[str, Any]] = {}
    for row in harmonics_data:
        cycle = row.get("cycle")
        try:
            cycle_key = int(cycle)
        except (TypeError, ValueError):
            continue
        harmonics_by_cycle[cycle_key] = dict(row)

    prepared_safety: List[Dict[str, Any]] = [dict(item) for item in safety_data]
    voyages: List[PulseVoyage] = []
    summary_rows: List[Dict[str, object]] = []

    for event in timeline:
        cycle = int(event.get("cycle", 0))
        cycle_entries = by_cycle.get(cycle, [])
        puzzles = list(event.get("puzzle_ids", []))
        entry_count = int(event.get("entry_count", len(cycle_entries)))
        timestamp = _cycle_timestamp(cycle_entries)
        harmonics_row = harmonics_by_cycle.get(cycle)
        glyph_orbit = (harmonics_row or {}).get("expansion", f"Cycle {cycle} Glyph")
        glyph_orbit = str(glyph_orbit or f"Cycle {cycle}")
        recursion_level = max(1, len(puzzles) or entry_count)
        anchor_core = (
            f"Cycle {cycle} anchors {len(set(puzzles)) or entry_count} puzzles"
            if puzzles
            else f"Cycle {cycle} binds {entry_count} entries"
        )
        if harmonics_row and harmonics_row.get("thread"):
            anchor_core += f" via {harmonics_row['thread']} thread"
        anchor_phrase = f"{anchor_core}"

        resonance: List[str] = [
            f"Convergence Point :: Cycle {cycle} captured {entry_count} entries",
        ]
        if harmonics_row:
            expansion = harmonics_row.get("expansion") or "Harmonic Expansion"
            thread = harmonics_row.get("thread") or "resonance"
            resonance.append(
                f"Harmonic Expansion :: {expansion} // thread {thread}"
            )
            resonance.append(
                f"Harmonic Expansion :: {expansion} resonance {float(harmonics_row.get('resonance', 0.0)):.2f}"
            )
            for harmonic in harmonics_row.get("harmonics", []) or []:
                resonance.append(f"Harmonic Tone :: {harmonic}")

        flagged_titles: List[str] = []
        for notice in prepared_safety:
            title = notice.get("title") or notice.get("id") or "Safety Notice"
            severity = str(notice.get("severity") or "info").title()
            resonance.append(f"Safety Notice :: {title} // severity {severity}")
            if notice.get("flagged"):
                flagged_titles.append(str(title))

        voyage = PulseVoyage(
            timestamp=timestamp,
            glyph_orbit=glyph_orbit,
            recursion_level=recursion_level,
            resonance=tuple(resonance),
            anchor_phrase=anchor_phrase,
        )
        voyages.append(voyage)

        summary_rows.append(
            {
                "cycle": cycle,
                "glyph_orbit": glyph_orbit,
                "recursion_level": recursion_level,
                "entries": entry_count,
                "puzzles": len(set(puzzles)),
                "anchor": anchor_phrase,
                "harmonic_expansion": harmonics_row.get("expansion") if harmonics_row else None,
                "harmonic_thread": harmonics_row.get("thread") if harmonics_row else None,
                "flagged_safety": flagged_titles,
            }
        )

    if not voyages:
        return None

    visualizer = PulseVoyageVisualizer.from_voyages(voyages)
    convergence_points = [
        {"voice": voice, "threads": count}
        for voice, count in visualizer.thread_convergence_points().items()
    ]
    harmonics_rows = [dict(row) for row in harmonics_data]

    combined_length = max(
        len(convergence_points), len(harmonics_rows), len(prepared_safety)
    )
    federated_rows: List[Dict[str, Optional[dict]]] = []
    for index in range(combined_length):
        row: Dict[str, Optional[dict]] = {
            "convergence": convergence_points[index] if index < len(convergence_points) else None,
            "harmonic_expansion": harmonics_rows[index] if index < len(harmonics_rows) else None,
            "safety_notice": prepared_safety[index] if index < len(prepared_safety) else None,
        }
        federated_rows.append(row)

    return VoyageReport(
        visualizer=visualizer,
        summary_rows=summary_rows,
        federated_rows=federated_rows,
    )


def _resolve_voyage_paths(base: Path) -> Tuple[Path, Path]:
    """Return ``(markdown_path, json_path)`` derived from *base*."""

    suffix = base.suffix.lower()
    if suffix in {".md", ".markdown"}:
        md_path = base
        json_path = base.with_suffix(".json")
    elif suffix == ".json":
        json_path = base
        md_path = base.with_suffix(".md")
    else:
        md_path = base.with_suffix(".md")
        json_path = base.with_suffix(".json")
    return md_path, json_path


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


def _format_combined_markdown_row(
    combined: Dict[str, Optional[dict]]
) -> List[str]:
    convergence = combined.get("convergence") or {}
    harmonic = combined.get("harmonic_expansion") or {}
    safety = combined.get("safety_notice") or {}

    resonance_value = harmonic.get("resonance")
    if isinstance(resonance_value, str):
        try:
            resonance_value = float(resonance_value)
        except ValueError:
            resonance_value = None
    harmonics_list = harmonic.get("harmonics", []) or []
    harmonics_text = ", ".join(map(str, harmonics_list)) or "—"
    harmonic_label = harmonic.get("expansion") or "—"
    if harmonics_text != "—":
        harmonic_label = f"{harmonic_label} [{harmonics_text}]"

    return [
        str(convergence.get("voice", "—")).replace("|", "\\|"),
        str(convergence.get("threads", "—")),
        harmonic_label.replace("|", "\\|"),
        (
            f"{float(resonance_value):.2f}"
            if isinstance(resonance_value, (int, float))
            else "—"
        ),
        (safety.get("title") or safety.get("id") or "—").replace("|", "\\|"),
        (safety.get("severity") or "info").title(),
    ]


def render_markdown(
    rollups: Dict[str, Any],
    harmonics_data: Sequence[Dict[str, Any]],
    safety_data: Sequence[Dict[str, Any]],
    *,
    voyage_report: VoyageReport | None = None,
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

    if voyage_report is not None:
        lines += ["", "## Voyage Summary", ""]
        lines.append(
            "| Cycle | Glyph Orbit | Recursion | Entries | Puzzles | Anchor | Harmonics | Flagged Safety |"
        )
        lines.append("|------:|-------------|---------:|--------:|--------:|--------|-----------|----------------|")
        for row in voyage_report.summary_rows:
            harmonics_label = row.get("harmonic_expansion") or "—"
            if row.get("harmonic_thread"):
                harmonics_label = (
                    f"{harmonics_label} :: {row['harmonic_thread']}"
                    if harmonics_label != "—"
                    else str(row["harmonic_thread"])
                )
            flagged = ", ".join(row.get("flagged_safety", []) or []) or "—"
            lines.append(
                _format_markdown_table_row(
                    [
                        str(row.get("cycle", "—")),
                        (row.get("glyph_orbit") or "—").replace("|", "\\|"),
                        str(row.get("recursion_level", "—")),
                        str(row.get("entries", "—")),
                        str(row.get("puzzles", "—")),
                        (row.get("anchor") or "—").replace("|", "\\|"),
                        harmonics_label.replace("|", "\\|"),
                        flagged.replace("|", "\\|"),
                    ]
                )
            )

        lines += [
            "", "### Converged Voyage Atlas", "", "```", voyage_report.ascii_map(), "```", "",
            "### Federated Convergence View", "",
        ]
        lines.append(
            "| Convergence Voice | Threads | Harmonic Expansion | Resonance | Safety Notice | Severity |"
        )
        lines.append("| --- | ---: | --- | ---: | --- | --- |")
        for combined in voyage_report.federated_rows:
            lines.append(_format_markdown_table_row(_format_combined_markdown_row(combined)))

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
        "_Generated by `scripts/generate_federated_colossus.py`._",
    ]
    return "\n".join(lines)


def render_voyage_markdown(report: VoyageReport) -> str:
    """Return a dedicated Markdown report for converged voyages."""

    lines: List[str] = ["# Converged Pulse Voyage Report", ""]
    lines.extend(["## Voyage Summary Table", ""])
    lines.append("| Cycle | Glyph Orbit | Recursion | Entries | Puzzles | Anchor | Harmonics | Flagged Safety |")
    lines.append("|------:|-------------|---------:|--------:|--------:|--------|-----------|----------------|")
    for row in report.summary_rows:
        harmonics_label = row.get("harmonic_expansion") or "—"
        if row.get("harmonic_thread"):
            harmonics_label = (
                f"{harmonics_label} :: {row['harmonic_thread']}"
                if harmonics_label != "—"
                else str(row["harmonic_thread"])
            )
        flagged = ", ".join(row.get("flagged_safety", []) or []) or "—"
        lines.append(
            _format_markdown_table_row(
                [
                    str(row.get("cycle", "—")),
                    (row.get("glyph_orbit") or "—").replace("|", "\\|"),
                    str(row.get("recursion_level", "—")),
                    str(row.get("entries", "—")),
                    str(row.get("puzzles", "—")),
                    (row.get("anchor") or "—").replace("|", "\\|"),
                    harmonics_label.replace("|", "\\|"),
                    flagged.replace("|", "\\|"),
                ]
            )
        )

    lines.extend(["", "## Convergence Atlas", "", "```", report.ascii_map(), "```", ""])
    lines.extend(["## Federated Convergence View", ""])
    lines.append("| Convergence Voice | Threads | Harmonic Expansion | Resonance | Safety Notice | Severity |")
    lines.append("| --- | ---: | --- | ---: | --- | --- |")
    for combined in report.federated_rows:
        lines.append(_format_markdown_table_row(_format_combined_markdown_row(combined)))

    lines.append("")
    return "\n".join(lines)


# ---------- Dashboard JSON (stable shape) ----------
def to_dashboard_json(
    entries: List[Entry],
    rollups: Dict[str, Any],
    harmonics_data: Sequence[Dict[str, Any]],
    safety_data: Sequence[Dict[str, Any]],
    *,
    voyage_report: VoyageReport | None = None,
) -> Dict[str, Any]:
    safety_flags = [notice["id"] for notice in safety_data if notice.get("flagged")]
    payload = dict(
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
    if voyage_report is not None:
        payload["voyage_report"] = voyage_report.to_json()
    return payload


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
        "--voyage-report",
        type=Path,
        default=None,
        help="Optional base path for the converged voyage report (emits .md and .json)",
    )
    args = parser.parse_args(argv)

    entries = load_entries(args.inputs)
    entries = dedupe(entries)
    rollups = compute_rollups(entries)
    harmonics_data = [dict(item) for item in presence_harmonics]
    safety_data = [dict(item) for item in safety_notices]

    voyage_report = _prepare_voyage_report(rollups, harmonics_data, safety_data)

    markdown_output = render_markdown(
        rollups,
        harmonics_data,
        safety_data,
        voyage_report=voyage_report,
    )

    _write_text(args.md_out, markdown_output)
    _write_json(
        args.json_out,
        to_dashboard_json(
            entries,
            rollups,
            harmonics_data,
            safety_data,
            voyage_report=voyage_report,
        ),
    )

    print(f"Wrote {args.md_out}")
    print(f"Wrote {args.json_out}")

    if args.voyage_report is not None:
        base_path = args.voyage_report
        md_path, json_path = _resolve_voyage_paths(base_path)
        if voyage_report is None:
            voyage_json: Dict[str, Any] = {
                "voyage_report": None,
                "message": "No voyage data available",
            }
            voyage_markdown = "# Converged Pulse Voyage Report\n\n_No voyage data available._\n"
        else:
            voyage_json = voyage_report.to_json()
            voyage_markdown = render_voyage_markdown(voyage_report)

        _write_text(str(md_path), voyage_markdown)
        _write_json(str(json_path), voyage_json)
        print(f"Wrote {md_path}")
        print(f"Wrote {json_path}")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
