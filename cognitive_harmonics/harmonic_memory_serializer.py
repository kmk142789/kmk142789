"""Helpers for projecting EchoEvolver state into the harmonic-memory schema."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict

from satoshi.puzzle_dataset import PuzzleSolution, load_puzzle_solutions

# Snapshot files live under this directory so downstream tooling can glob them.
CYCLES_DIR = Path("harmonic_memory") / "cycles"


def canonical_checksum(payload: Any) -> str:
    """Return a deterministic SHA-256 checksum for arbitrary JSON data."""

    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _select_puzzle(cycle_id: int) -> PuzzleSolution:
    """Return the solved puzzle entry corresponding to ``cycle_id``."""

    solutions = load_puzzle_solutions()
    if not solutions:
        raise RuntimeError("Puzzle dataset is empty; cannot build harmonic memory record")

    index = min(max(cycle_id - 1, 0), len(solutions) - 1)
    return solutions[index]


def _puzzle_metadata(puzzle: PuzzleSolution) -> Dict[str, Any]:
    """Convert a :class:`PuzzleSolution` into the serializer metadata block."""

    address_checksum = sha256(puzzle.address.encode("utf-8")).hexdigest()
    hash_checksum = sha256(puzzle.hash160_compressed.lower().encode("utf-8")).hexdigest()

    return {
        "puzzle_id": f"puzzle-{puzzle.bits:03d}",
        "bits": puzzle.bits,
        "address": puzzle.address,
        "hash160": puzzle.hash160_compressed.lower(),
        "solve_date": puzzle.solve_date,
        "btc_value": puzzle.btc_value,
        "range": {"min": puzzle.range_min, "max": puzzle.range_max},
        "public_key": puzzle.public_key,
        "checksums": {
            "address_sha256": address_checksum,
            "hash160_sha256": hash_checksum,
        },
    }


def build_harmonic_memory_record(
    *,
    cycle_id: int,
    snapshot: Dict[str, Any],
    payload: Dict[str, Any],
    artifact_text: str,
    artifact_path: Path,
) -> Dict[str, Any]:
    """Return a record matching :mod:`harmonic_memory`'s function schema."""

    puzzle = _select_puzzle(cycle_id)
    puzzle_block = _puzzle_metadata(puzzle)

    checksums = {
        "state_sha256": canonical_checksum(snapshot),
        "payload_sha256": canonical_checksum(payload),
        "artifact_sha256": sha256(artifact_text.encode("utf-8")).hexdigest(),
    }

    cycle_snapshot = {
        "cycle_id": cycle_id,
        "puzzle": puzzle_block,
        "state": snapshot,
        "payload": payload,
        "artifact": {
            "path": str(artifact_path),
            "body": artifact_text,
        },
        "checksums": checksums,
    }

    record = {
        "user_music_preference": (
            f"cycle-{cycle_id:05d}-puzzle-{puzzle.bits:03d}-address-{puzzle.address}"
        ),
        "lyrical_complexity": (
            "|".join(
                [
                    f"narrative-lines:{len(snapshot.get('storyboard', []))}",
                    f"event-count:{len(snapshot.get('events', []))}",
                    f"payload-checksum:{checksums['payload_sha256'][:12]}",
                ]
            )
        ),
        "adaptive_evolution": True,
        "cycle_snapshot": cycle_snapshot,
    }

    return record


def persist_cycle_record(record: Dict[str, Any], *, base_path: Path = CYCLES_DIR) -> Path:
    """Write *record* to disk and return the resulting file path."""

    base_path.mkdir(parents=True, exist_ok=True)
    cycle_id = record["cycle_snapshot"]["cycle_id"]
    path = base_path / f"cycle_{cycle_id:05d}.json"
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
