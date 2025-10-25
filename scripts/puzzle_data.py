"""Shared helpers for puzzle lineage tooling."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / "data" / "puzzle_index.json"


@dataclass(frozen=True)
class Puzzle:
    """Representation of a puzzle entry from the shared index."""

    id: int
    title: str
    doc: str
    script_type: str
    hash160: str
    address: str
    status: str

    @property
    def doc_path(self) -> Path:
        return ROOT / self.doc


def load_index(path: Optional[Path] = None) -> Dict[str, object]:
    """Load the shared puzzle index JSON."""

    target = Path(path) if path else DEFAULT_INDEX
    with target.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload


def load_puzzles(path: Optional[Path] = None) -> List[Puzzle]:
    """Return puzzle dataclasses sorted by identifier."""

    payload = load_index(path)
    puzzles: List[Puzzle] = [
        Puzzle(
            id=entry["id"],
            title=entry.get("title", f"Puzzle #{entry['id']}") if isinstance(entry.get("title"), str) else f"Puzzle #{entry['id']}",
            doc=entry["doc"],
            script_type=entry["script_type"],
            hash160=entry["hash160"],
            address=entry["address"],
            status=entry.get("status", "unknown"),
        )
        for entry in payload.get("puzzles", [])
    ]
    return sorted(puzzles, key=lambda item: item.id)


def build_lookup(puzzles: Iterable[Puzzle]) -> Dict[int, Puzzle]:
    """Create an id→puzzle dictionary."""

    return {puzzle.id: puzzle for puzzle in puzzles}


def lineage_links(path: Optional[Path] = None) -> List[Dict[str, object]]:
    """Return the static lineage links from the dataset."""

    payload = load_index(path)
    links = payload.get("lineage_links", [])
    cleaned: List[Dict[str, object]] = []
    for item in links:
        if "source" not in item or "target" not in item:
            continue
        cleaned.append(item)
    return cleaned
