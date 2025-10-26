"""Utilities for validating and summarising hexadecimal keyspace ranges."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
from typing import Iterable, List

CHUNK_MASK = int("fffffffff", 16)
CHUNK_SIZE = CHUNK_MASK + 1


@dataclass(frozen=True)
class RangeAllocation:
    """Represents a closed interval of the keyspace."""

    start: int
    end: int

    @property
    def size(self) -> int:
        """Return the number of values contained in the interval."""

        return self.end - self.start + 1


def parse_range_line(line: str) -> RangeAllocation:
    """Parse a line containing a colon separated hexadecimal range."""

    raw = line.strip()
    if not raw or raw.startswith("#"):
        raise ValueError("Range lines must contain start:end hexadecimal pairs")

    try:
        start_str, end_str = raw.split(":", maxsplit=1)
    except ValueError as exc:  # pragma: no cover - defensive branch
        raise ValueError(f"Invalid range line: {line!r}") from exc

    if not start_str or not end_str:
        raise ValueError(f"Invalid range line: {line!r}")

    start = int(start_str, 16)
    end = int(end_str, 16)

    if end < start:
        raise ValueError(f"End before start in range {line!r}")

    return RangeAllocation(start=start, end=end)


def validate_allocation(allocation: RangeAllocation) -> None:
    """Ensure the allocation aligns with the expected 36-bit chunking."""

    if allocation.start & CHUNK_MASK:
        raise ValueError(
            f"Start {allocation.start:#x} is not aligned to {CHUNK_SIZE:#x} boundaries"
        )

    if allocation.end & CHUNK_MASK != CHUNK_MASK:
        raise ValueError(
            f"End {allocation.end:#x} does not terminate on the expected boundary"
        )

    if allocation.size != CHUNK_SIZE:
        raise ValueError(
            f"Range {allocation.start:#x}:{allocation.end:#x} spans {allocation.size},"
            f" expected {CHUNK_SIZE}"
        )


@dataclass
class AllocationSummary:
    count: int
    chunk_size: int
    total_values: int

    def as_dict(self) -> dict[str, int]:
        return {
            "count": self.count,
            "chunk_size": self.chunk_size,
            "total_values": self.total_values,
        }


def summarise_ranges(lines: Iterable[str]) -> AllocationSummary:
    """Parse and validate a collection of textual range definitions.

    Comment lines beginning with ``#`` and empty lines are ignored so callers
    can annotate range files without breaking validation.
    """

    allocations: List[RangeAllocation] = []
    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        allocation = parse_range_line(stripped)
        validate_allocation(allocation)
        allocations.append(allocation)

    total_values = sum(item.size for item in allocations)
    return AllocationSummary(
        count=len(allocations),
        chunk_size=CHUNK_SIZE,
        total_values=total_values,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarise hexadecimal keyspace ranges provided in a text file."
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Path to a file containing colon separated start:end hexadecimal pairs.",
    )
    args = parser.parse_args()

    summary = summarise_ranges(args.path.read_text().splitlines())
    print(
        f"Ranges: {summary.count}\n"
        f"Chunk size: {summary.chunk_size} (0x{CHUNK_SIZE:x})\n"
        f"Total values: {summary.total_values}"
    )


if __name__ == "__main__":  # pragma: no cover - CLI behaviour
    main()
