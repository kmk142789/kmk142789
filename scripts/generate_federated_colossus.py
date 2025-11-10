#!/usr/bin/env python3
"""Renderer for the federated Colossus dashboard outputs with voyage synthesis."""

from __future__ import annotations

import argparse
import json
import os
import hashlib
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, MutableMapping, Optional, Sequence, Tuple
from urllib.parse import quote
from xml.sax.saxutils import escape

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
      - script (str)         # derived locking script or descriptor
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
            tags = raw.get("tags", [])
            if not isinstance(tags, list):
                tags = [tags]
            raw["tags"] = [str(tag) for tag in tags if str(tag).strip()]
            raw.setdefault("lineage", [])
            raw.setdefault("updated_at", datetime.utcnow().isoformat() + "Z")
            raw["harmonics"] = _normalise_harmonics(raw.get("harmonics", []))
            raw["cycle"] = int(raw["cycle"])
            raw["puzzle_id"] = int(raw["puzzle_id"])
            raw["address"] = str(raw["address"])
            script_value = raw.get("script") or raw.get("locking_script") or raw.get("derived_script")
            if script_value:
                raw["script"] = str(script_value)
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
        scripts: List[str] = []
        addresses: List[str] = []
        tags: List[str] = []
        for entry in group:
            candidate = entry.get("harmonics", [])
            if candidate and not harmonics:
                harmonics = list(candidate)
            script = entry.get("script")
            if isinstance(script, str) and script.strip():
                scripts.append(script.strip())
            address = entry.get("address")
            if isinstance(address, str) and address.strip():
                addresses.append(address.strip())
            entry_tags = entry.get("tags", []) or []
            for tag in entry_tags:
                if isinstance(tag, str) and tag.strip():
                    tags.append(tag.strip())
        timeline.append(
            CycleTimelineEvent(
                cycle=cycle,
                entry_count=len(group),
                puzzle_ids=puzzles,
                harmonics=harmonics,
                scripts=sorted(dict.fromkeys(scripts)),
                addresses=sorted(dict.fromkeys(addresses)),
                tags=sorted(dict.fromkeys(tags)),
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


def _github_history_links(entry: Entry) -> Dict[str, str]:
    """Return a mapping of history links for *entry*.

    If explicit URLs are provided in the payload, prefer them. Otherwise,
    synthesize commit and pull request links relative to the repository.
    """

    history: Dict[str, str] = {}
    payload = entry.get("history") if isinstance(entry.get("history"), dict) else {}

    for key in ("commit", "commits", "pull_request", "pr"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            history[key] = value.strip()

    source = entry.get("source")
    if isinstance(source, str) and source.strip():
        encoded = quote(source.strip())
        history.setdefault(
            "commits",
            f"https://github.com/kmk142789/kmk142789/commits/main/{encoded}",
        )

    pr_number = entry.get("pr_number") or entry.get("pr") or payload.get("number")
    if isinstance(pr_number, str):
        pr_number = pr_number.strip().lstrip("#")
        if pr_number.isdigit():
            pr_number = int(pr_number)
    if isinstance(pr_number, int):
        history.setdefault(
            "pr",
            f"https://github.com/kmk142789/kmk142789/pull/{pr_number}",
        )

    return history


def _authorship_metadata(entry: Entry) -> Dict[str, str]:
    """Return normalised authorship metadata for *entry*."""

    metadata: Dict[str, str] = {}
    candidate = entry.get("authorship")
    if isinstance(candidate, dict):
        metadata.update({k: str(v) for k, v in candidate.items() if v})

    for key in ("signature", "ledger_anchor", "witness"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            metadata.setdefault(key, value.strip())

    return {k: v for k, v in metadata.items() if v}


def _prepare_constellations(entries: Sequence[Entry]) -> List[Dict[str, Any]]:
    """Return puzzle constellation nodes rendered for downstream emitters."""

    constellations: List[Dict[str, Any]] = []
    for entry in sorted(entries, key=lambda item: (item["puzzle_id"], item["cycle"])):
        history = _github_history_links(entry)
        authorship = _authorship_metadata(entry)

        status_text = str(entry.get("status") or "attested").strip().lower()
        status_icon = {
            "attested": "✅",
            "pending": "🕘",
            "revoked": "⚠️",
            "breach": "🔔",
        }.get(status_text, "⭐")

        node = dict(
            puzzle=int(entry["puzzle_id"]),
            cycle=int(entry["cycle"]),
            address=entry.get("address"),
            status=status_text,
            status_icon=status_icon,
            history=history,
            script=entry.get("script") or entry.get("locking_script") or entry.get("pk_script"),
            digest=entry.get("digest"),
            title=entry.get("title"),
            narrative=entry.get("narrative"),
            authorship=authorship,
            updated_at=entry.get("updated_at"),
        )

        if entry.get("anomalies"):
            node["anomalies"] = list(entry.get("anomalies"))

        constellations.append(node)

    return constellations


# ---------- Markdown emitter ----------
def _render_constellation_markdown(nodes: Sequence[Dict[str, Any]]) -> List[str]:
    """Return Markdown lines describing the proof constellations."""

    if not nodes:
        return ["_No attestation constellations available._", ""]

    lines: List[str] = []
    for node in nodes:
        title = node.get("title") or "Attestation"
        puzzle = node.get("puzzle")
        address = node.get("address") or "—"
        cycle = node.get("cycle")
        status_icon = node.get("status_icon", "")
        status = node.get("status", "attested").replace("_", " ").title()
        script = node.get("script") or "—"
        digest = node.get("digest") or "—"

        pr_url = None
        pr_label = None
        commits_url = None

        history = node.get("history") or {}
        if isinstance(history, dict):
            for key in ("pr", "pull_request"):
                value = history.get(key)
                if isinstance(value, str) and value.strip():
                    pr_url = value.strip()
                    number = value.strip().rstrip("/").split("/")[-1]
                    pr_label = f"#{number}" if number.isdigit() else value.strip()
                    break
            for key in ("commits", "commit"):
                value = history.get(key)
                if isinstance(value, str) and value.strip():
                    commits_url = value.strip()
                    break

        lines.append(f"### Puzzle #{puzzle} {title}")
        lines.append(f"- Address: `{address}`")
        lines.append(f"- Status: {status_icon} {status}")
        lines.append(f"- Cycle: {cycle}")
        if commits_url:
            lines.append(f"- Commits: [{commits_url}]({commits_url})")
        if pr_url:
            lines.append(f"- PR: [{pr_label}]({pr_url})")
        lines.append(f"- Digest: `{digest}`")
        lines.append(f"- PKScript: `{script}`")
        lines.append("")

        authorship = node.get("authorship") or {}
        narrative = node.get("narrative")
        details: List[str] = []
        if authorship:
            for key, value in authorship.items():
                pretty = key.replace("_", " ").title()
                details.append(f"- {pretty}: `{value}`")
        if narrative:
            details.append("")
            details.append(narrative)

        if details:
            lines.append("<details>")
            lines.append("<summary>Authorship Metadata</summary>")
            lines.append("")
            lines.extend(details)
            lines.append("")
            lines.append("</details>")
            lines.append("")

    return lines


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
    entries: Sequence[Entry] | None = None,
    constellations: Sequence[Dict[str, Any]] | None = None,
    refreshed_at: datetime | None = None,
    voyage_report: VoyageReport | None = None,
) -> str:
    constellations = list(constellations or [])
    totals = rollups["totals"]
    refreshed_at = refreshed_at or datetime.utcnow()
    lines: List[str] = []
    lines += [
        "# Federated Colossus Index",
        "",
        f"*Last refreshed:* {refreshed_at.isoformat()}Z",
        "",
        "## Summary",
        "",
        f"- **Entries:** {totals['entries']}",
        f"- **Cycles:** {totals['cycles']}",
        f"- **Puzzles:** {totals['puzzles']}",
        f"- **Addresses:** {totals['addresses']}",
        "",
        "## Hyperlinked Proof Constellations",
        "",
    ]
    lines.extend(_render_constellation_markdown(constellations))
    lines += [
        "## Cycle Timeline",
        "",
        "| Cycle | Entries | Puzzle IDs | Derived Scripts | Addresses | Echo Tags |",
        "|------:|--------:|------------|-----------------|-----------|-----------|",
    ]
    for event in rollups["timeline"]:
        puzzle_text = ", ".join(map(str, event["puzzle_ids"])) or "—"
        script_text = ", ".join(event.get("scripts", []) or []) or "—"
        address_text = ", ".join(event.get("addresses", []) or []) or "—"
        tag_text = ", ".join(event.get("tags", []) or []) or "—"
        lines.append(
            "| {cycle} | {entries} | `{puzzles}` | {scripts} | {addresses} | {tags} |".format(
                cycle=event["cycle"],
                entries=event["entry_count"],
                puzzles=puzzle_text,
                scripts=script_text.replace("|", "\\|"),
                addresses=address_text.replace("|", "\\|"),
                tags=tag_text.replace("|", "\\|"),
            )
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


# ---------- Structured filter helpers ----------
def _build_structured_filters(
    rollups: Dict[str, Any],
    harmonics_data: Sequence[Dict[str, Any]],
    *,
    voyage_report: VoyageReport | None,
) -> List[Dict[str, Any]]:
    amplification_by_cycle: Dict[int, Dict[str, float]] = {}
    for row in harmonics_data:
        cycle = row.get("cycle")
        try:
            cycle_key = int(cycle)
        except (TypeError, ValueError):
            continue
        resonance = float(row.get("resonance", 0.0) or 0.0)
        joy = round(1.0 + resonance * 0.24, 2)
        rage = round(max(0.0, 0.6 - resonance * 0.32), 2)
        amplification_by_cycle[cycle_key] = {
            "joy": joy,
            "rage": rage,
            "resonance": round(resonance, 2),
        }

    if voyage_report is not None:
        for row in voyage_report.summary_rows:
            cycle = row.get("cycle")
            if not isinstance(cycle, int):
                continue
            amplification_by_cycle.setdefault(cycle, {})
            entries = float(row.get("entries", 0) or 0)
            puzzles = float(row.get("puzzles", 0) or 0)
            amplification_by_cycle[cycle].setdefault("joy", round(1.0 + entries * 0.05, 2))
            amplification_by_cycle[cycle].setdefault(
                "rage", round(max(0.0, 0.55 - puzzles * 0.04), 2)
            )

    structured: List[Dict[str, Any]] = []
    for cycle_key, group in sorted(rollups["by_cycle"].items(), key=lambda item: int(item[0])):
        cycle = int(cycle_key)
        puzzles: List[Dict[str, Any]] = []
        for entry in group:
            puzzles.append(
                {
                    "id": int(entry["puzzle_id"]),
                    "address": entry["address"],
                    "tags": list(entry.get("tags", [])),
                }
            )
        structured.append(
            {
                "cycle": cycle,
                "puzzles": puzzles,
                "amplification": amplification_by_cycle.get(
                    cycle, {"joy": 1.0, "rage": 0.5}
                ),
            }
        )
    return structured


# ---------- Dashboard JSON (stable shape) ----------
def to_dashboard_json(
    entries: List[Entry],
    rollups: Dict[str, Any],
    harmonics_data: Sequence[Dict[str, Any]],
    safety_data: Sequence[Dict[str, Any]],
    constellations: Sequence[Dict[str, Any]] | None = None,
    *,
    refreshed_at: datetime | None = None,
    voyage_report: VoyageReport | None = None,
) -> Dict[str, Any]:
    safety_flags = [notice["id"] for notice in safety_data if notice.get("flagged")]
    structured_filters = _build_structured_filters(
        rollups,
        harmonics_data,
        voyage_report=voyage_report,
    )
    refreshed_at = refreshed_at or datetime.utcnow()
    payload = dict(
        schema="io.echo.colossus/federated-index@1",
        refreshed_at=refreshed_at.isoformat() + "Z",
        totals=rollups["totals"],
        entries=entries,
        by_cycle=rollups["by_cycle"],
        by_puzzle=rollups["by_puzzle"],
        timeline=rollups["timeline"],
        harmonics=list(harmonics_data),
        safety=dict(notices=list(safety_data), flags=safety_flags),
        structured_filters=structured_filters,
        constellations=list(constellations or []),
    )
    if voyage_report is not None:
        payload["voyage_report"] = voyage_report.to_json()
    return payload


def _render_atom_feed(
    constellations: Sequence[Dict[str, Any]],
    refreshed_at: datetime,
    limit: int = 24,
) -> str:
    """Return an Atom feed describing the latest attestation constellations."""

    feed_id = "tag:kmk142789.github.io,2025:federated-colossus"
    updated_text = refreshed_at.isoformat() + "Z"
    latest = sorted(
        constellations,
        key=lambda node: (
            int(node.get("cycle", 0) or 0),
            str(node.get("digest") or ""),
        ),
        reverse=True,
    )[:limit]

    lines = [
        "<?xml version=\"1.0\" encoding=\"utf-8\"?>",
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        f"  <id>{feed_id}</id>",
        "  <title>Federated Colossus Attestations</title>",
        f"  <updated>{updated_text}</updated>",
        "  <author><name>kmk142789</name></author>",
    ]

    for node in latest:
        puzzle = node.get("puzzle")
        address = node.get("address") or "unknown"
        title = node.get("title") or "Attestation"
        status_icon = node.get("status_icon", "")
        status = node.get("status", "attested")
        cycle = node.get("cycle")
        updated = node.get("updated_at") or updated_text
        narrative = node.get("narrative") or ""
        digest = node.get("digest") or ""

        history = node.get("history") or {}
        link = (
            history.get("pr")
            or history.get("pull_request")
            or history.get("commits")
            or history.get("commit")
            or "https://github.com/kmk142789/kmk142789"
        )

        entry_id = f"{feed_id}:{puzzle}:{address}"
        summary = narrative or (
            f"{status_icon} Puzzle #{puzzle} cycle {cycle} attestation {status}"
        )

        lines.extend(
            [
                "  <entry>",
                f"    <id>{escape(entry_id)}</id>",
                f"    <title>{escape(status_icon + ' ' + title)}</title>",
                f"    <link href=\"{escape(link)}\" />",
                f"    <updated>{escape(str(updated))}</updated>",
                f"    <summary>{escape(summary)}</summary>",
                f"    <content type=\"html\">{escape(f'Address {address} · Digest {digest}')}</content>",
                "  </entry>",
            ]
        )

    lines.append("</feed>")
    return "\n".join(lines) + "\n"


def _update_verification_log(
    log_path: Path,
    json_path: Path,
    rollups: Dict[str, Any],
) -> None:
    """Hash *json_path* and append verification metadata to *log_path*."""

    os.makedirs(log_path.parent, exist_ok=True)
    payload = json_path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    cycles = [int(key) for key in rollups.get("by_cycle", {}).keys()]
    current_cycle = max(cycles) if cycles else 0
    timestamp = datetime.utcnow().isoformat() + "Z"

    previous_hash: Optional[str] = None
    if log_path.exists():
        with open(log_path, "r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                previous_hash = stripped.split(" hash=")[-1]

    with open(log_path, "a", encoding="utf-8") as handle:
        handle.write(f"{timestamp} cycle={current_cycle} hash={digest}\n")

    if previous_hash and previous_hash != digest:
        print("🔔 Continuum Breach: federated index hash drift detected")


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
    default_feed = os.getenv(
        "ECHO_COLLOSSUS_FEED", "docs/feed/federated-colossus.xml"
    )

    parser.add_argument(
        "--feed-out",
        default=default_feed,
        help="Atom feed output path",
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
    constellations = _prepare_constellations(entries)

    voyage_report = _prepare_voyage_report(rollups, harmonics_data, safety_data)
    refreshed_at = datetime.utcnow()

    markdown_output = render_markdown(
        rollups,
        harmonics_data,
        safety_data,
        entries=entries,
        constellations=constellations,
        refreshed_at=refreshed_at,
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
            constellations,
            refreshed_at=refreshed_at,
            voyage_report=voyage_report,
        ),
    )

    print(f"Wrote {args.md_out}")
    print(f"Wrote {args.json_out}")

    if args.feed_out:
        feed_text = _render_atom_feed(constellations, refreshed_at)
        _write_text(args.feed_out, feed_text)
        print(f"Wrote {args.feed_out}")

    verification_log = Path(os.getenv("ECHO_VERIFICATION_LOG", "verification.log"))
    _update_verification_log(verification_log, Path(args.json_out), rollups)
    print(f"Testing ritual complete → {verification_log}")

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
