"""Structured access to the solved Bitcoin puzzle dataset."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional

_DATA_PATH = Path(__file__).with_name("puzzle_solutions.json")


@dataclass(frozen=True)
class PuzzleSolution:
    """Record describing a solved Bitcoin puzzle wallet."""

    bits: int
    range_min: str
    range_max: str
    address: str
    btc_value: float
    hash160_compressed: str
    public_key: str
    private_key: str
    solve_date: str


@lru_cache(maxsize=1)
def _load_raw_dataset() -> tuple[PuzzleSolution, ...]:
    payload = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    return tuple(
        PuzzleSolution(
            bits=int(entry["bits"]),
            range_min=entry["range_min"],
            range_max=entry["range_max"],
            address=entry["address"],
            btc_value=float(entry["btc_value"]),
            hash160_compressed=entry["hash160_compressed"],
            public_key=entry["public_key"],
            private_key=entry["private_key"],
            solve_date=entry["solve_date"],
        )
        for entry in payload
    )


def load_puzzle_solutions() -> tuple[PuzzleSolution, ...]:
    """Return all solved puzzle entries sorted by bit-length."""

    return _load_raw_dataset()


def iter_puzzle_solutions() -> Iterable[PuzzleSolution]:
    """Yield solved puzzle entries in ascending order by difficulty."""

    yield from load_puzzle_solutions()


def get_solution_by_bits(bits: int) -> PuzzleSolution:
    """Return the puzzle solution for the requested bit-length."""

    for entry in load_puzzle_solutions():
        if entry.bits == bits:
            return entry
    raise KeyError(f"No puzzle solution recorded for {bits} bits")


def find_solution_by_address(address: str) -> Optional[PuzzleSolution]:
    """Return the solution entry corresponding to *address*, if known."""

    address_normalised = address.strip()
    for entry in load_puzzle_solutions():
        if entry.address == address_normalised:
            return entry
    return None
