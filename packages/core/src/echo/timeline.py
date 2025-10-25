"""Build aggregated cycle timelines joining pulses, snapshots, and puzzle data."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from typing import Dict, List, Mapping, MutableMapping, Sequence, Tuple


def _ensure_timezone(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _parse_iso_timestamp(value: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    return _ensure_timezone(dt)


def _normalise_message(message: str) -> str:
    text = message or ""
    while text and not text[0].isalnum():
        text = text[1:]
    return text.strip()


def _pulse_origin(message: str) -> str:
    segments = [segment for segment in _normalise_message(message).split(":") if segment]
    if len(segments) >= 2:
        return segments[1]
    if segments:
        return segments[0]
    return "unknown"


def _normalise_doc_path(path: str) -> str:
    return str(Path(path)).replace("\\", "/")


def _coerce_path(project_root: Path, candidate: Path | str | None, default: Path) -> Path:
    if candidate is None:
        path = default
    else:
        path = Path(candidate)
        if not path.is_absolute():
            path = project_root / path
    return path


def _list_commit_paths(commit_sha: str, *, cwd: Path) -> set[Path]:
    if not commit_sha:
        return set()
    try:
        completed = subprocess.run(
            [
                "git",
                "show",
                "--pretty=format:",
                "--name-only",
                commit_sha,
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=cwd,
        )
    except FileNotFoundError:
        return set()
    if completed.returncode != 0:
        return set()
    paths: set[Path] = set()
    for line in completed.stdout.splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        paths.add(Path(candidate))
    return paths


@dataclass(frozen=True)
class PulseEvent:
    """Single entry from ``pulse_history.json``."""

    timestamp: float
    message: str
    hash: str

    @property
    def iso(self) -> str:
        return datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat()

    def to_dict(self) -> Mapping[str, object]:
        return {
            "timestamp": self.timestamp,
            "iso": self.iso,
            "message": self.message,
            "hash": self.hash,
        }


@dataclass(frozen=True)
class PuzzleEntry:
    """Puzzle index metadata linked to a commit."""

    id: int
    title: str
    doc: str
    script_type: str
    address: str
    status: str

    def to_dict(self) -> Mapping[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "doc": self.doc,
            "script_type": self.script_type,
            "address": self.address,
            "status": self.status,
        }


@dataclass(frozen=True)
class CycleSnapshot:
    """Amplification snapshot describing a cycle."""

    cycle: int
    index: float
    timestamp: datetime
    commit_sha: str
    metrics: Mapping[str, float]

    def to_dict(self) -> Mapping[str, object]:
        return {
            "cycle": self.cycle,
            "index": self.index,
            "timestamp": self.timestamp.isoformat(),
            "commit_sha": self.commit_sha,
            "metrics": dict(self.metrics),
        }


@dataclass(frozen=True)
class CycleTimelineEntry:
    """Aggregated relationship between a cycle, pulses, and puzzle activity."""

    snapshot: CycleSnapshot
    pulses: Tuple[PulseEvent, ...]
    puzzles: Tuple[PuzzleEntry, ...]
    pulse_summary: Mapping[str, int]
    window_start: datetime | None
    window_end: datetime

    def to_dict(self) -> Mapping[str, object]:
        return {
            "snapshot": self.snapshot.to_dict(),
            "pulses": [event.to_dict() for event in self.pulses],
            "pulse_summary": dict(self.pulse_summary),
            "puzzles": [puzzle.to_dict() for puzzle in self.puzzles],
            "window": {
                "start": self.window_start.isoformat() if self.window_start else None,
                "end": self.window_end.isoformat(),
            },
            "markdown": self.to_markdown(),
        }

    def to_markdown(self) -> str:
        lines: List[str] = []
        lines.append(
            f"### Cycle {self.snapshot.cycle} — index {self.snapshot.index:.2f}"
        )
        lines.append(f"* Timestamp: {self.snapshot.timestamp.isoformat()}")
        lines.append(f"* Commit: `{self.snapshot.commit_sha}`")
        lines.append(f"* Pulse events: {len(self.pulses)}")
        if self.pulse_summary:
            summary_bits = ", ".join(
                f"{key}×{value}"
                for key, value in sorted(
                    self.pulse_summary.items(), key=lambda item: (-item[1], item[0])
                )
            )
            lines.append(f"* Pulse breakdown: {summary_bits}")
        else:
            lines.append("* Pulse breakdown: none recorded")
        if self.puzzles:
            lines.append("* Puzzle index impact:")
            for puzzle in self.puzzles:
                lines.append(
                    f"  * Puzzle #{puzzle.id} — {puzzle.title} (`{puzzle.doc}`)"
                )
        else:
            lines.append("* Puzzle index impact: none detected")
        if self.snapshot.metrics:
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            for key, value in sorted(self.snapshot.metrics.items()):
                lines.append(f"| {key.replace('_', ' ').title()} | {value:.2f} |")
        if self.pulses:
            lines.append("")
            lines.append("| Pulse | Message |")
            lines.append("|-------|---------|")
            for event in self.pulses:
                safe_message = event.message.replace("|", "\\|")
                lines.append(f"| {event.iso} | {safe_message} |")
        return "\n".join(lines)


def _load_pulse_history(path: Path) -> List[PulseEvent]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    events: List[PulseEvent] = []
    for item in payload:
        if not isinstance(item, MutableMapping):
            continue
        timestamp = item.get("timestamp")
        message = item.get("message", "")
        pulse_hash = item.get("hash", "")
        if not isinstance(timestamp, (int, float)):
            continue
        events.append(
            PulseEvent(timestamp=float(timestamp), message=str(message), hash=str(pulse_hash))
        )
    events.sort(key=lambda event: event.timestamp)
    return events


def _load_amplify_log(path: Path) -> List[CycleSnapshot]:
    if not path.exists():
        return []
    snapshots: List[CycleSnapshot] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            cycle = payload.get("cycle")
            index = payload.get("index")
            timestamp_str = payload.get("timestamp")
            commit_sha = payload.get("commit_sha", "")
            metrics_payload = payload.get("metrics", {})
            if not isinstance(cycle, int) or not isinstance(index, (int, float)):
                continue
            if not isinstance(timestamp_str, str):
                continue
            metrics: Dict[str, float] = {}
            if isinstance(metrics_payload, Mapping):
                for key, value in metrics_payload.items():
                    if isinstance(value, (int, float)):
                        metrics[str(key)] = float(value)
            snapshots.append(
                CycleSnapshot(
                    cycle=int(cycle),
                    index=float(index),
                    timestamp=_parse_iso_timestamp(timestamp_str),
                    commit_sha=str(commit_sha),
                    metrics=metrics,
                )
            )
    snapshots.sort(key=lambda snap: snap.cycle)
    return snapshots


def _load_puzzle_index(path: Path) -> List[PuzzleEntry]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    items = payload.get("puzzles", [])
    entries: List[PuzzleEntry] = []
    if not isinstance(items, Sequence):
        return entries
    for item in items:
        if not isinstance(item, Mapping):
            continue
        try:
            puzzle_id = int(item["id"])
            doc = str(item["doc"])
        except (KeyError, ValueError, TypeError):
            continue
        entries.append(
            PuzzleEntry(
                id=puzzle_id,
                title=str(item.get("title", f"Puzzle #{puzzle_id}")),
                doc=_normalise_doc_path(doc),
                script_type=str(item.get("script_type", "unknown")),
                address=str(item.get("address", "")),
                status=str(item.get("status", "unknown")),
            )
        )
    return entries


def _summarise_pulses(pulses: Sequence[PulseEvent]) -> Mapping[str, int]:
    counts: Dict[str, int] = {}
    for event in pulses:
        origin = _pulse_origin(event.message)
        counts[origin] = counts.get(origin, 0) + 1
    return dict(sorted(counts.items()))


def build_cycle_timeline(
    *,
    project_root: Path | None = None,
    amplify_log: Path | str | None = None,
    pulse_history: Path | str | None = None,
    puzzle_index: Path | str | None = None,
    limit: int | None = None,
) -> List[CycleTimelineEntry]:
    root = Path(project_root) if project_root is not None else Path.cwd()
    amplify_path = _coerce_path(root, amplify_log, root / "state" / "amplify_log.jsonl")
    pulse_path = _coerce_path(root, pulse_history, root / "pulse_history.json")
    puzzle_path = _coerce_path(root, puzzle_index, root / "data" / "puzzle_index.json")

    pulses = _load_pulse_history(pulse_path)
    snapshots = _load_amplify_log(amplify_path)
    puzzles = _load_puzzle_index(puzzle_path)
    puzzle_lookup = {
        _normalise_doc_path(entry.doc): entry for entry in puzzles
    }

    entries: List[CycleTimelineEntry] = []
    if not snapshots:
        return entries

    previous_timestamp: datetime | None = None
    for snapshot in snapshots:
        start_ts = previous_timestamp
        end_ts = snapshot.timestamp
        start_epoch = start_ts.timestamp() if start_ts else None
        end_epoch = end_ts.timestamp()
        cycle_pulses = [
            event
            for event in pulses
            if (start_epoch is None or event.timestamp > start_epoch)
            and event.timestamp <= end_epoch
        ]
        commit_paths = _list_commit_paths(snapshot.commit_sha, cwd=root)
        linked: Dict[int, PuzzleEntry] = {}
        for path in commit_paths:
            key = _normalise_doc_path(str(path))
            puzzle = puzzle_lookup.get(key)
            if puzzle:
                linked[puzzle.id] = puzzle
        entry = CycleTimelineEntry(
            snapshot=snapshot,
            pulses=tuple(cycle_pulses),
            puzzles=tuple(sorted(linked.values(), key=lambda item: item.id)),
            pulse_summary=_summarise_pulses(cycle_pulses),
            window_start=start_ts,
            window_end=end_ts,
        )
        entries.append(entry)
        previous_timestamp = end_ts

    if limit is not None and limit > 0:
        entries = entries[-limit:]
    return entries


def render_markdown(entries: Sequence[CycleTimelineEntry]) -> str:
    generated = datetime.now(timezone.utc).isoformat()
    lines = ["# Echo Cycle Timeline", "", f"Generated: {generated}", ""]
    for entry in entries:
        lines.append(entry.to_markdown())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def refresh_cycle_timeline(
    *,
    project_root: Path | None = None,
    amplify_log: Path | str | None = None,
    pulse_history: Path | str | None = None,
    puzzle_index: Path | str | None = None,
    output_dir: Path | str | None = None,
    limit: int | None = None,
) -> List[CycleTimelineEntry]:
    root = Path(project_root) if project_root is not None else Path.cwd()
    entries = build_cycle_timeline(
        project_root=root,
        amplify_log=amplify_log,
        pulse_history=pulse_history,
        puzzle_index=puzzle_index,
        limit=limit,
    )
    if not entries:
        return entries
    out_dir = Path(output_dir) if output_dir is not None else root / "artifacts"
    if not out_dir.is_absolute():
        out_dir = root / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "cycles": [entry.to_dict() for entry in entries],
        "stats": {
            "cycle_count": len(entries),
            "latest_cycle": entries[-1].snapshot.cycle if entries else None,
        },
    }
    json_path = out_dir / "cycle_timeline.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    markdown_path = out_dir / "cycle_timeline.md"
    markdown_path.write_text(render_markdown(entries), encoding="utf-8")

    return entries


__all__ = [
    "build_cycle_timeline",
    "CycleTimelineEntry",
    "CycleSnapshot",
    "PulseEvent",
    "PuzzleEntry",
    "refresh_cycle_timeline",
    "render_markdown",
]
