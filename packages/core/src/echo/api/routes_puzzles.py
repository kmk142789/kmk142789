"""Puzzle detail API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .puzzle_service import PuzzleService

router = APIRouter(prefix="/api/puzzles", tags=["puzzles"])
_service = PuzzleService()


@router.get("/{puzzle_id}")
def get_puzzle(puzzle_id: int) -> dict[str, object]:
    try:
        metadata = _service.load(puzzle_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    attestations = [record.to_dict() for record in _service.list_attestations(puzzle_id, limit=50)]
    return {
        "puzzle_id": metadata.puzzle_id,
        "title": metadata.title,
        "address": metadata.address,
        "sha256": metadata.sha256,
        "path": metadata.path,
        "attestations": attestations,
    }


__all__ = ["router"]
