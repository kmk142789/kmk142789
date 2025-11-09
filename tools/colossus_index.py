"""Federate Colossus artifacts into a consolidated Markdown index.

This helper parses the existing Colossus cycle artifacts along with
supporting federation signals (pulse, ledger anchors, glyph narratives,
and Satoshi puzzle reconstructions) to emit a human readable index.

The module exposes composable helpers so the behaviour can be unit tested
and reused by other automation.  Executing the module as a script writes
the generated index to the provided ``--output`` path.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import re
from typing import List, MutableMapping, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
COLOSSUS_ROOT = REPO_ROOT / "colossus"
PUZZLE_SOLUTIONS_ROOT = REPO_ROOT / "puzzle_solutions"

def _load_curated_puzzle_ids() -> set[int]:
    """Extract curated puzzle identifiers from the master index."""

    table_path = REPO_ROOT / "colossus_master_index.md"
    if not table_path.exists():
        return set()
    ids: set[int] = set()
    for line in table_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith('|'):
            continue
        parts = [segment.strip() for segment in stripped.strip('|').split('|')]
        if not parts or not parts[0].isdigit():
            continue
        try:
            ids.add(int(parts[0]))
        except ValueError:  # pragma: no cover - defensive
            continue
    return ids

CURATED_PUZZLE_IDS = _load_curated_puzzle_ids()

# Only a subset of the historic Bitcoin puzzles have been reconstructed and
# vetted within the Colossus index.  The attestation set begins with puzzle 200
# and later entries, so we suppress older files when building the summary even
# if they fall within the caller provided range.  This keeps the generated
# tables aligned with the human curated ``colossus_master_index`` output.
MIN_DOCUMENTED_PUZZLE = 200
PULSE_PATH = REPO_ROOT / "pulse.json"
PULSE_HISTORY_PATH = REPO_ROOT / "pulse_history.json"
LEDGER_PATH = REPO_ROOT / "genesis_ledger" / "ledger.jsonl"


@dataclass(slots=True)
class CycleSummary:
    """Key facts extracted from a Colossus cycle."""

    cycle: int
    timestamp: str
    glyph_signature: str
    puzzle_path: Path
    puzzle_title: str
    puzzle_excerpt: str
    dataset_path: Path
    dataset_checksum: Optional[int]
    harmonics: Sequence[int]
    anchors: Sequence[str]
    narrative_excerpt: str
    verify_path: Path

    def dataset_stats(self) -> str:
        if not self.harmonics:
            return "count=0"
        count = len(self.harmonics)
        minimum = min(self.harmonics)
        maximum = max(self.harmonics)
        mean = sum(self.harmonics) / count
        checksum = f" checksum={self.dataset_checksum}" if self.dataset_checksum is not None else ""
        return f"count={count} min={minimum} max={maximum} mean={mean:.1f}{checksum}"


@dataclass(slots=True)
class PulseSummary:
    status: str
    branch_anchor: Optional[str]
    notes: Optional[str]
    history_entries: int
    latest_event: Optional[str]


@dataclass(slots=True)
class AnchorSummary:
    total_entries: int
    latest_seq: Optional[int]
    latest_type: Optional[str]
    latest_timestamp: Optional[str]


@dataclass(slots=True)
class PuzzleSolutionSummary:
    puzzle: int
    address: str
    hash160: Optional[str]
    source_path: Path


@dataclass(slots=True)
class GlyphSummary:
    unique_signatures: Sequence[str]
    highlights: Sequence[str]


@dataclass(slots=True)
class MasterIndexContext:
    artifact_type: str
    puzzle_range: tuple[int, int]
    federation_sources: Sequence[str]
    cycles: Sequence[CycleSummary]
    puzzle_solutions: Sequence[PuzzleSolutionSummary]
    pulse: Optional[PulseSummary]
    anchor: Optional[AnchorSummary]
    glyph: GlyphSummary


def parse_puzzle_range(text: str) -> tuple[int, int]:
    """Parse a ``min-max`` puzzle range string."""

    if "-" not in text:
        raise ValueError("puzzle range must be of the form <min>-<max>")
    start_text, end_text = text.split("-", 1)
    try:
        start = int(start_text)
        end = int(end_text)
    except ValueError as exc:  # pragma: no cover - defensive branch
        raise ValueError("puzzle range bounds must be integers") from exc
    if start <= 0 or end <= 0:
        raise ValueError("puzzle range bounds must be positive")
    if end < start:
        raise ValueError("puzzle range upper bound must be greater than or equal to lower bound")
    return start, end


def parse_federation_sources(text: str) -> List[str]:
    """Parse a comma-separated federation source string."""

    sources: List[str] = []
    for entry in text.split(","):
        item = entry.strip()
        if item and item not in sources:
            sources.append(item)
    return sources


def _parse_front_matter(lines: Sequence[str]) -> tuple[MutableMapping[str, str], Sequence[str]]:
    if not lines or lines[0].strip() != "---":
        return {}, lines
    data: MutableMapping[str, str] = {}
    index = 1
    while index < len(lines):
        raw = lines[index].strip()
        if raw == "---":
            break
        if raw and ":" in raw:
            key, value = raw.split(":", 1)
            data[key.strip()] = value.strip().strip('"')
        index += 1
    return data, lines[index + 1 :]


def _first_paragraph(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("-") and ":" in stripped:
            continue
        return stripped
    return ""


def _relative(path: Path) -> Path:
    try:
        return path.relative_to(REPO_ROOT)
    except ValueError:  # pragma: no cover - defensive fallback
        return path


def load_colossus_cycles(root: Path = COLOSSUS_ROOT) -> List[CycleSummary]:
    """Load Colossus cycle metadata from ``root``."""

    if not root.exists():
        return []
    summaries: List[CycleSummary] = []
    for cycle_dir in sorted(p for p in root.iterdir() if p.is_dir() and p.name.startswith("cycle_")):
        match = re.search(r"(\d+)$", cycle_dir.name)
        if not match:
            continue
        cycle_id = int(match.group(1))
        puzzle_path = cycle_dir / f"puzzle_cycle_{cycle_id:05d}.md"
        dataset_path = cycle_dir / f"dataset_cycle_{cycle_id:05d}.json"
        lineage_path = cycle_dir / f"lineage_map_{cycle_id:05d}.json"
        narrative_path = cycle_dir / f"glyph_narrative_{cycle_id:05d}.md"
        verify_path = cycle_dir / f"verify_cycle_{cycle_id:05d}.py"

        puzzle_lines = puzzle_path.read_text(encoding="utf-8").splitlines()
        front_matter, body_lines = _parse_front_matter(puzzle_lines)
        puzzle_body = "\n".join(body_lines)
        puzzle_title_match = re.search(r"^#\s+(.+)$", puzzle_body, re.MULTILINE)
        puzzle_title = puzzle_title_match.group(1).strip() if puzzle_title_match else f"Cycle {cycle_id:05d}"
        puzzle_excerpt = _first_paragraph(puzzle_body)

        dataset_payload = json.loads(dataset_path.read_text(encoding="utf-8"))
        harmonics = list(dataset_payload.get("harmonics", []))
        checksum = dataset_payload.get("checksum")
        timestamp = dataset_payload.get("timestamp") or front_matter.get("timestamp", "")
        glyph_signature = dataset_payload.get("glyph_signature") or front_matter.get("glyph_signature", "")

        lineage_payload = json.loads(lineage_path.read_text(encoding="utf-8"))
        anchors = [
            f"{entry.get('type', 'unknown')} → {entry.get('ref', 'unknown')}"
            for entry in lineage_payload.get("anchors", [])
        ]

        narrative_text = narrative_path.read_text(encoding="utf-8")
        narrative_excerpt = _first_paragraph(narrative_text)

        summaries.append(
            CycleSummary(
                cycle=cycle_id,
                timestamp=timestamp,
                glyph_signature=glyph_signature,
                puzzle_path=_relative(puzzle_path),
                puzzle_title=puzzle_title,
                puzzle_excerpt=puzzle_excerpt,
                dataset_path=_relative(dataset_path),
                dataset_checksum=checksum if isinstance(checksum, int) else None,
                harmonics=harmonics,
                anchors=anchors,
                narrative_excerpt=narrative_excerpt,
                verify_path=_relative(verify_path),
            )
        )
    return sorted(summaries, key=lambda entry: entry.cycle)


_HASH160_RE = re.compile(r"\*\*(?:Extracted|Provided) hash160\*\*: `([0-9a-f]{40})`")
_ADDRESS_RE = re.compile(r"\*\*Base58Check encoding\*\*: `([1-9A-HJ-NP-Za-km-z]{26,})`")
_CODE_BLOCK_RE = re.compile(r"```\s*\n([1-9A-HJ-NP-Za-km-z]{26,})\s*\n```", re.MULTILINE)


def collect_puzzle_solutions(min_puzzle: int, max_puzzle: int, root: Path = PUZZLE_SOLUTIONS_ROOT) -> List[PuzzleSolutionSummary]:
    """Collect puzzle solution summaries within the provided range."""

    if not root.exists():
        return []
    summaries: List[PuzzleSolutionSummary] = []
    effective_min = max(min_puzzle, MIN_DOCUMENTED_PUZZLE)
    for path in root.glob("puzzle_*.md"):
        if CURATED_PUZZLE_IDS and int(path.stem.split("_")[1]) not in CURATED_PUZZLE_IDS:
            continue
        match = re.search(r"puzzle_(\d+)\.md$", path.name)
        if not match:
            continue
        puzzle_id = int(match.group(1))
        if puzzle_id < effective_min or puzzle_id > max_puzzle:
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        front_matter, body_lines = _parse_front_matter(lines)
        status = front_matter.get("status", "").strip().lower()
        if status and status not in {"documented", "attested", "verified"}:
            continue
        if not status:
            # Require explicit opt-in so only vetted solutions appear in the
            # generated index.  Files without a documented status remain
            # accessible in the repository but are excluded from the summary.
            continue
        text = "\n".join(body_lines)
        hash_match = _HASH160_RE.search(text)
        address_match = _ADDRESS_RE.search(text)
        address = address_match.group(1) if address_match else None
        if address is None:
            block_match = _CODE_BLOCK_RE.search(text)
            address = block_match.group(1) if block_match else ""
        hash160 = hash_match.group(1) if hash_match else None
        summaries.append(
            PuzzleSolutionSummary(
                puzzle=puzzle_id,
                address=address or "",
                hash160=hash160,
                source_path=_relative(path),
            )
        )
    return sorted(summaries, key=lambda entry: entry.puzzle)


def load_pulse_summary(
    pulse_path: Path = PULSE_PATH,
    history_path: Path = PULSE_HISTORY_PATH,
) -> Optional[PulseSummary]:
    if not pulse_path.exists():
        return None
    payload = json.loads(pulse_path.read_text(encoding="utf-8"))
    status = str(payload.get("status", "unknown"))
    branch_anchor = payload.get("branch_anchor")
    notes = payload.get("notes")
    history_entries = 0
    latest_event: Optional[str] = None
    if history_path.exists():
        history = json.loads(history_path.read_text(encoding="utf-8"))
        history_entries = len(history)
        if history:
            latest = max(history, key=lambda item: item.get("timestamp", 0))
            ts = latest.get("timestamp")
            try:
                iso = datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()
            except (TypeError, ValueError):  # pragma: no cover - defensive branch
                iso = None
            latest_event = f"{iso} — {latest.get('message')}" if iso else latest.get("message")
    return PulseSummary(
        status=status,
        branch_anchor=branch_anchor,
        notes=notes,
        history_entries=history_entries,
        latest_event=latest_event,
    )


def load_anchor_summary(ledger_path: Path = LEDGER_PATH) -> Optional[AnchorSummary]:
    if not ledger_path.exists():
        return None
    entries: List[dict] = []
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:  # pragma: no cover - ignore malformed lines
            continue
    if not entries:
        return AnchorSummary(total_entries=0, latest_seq=None, latest_type=None, latest_timestamp=None)
    latest = max(entries, key=lambda item: item.get("seq", -1))
    return AnchorSummary(
        total_entries=len(entries),
        latest_seq=latest.get("seq"),
        latest_type=latest.get("type"),
        latest_timestamp=latest.get("ts"),
    )


def summarise_glyphs(cycles: Sequence[CycleSummary]) -> GlyphSummary:
    signatures = []
    highlights = []
    seen = set()
    for cycle in cycles:
        if cycle.glyph_signature and cycle.glyph_signature not in seen:
            signatures.append(cycle.glyph_signature)
            seen.add(cycle.glyph_signature)
        excerpt = cycle.narrative_excerpt or cycle.puzzle_excerpt
        if excerpt:
            highlights.append(f"Cycle {cycle.cycle:05d}: {excerpt}")
    return GlyphSummary(unique_signatures=signatures, highlights=highlights)


def build_master_index(context: MasterIndexContext) -> str:
    min_puzzle, max_puzzle = context.puzzle_range
    span = max_puzzle - min_puzzle + 1
    lines: List[str] = []
    lines.append("# Colossus Master Index")
    lines.append("")
    lines.append(f"- Artifact type: **{context.artifact_type}**")
    lines.append(f"- Puzzle range: **{min_puzzle}–{max_puzzle}** (span {span:,} puzzles)")
    if context.puzzle_solutions:
        first = context.puzzle_solutions[0].puzzle
        last = context.puzzle_solutions[-1].puzzle
        lines.append(
            f"- Range coverage: {len(context.puzzle_solutions)} documented puzzle(s) — earliest #{first}, latest #{last}."
        )
    else:
        lines.append("- Range coverage: no documented puzzle solutions in the requested range (yet).")
    if context.federation_sources:
        joined = ", ".join(context.federation_sources)
        lines.append(f"- Federation streams: {joined}")
    lines.append("")

    if context.cycles:
        lines.append("## Colossus Cycles")
        lines.append("")
        lines.append("| Cycle | Timestamp | Glyph | Puzzle | Dataset | Anchors | Verify |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for cycle in context.cycles:
            puzzle_ref = f"`{cycle.puzzle_path}`"
            dataset_ref = f"`{cycle.dataset_path}`\n{cycle.dataset_stats()}"
            anchors = "<br />".join(cycle.anchors) if cycle.anchors else "—"
            verify_ref = f"`{cycle.verify_path}`"
            glyph = cycle.glyph_signature or "—"
            lines.append(
                "| {cycle} | {timestamp} | {glyph} | {puzzle} | {dataset} | {anchors} | {verify} |".format(
                    cycle=f"{cycle.cycle:05d}",
                    timestamp=cycle.timestamp or "—",
                    glyph=glyph,
                    puzzle=puzzle_ref,
                    dataset=dataset_ref,
                    anchors=anchors,
                    verify=verify_ref,
                )
            )
        lines.append("")
        lines.append("### Cycle Highlights")
        lines.append("")
        for cycle in context.cycles:
            if cycle.puzzle_excerpt:
                lines.append(f"- **Cycle {cycle.cycle:05d}** — {cycle.puzzle_excerpt}")
        lines.append("")
    else:
        lines.append("## Colossus Cycles")
        lines.append("")
        lines.append("No Colossus cycles were discovered in the repository.")
        lines.append("")

    if context.puzzle_solutions:
        lines.append("## Satoshi Reconstruction — Puzzle Solutions")
        lines.append("")
        lines.append("| Puzzle | Address | HASH160 | Source |")
        lines.append("| --- | --- | --- | --- |")
        for entry in context.puzzle_solutions:
            hash160 = entry.hash160 or "—"
            lines.append(
                f"| {entry.puzzle} | `{entry.address}` | `{hash160}` | `{entry.source_path}` |"
            )
        lines.append("")
    elif "satoshi-reconstruction" in context.federation_sources:
        lines.append("## Satoshi Reconstruction — Puzzle Solutions")
        lines.append("")
        lines.append("No documented puzzles were located in the requested range.")
        lines.append("")

    if "pulse" in context.federation_sources and context.pulse:
        lines.append("## Pulse Federation Signal")
        lines.append("")
        lines.append(f"- Status: **{context.pulse.status}**")
        if context.pulse.branch_anchor:
            lines.append(f"- Branch anchor: {context.pulse.branch_anchor}")
        if context.pulse.notes:
            lines.append(f"- Notes: {context.pulse.notes}")
        lines.append(f"- Recorded history entries: {context.pulse.history_entries}")
        if context.pulse.latest_event:
            lines.append(f"- Latest event: {context.pulse.latest_event}")
        lines.append("")

    if "anchor" in context.federation_sources and context.anchor:
        lines.append("## Anchor Ledger Summary")
        lines.append("")
        lines.append(f"- Total entries: {context.anchor.total_entries}")
        if context.anchor.latest_seq is not None:
            lines.append(
                f"- Latest sequence {context.anchor.latest_seq} ({context.anchor.latest_type}) at {context.anchor.latest_timestamp}"
            )
        lines.append("")

    if "glyph" in context.federation_sources:
        lines.append("## Glyph Highlights")
        lines.append("")
        if context.glyph.unique_signatures:
            signatures = ", ".join(context.glyph.unique_signatures)
            lines.append(f"- Unique glyph signatures: {signatures}")
        for highlight in context.glyph.highlights:
            lines.append(f"- {highlight}")
        if not context.glyph.unique_signatures and not context.glyph.highlights:
            lines.append("No glyph narratives available.")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def build_context(
    *,
    artifact_type: str,
    puzzle_range: tuple[int, int],
    federation_sources: Sequence[str],
    cycles: Optional[Sequence[CycleSummary]] = None,
    puzzle_solutions: Optional[Sequence[PuzzleSolutionSummary]] = None,
    pulse: Optional[PulseSummary] = None,
    anchor: Optional[AnchorSummary] = None,
    glyph: Optional[GlyphSummary] = None,
) -> MasterIndexContext:
    resolved_cycles = list(cycles or [])
    glyph_summary = glyph or summarise_glyphs(resolved_cycles)
    return MasterIndexContext(
        artifact_type=artifact_type,
        puzzle_range=puzzle_range,
        federation_sources=list(federation_sources),
        cycles=resolved_cycles,
        puzzle_solutions=list(puzzle_solutions or []),
        pulse=pulse,
        anchor=anchor,
        glyph=glyph_summary,
    )


def _cli(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Federate and expand the Colossus index")
    parser.add_argument("--puzzle-range", required=True, help="Puzzle range to include (min-max)")
    parser.add_argument("--federation", required=True, help="Comma separated federation sources")
    parser.add_argument("--artifact-type", required=True, help="Artifact type label for the index")
    parser.add_argument("--output", required=True, type=Path, help="Output Markdown path")
    parser.add_argument("--colossus-root", type=Path, default=COLOSSUS_ROOT)
    parser.add_argument("--puzzle-root", type=Path, default=PUZZLE_SOLUTIONS_ROOT)
    parser.add_argument("--pulse", type=Path, default=PULSE_PATH)
    parser.add_argument("--pulse-history", dest="pulse_history", type=Path, default=PULSE_HISTORY_PATH)
    parser.add_argument("--ledger", type=Path, default=LEDGER_PATH)

    args = parser.parse_args(argv)

    puzzle_range = parse_puzzle_range(args.puzzle_range)
    federation_sources = parse_federation_sources(args.federation)
    cycles = load_colossus_cycles(args.colossus_root)
    puzzle_solutions = collect_puzzle_solutions(
        puzzle_range[0], puzzle_range[1], root=args.puzzle_root
    )
    pulse = load_pulse_summary(args.pulse, args.pulse_history)
    anchor = load_anchor_summary(args.ledger)
    glyph = summarise_glyphs(cycles)

    context = build_context(
        artifact_type=args.artifact_type,
        puzzle_range=puzzle_range,
        federation_sources=federation_sources,
        cycles=cycles,
        puzzle_solutions=puzzle_solutions,
        pulse=pulse,
        anchor=anchor,
        glyph=glyph,
    )
    content = build_master_index(context)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8")
    return 0


def main() -> None:
    raise SystemExit(_cli())


if __name__ == "__main__":  # pragma: no cover - CLI execution
    main()
