"""Federated reporting helpers for Colossus and Harmonix artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Sequence
import hashlib
import json

from .graph import FederationGraph


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_search_index(path: Path) -> List[dict]:
    if path.is_dir():
        path = path / "index.json"
    if not path.exists():
        return []
    payload = _load_json(path)
    entries = payload.get("entries", [])
    return [entry for entry in entries if isinstance(entry, dict)]


def _clean_lines(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


@dataclass(slots=True)
class HarmonixSnapshot:
    cycle: int
    glyphs: str
    mythocode: List[str]
    quantum_key: str | None
    narrative: str

    @property
    def mythocode_summary(self) -> str:
        if not self.mythocode:
            return "∅"
        primary = self.mythocode[0]
        remainder = len(self.mythocode) - 1
        if remainder <= 0:
            return primary
        return f"{primary} (+{remainder})"

    @property
    def narrative_excerpt(self) -> str:
        lines = _clean_lines(self.narrative)
        if not lines:
            return ""
        return lines[0][:160]


def _load_harmonix_snapshots(paths: Iterable[Path]) -> Dict[int, HarmonixSnapshot]:
    snapshots: Dict[int, HarmonixSnapshot] = {}
    for source in paths:
        if not source.exists() or not source.is_file():
            continue
        try:
            payload = _load_json(source)
        except json.JSONDecodeError:
            continue
        cycle = payload.get("cycle")
        metadata = payload.get("metadata", payload)
        if not isinstance(cycle, int):
            continue
        glyphs = metadata.get("glyphs") or payload.get("glyphs") or ""
        mythocode = metadata.get("mythocode") or payload.get("mythocode") or []
        quantum_key = metadata.get("quantum_key") or payload.get("quantum_key")
        narrative = metadata.get("narrative") or payload.get("narrative") or ""
        snapshot = HarmonixSnapshot(
            cycle=cycle,
            glyphs=glyphs,
            mythocode=list(mythocode) if isinstance(mythocode, Sequence) else [],
            quantum_key=quantum_key if isinstance(quantum_key, str) else None,
            narrative=str(narrative),
        )
        snapshots[cycle] = snapshot
    return snapshots


@dataclass(slots=True)
class CycleAnchor:
    kind: str
    reference: str
    relationships: List[str]


@dataclass(slots=True)
class CycleReport:
    cycle: int
    timestamp: str
    glyph_signature: str
    anchors: List[CycleAnchor] = field(default_factory=list)
    search_hits: List[str] = field(default_factory=list)
    harmonix: HarmonixSnapshot | None = None

    def label(self) -> str:
        return f"Cycle {self.cycle:05d}"


def _load_cycle_directory(path: Path) -> CycleReport | None:
    dataset_path = path / f"dataset_cycle_{path.name.split('_')[-1]}.json"
    lineage_path = path / f"lineage_map_{path.name.split('_')[-1]}.json"
    if not dataset_path.exists():
        return None
    try:
        dataset = _load_json(dataset_path)
    except json.JSONDecodeError:
        return None
    cycle = dataset.get("cycle")
    timestamp = dataset.get("timestamp", "")
    glyph_signature = dataset.get("glyph_signature", "")
    if not isinstance(cycle, int):
        return None
    anchors: List[CycleAnchor] = []
    if lineage_path.exists():
        try:
            lineage = _load_json(lineage_path)
        except json.JSONDecodeError:
            lineage = {}
        for anchor in lineage.get("anchors", []):
            kind = anchor.get("type", "unknown")
            reference = anchor.get("ref", "")
            relationships = [
                rel for rel in anchor.get("relationships", []) if isinstance(rel, str)
            ]
            anchors.append(
                CycleAnchor(kind=kind, reference=reference, relationships=relationships)
            )
    return CycleReport(
        cycle=cycle,
        timestamp=str(timestamp),
        glyph_signature=str(glyph_signature),
        anchors=anchors,
    )


def _load_cycles(colossus_root: Path) -> Dict[int, CycleReport]:
    cycles: Dict[int, CycleReport] = {}
    if not colossus_root.exists() or not colossus_root.is_dir():
        return cycles
    for directory in sorted(colossus_root.glob("cycle_*/")):
        report = _load_cycle_directory(directory)
        if report is None:
            continue
        cycles[report.cycle] = report
    return cycles


@dataclass(slots=True)
class PuzzleEntry:
    puzzle_id: int
    title: str
    address: str | None
    sha256: str
    source: Path


def _extract_puzzle_id(path: Path) -> int | None:
    name = path.stem
    for segment in name.split("_"):
        if segment.isdigit():
            return int(segment)
    return None


def _extract_title(text: str, default: str) -> str:
    for line in text.splitlines():
        if line.strip().startswith("#"):
            candidate = line.lstrip("#").strip()
            if candidate:
                return candidate
    return default


def _extract_address(text: str) -> str | None:
    fence = "```"
    blocks: List[str] = []
    collecting = False
    buffer: List[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith(fence):
            if collecting:
                if buffer:
                    blocks.append("\n".join(buffer).strip())
                buffer = []
                collecting = False
            else:
                collecting = True
                buffer = []
        elif collecting:
            buffer.append(line)
    if collecting and buffer:
        blocks.append("\n".join(buffer).strip())
    for block in reversed(blocks):
        if block:
            return block.splitlines()[0].strip()
    return None


def _load_puzzles(puzzle_root: Path) -> List[PuzzleEntry]:
    if not puzzle_root.exists() or not puzzle_root.is_dir():
        return []
    entries: List[PuzzleEntry] = []
    for path in sorted(puzzle_root.glob("puzzle_*.md")):
        puzzle_id = _extract_puzzle_id(path)
        if puzzle_id is None:
            continue
        text = path.read_text(encoding="utf-8")
        title = _extract_title(text, f"Puzzle {puzzle_id}")
        address = _extract_address(text)
        sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
        entries.append(
            PuzzleEntry(
                puzzle_id=puzzle_id,
                title=title,
                address=address,
                sha256=sha256,
                source=path,
            )
        )
    entries.sort(key=lambda entry: entry.puzzle_id)
    return entries


def _collect_search_hits(entries: Sequence[dict], tokens: Sequence[str]) -> List[str]:
    hits: Dict[str, None] = {}
    lowered_tokens = [token.lower() for token in tokens if token]
    if not lowered_tokens:
        return []
    for entry in entries:
        haystack = str(entry.get("text", "")).lower()
        node_id = entry.get("node_id")
        if not node_id:
            continue
        if any(token in haystack for token in lowered_tokens):
            hits[node_id] = None
    return sorted(hits.keys())


def _address_catalog(puzzles: Sequence[PuzzleEntry]) -> List[dict]:
    catalog: Dict[str, List[int]] = {}
    for entry in puzzles:
        if not entry.address:
            continue
        catalog.setdefault(entry.address, []).append(entry.puzzle_id)
    payload = []
    for address, puzzle_ids in sorted(catalog.items()):
        payload.append(
            {
                "address": address,
                "puzzles": sorted(set(puzzle_ids)),
                "count": len(set(puzzle_ids)),
            }
        )
    return payload


@dataclass
class FederatedColossusReport:
    generated_at: str
    graph_path: Path
    graph_summary: dict
    search_entry_count: int
    cycles: List[CycleReport]
    puzzles: List[PuzzleEntry]
    addresses: List[dict]

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "graph": {
                "path": str(self.graph_path),
                **self.graph_summary,
            },
            "search_index": {"entries": self.search_entry_count},
            "cycles": [
                {
                    "cycle": cycle.cycle,
                    "timestamp": cycle.timestamp,
                    "glyph_signature": cycle.glyph_signature,
                    "anchors": [
                        {
                            "type": anchor.kind,
                            "reference": anchor.reference,
                            "relationships": list(anchor.relationships),
                        }
                        for anchor in cycle.anchors
                    ],
                    "search_hits": list(cycle.search_hits),
                    "harmonix": (
                        {
                            "glyphs": cycle.harmonix.glyphs,
                            "mythocode_summary": cycle.harmonix.mythocode_summary,
                            "quantum_key": cycle.harmonix.quantum_key,
                            "narrative_excerpt": cycle.harmonix.narrative_excerpt,
                        }
                        if cycle.harmonix
                        else None
                    ),
                }
                for cycle in self.cycles
            ],
            "puzzles": [
                {
                    "puzzle_id": entry.puzzle_id,
                    "title": entry.title,
                    "address": entry.address,
                    "sha256": entry.sha256,
                    "source": str(entry.source),
                }
                for entry in self.puzzles
            ],
            "addresses": list(self.addresses),
        }


def _format_cycle_table(cycles: Sequence[CycleReport]) -> List[str]:
    lines = [
        "| Cycle | Timestamp | Glyph | Harmonix Glyphs | Search Hits |",
        "| --- | --- | --- | --- | --- |",
    ]
    for cycle in cycles:
        harmonix_glyphs = cycle.harmonix.glyphs if cycle.harmonix else "—"
        search_hits = ", ".join(cycle.search_hits) if cycle.search_hits else "—"
        lines.append(
            f"| {cycle.cycle} | {cycle.timestamp} | {cycle.glyph_signature} | {harmonix_glyphs} | {search_hits} |"
        )
    if len(lines) == 2:
        lines.append("| — | — | — | — | — |")
    return lines


def _format_puzzle_table(puzzles: Sequence[PuzzleEntry]) -> List[str]:
    lines = ["| Puzzle | Title | Address | SHA256 |", "| --- | --- | --- | --- |"]
    for entry in puzzles:
        address = entry.address or "—"
        lines.append(
            f"| {entry.puzzle_id} | {entry.title} | {address} | `{entry.sha256[:12]}…` |"
        )
    if len(lines) == 2:
        lines.append("| — | — | — | — |")
    return lines


def _format_address_table(addresses: Sequence[dict]) -> List[str]:
    lines = ["| Address | Puzzle IDs | Count |", "| --- | --- | --- |"]
    for entry in addresses:
        puzzles = ", ".join(str(pid) for pid in entry["puzzles"]) or "—"
        lines.append(
            f"| {entry['address']} | {puzzles} | {entry['count']} |"
        )
    if len(lines) == 2:
        lines.append("| — | — | — |")
    return lines


def _format_cycle_details(cycles: Sequence[CycleReport]) -> List[str]:
    lines: List[str] = []
    for cycle in cycles:
        lines.append(f"### Cycle {cycle.cycle:05d}")
        lines.append("")
        lines.append(f"- **Timestamp**: {cycle.timestamp or '—'}")
        lines.append(f"- **Glyph Signature**: `{cycle.glyph_signature}`")
        if cycle.harmonix:
            lines.append(
                f"- **Harmonix Mythocode**: `{cycle.harmonix.mythocode_summary}`"
            )
            if cycle.harmonix.quantum_key:
                lines.append(
                    f"- **Harmonix Quantum Key**: `{cycle.harmonix.quantum_key}`"
                )
        else:
            lines.append("- **Harmonix Mythocode**: _not captured_")
        if cycle.anchors:
            lines.append("- **Anchors**:")
            for anchor in cycle.anchors:
                rels = ", ".join(anchor.relationships) if anchor.relationships else "—"
                lines.append(
                    f"  - `{anchor.kind}` → `{anchor.reference}` (links: {rels})"
                )
        if cycle.search_hits:
            lines.append("- **Search Hits**:")
            for node in cycle.search_hits:
                lines.append(f"  - {node}")
        lines.append("")
    return lines


def _format_markdown(report: FederatedColossusReport) -> str:
    lines = ["# Federated Colossus Index", ""]
    lines.append(f"- **Generated**: {report.generated_at}")
    lines.append(f"- **Graph Path**: `{report.graph_path}`")
    lines.append(f"- **Universes**: {report.graph_summary['universes']}")
    lines.append(f"- **Artifacts**: {report.graph_summary['artifacts']}")
    lines.append(f"- **Edges**: {report.graph_summary['edges']}")
    lines.append(f"- **Search Entries**: {report.search_entry_count}")
    lines.append("")
    lines.append("## Cycle Overview")
    lines.append("")
    lines.extend(_format_cycle_table(report.cycles))
    lines.append("")
    lines.extend(_format_cycle_details(report.cycles))
    lines.append("## Puzzle Mapping")
    lines.append("")
    lines.extend(_format_puzzle_table(report.puzzles))
    lines.append("")
    lines.append("## Derived Address Catalog")
    lines.append("")
    lines.extend(_format_address_table(report.addresses))
    lines.append("")
    return "\n".join(lines)


def generate_federated_colossus_report(
    *,
    graph_path: Path,
    search_index_path: Path,
    colossus_root: Path,
    puzzle_root: Path,
    harmonix_sources: Iterable[Path] | None = None,
    markdown_path: Path,
    json_path: Path,
) -> FederatedColossusReport:
    graph = FederationGraph.load(graph_path)
    search_entries = _load_search_index(search_index_path)
    harmonix_sources = list(harmonix_sources or [])
    if not harmonix_sources:
        harmonix_sources = list(Path.cwd().glob("*.echo.json"))
    harmonix = _load_harmonix_snapshots(harmonix_sources)
    cycles = _load_cycles(colossus_root)
    search_tokens: Dict[int, List[str]] = {
        cycle: [
            f"cycle_{cycle:05d}",
            f"colossus {cycle:05d}",
            str(report.glyph_signature),
        ]
        for cycle, report in cycles.items()
    }
    for cycle, report in cycles.items():
        report.search_hits = _collect_search_hits(search_entries, search_tokens.get(cycle, []))
        if cycle in harmonix:
            report.harmonix = harmonix[cycle]
    puzzle_entries = _load_puzzles(puzzle_root)
    addresses = _address_catalog(puzzle_entries)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    graph_summary = {
        "universes": len(graph.universes),
        "artifacts": len(graph.artifacts),
        "edges": len(graph.edges),
    }
    ordered_cycles = [cycles[key] for key in sorted(cycles)]
    report = FederatedColossusReport(
        generated_at=generated_at,
        graph_path=graph_path,
        graph_summary=graph_summary,
        search_entry_count=len(search_entries),
        cycles=ordered_cycles,
        puzzles=puzzle_entries,
        addresses=addresses,
    )
    markdown_path.write_text(_format_markdown(report) + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


__all__ = ["generate_federated_colossus_report", "FederatedColossusReport"]

