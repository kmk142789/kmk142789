"""Utility helpers for puzzle metadata and attestations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Mapping

from codex import load_puzzle_entry, locate_puzzle_file

from .puzzle_attestations import PuzzleAttestationStore, PuzzleRecord, build_record


@dataclass(slots=True)
class PuzzleMetadata:
    """Lightweight metadata describing a stored puzzle solution."""

    puzzle_id: int
    title: str
    address: str | None
    sha256: str
    path: str

    def payload(self) -> Mapping[str, str | None]:
        return {
            "title": self.title,
            "address": self.address,
            "sha256": self.sha256,
            "path": self.path,
        }


class PuzzleService:
    """Resolve puzzles and persist attestation records."""

    def __init__(self, root: Path | None = None, store: PuzzleAttestationStore | None = None) -> None:
        self._root = Path(root or Path.cwd() / "puzzle_solutions")
        self._store = store or PuzzleAttestationStore()

    # ------------------------------------------------------------------
    # Puzzle resolution

    def load(self, puzzle_id: int) -> PuzzleMetadata:
        path = locate_puzzle_file(self._root, puzzle_id)
        if path is None:
            raise FileNotFoundError(f"Puzzle {puzzle_id} not found")
        entry = load_puzzle_entry(path, puzzle_id)
        try:
            relative = str(path.resolve().relative_to(Path.cwd()))
        except ValueError:
            relative = str(path.resolve())
        return PuzzleMetadata(
            puzzle_id=puzzle_id,
            title=entry.title,
            address=entry.address,
            sha256=entry.sha256,
            path=relative,
        )

    # ------------------------------------------------------------------
    # Attestation helpers

    def record_attestation(self, metadata: PuzzleMetadata) -> PuzzleRecord:
        record = build_record(metadata.puzzle_id, metadata.payload())
        self._store.store(record)
        return record

    def list_attestations(self, puzzle_id: int, *, limit: int | None = None) -> List[PuzzleRecord]:
        return self._store.list_for_puzzle(puzzle_id, limit=limit)

    def store_snapshot(self) -> List[dict[str, object]]:
        return self._store.as_json()


__all__ = ["PuzzleMetadata", "PuzzleService"]
