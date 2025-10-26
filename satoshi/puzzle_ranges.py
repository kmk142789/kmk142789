"""Utilities for parsing and summarising Bitcoin puzzle search ranges."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class RangePair:
    """Inclusive hexadecimal range describing a private key search segment."""

    start: int
    end: int

    @property
    def width(self) -> int:
        """Return the number of keys covered by the range (inclusive)."""

        return self.end - self.start + 1

    @property
    def bit_length(self) -> int:
        """Return the bit-length of the largest value in the range."""

        return max(self.start, self.end).bit_length()


@dataclass(frozen=True)
class RangeSummary:
    """Summary statistics for a collection of :class:`RangePair` entries."""

    count: int
    range_min: int
    range_max: int
    total_keys: int
    unique_widths: tuple[int, ...]
    bit_lengths: tuple[int, ...]
    puzzle_bits: int | None
    puzzle_min: int | None
    puzzle_max: int | None
    coverage_ratio: float | None

    @property
    def coverage_percent(self) -> float | None:
        """Return the coverage ratio expressed as a percentage."""

        if self.coverage_ratio is None:
            return None
        return self.coverage_ratio * 100


def parse_range_pair(text: str) -> RangePair:
    """Parse an inclusive hexadecimal ``start:end`` range string."""

    token = text.strip()
    if not token:
        raise ValueError("range payload is empty")
    if token.startswith("#"):
        raise ValueError("range payload is a comment")

    parts = token.split(":")
    if len(parts) != 2:
        raise ValueError("range must contain exactly one ':' separator")

    start_text, end_text = (part.strip().lower() for part in parts)
    if not start_text or not end_text:
        raise ValueError("range bounds cannot be empty")
    if not all(part.isalnum() for part in (start_text, end_text)):
        raise ValueError("range bounds must be hexadecimal characters")

    try:
        start = int(start_text, 16)
        end = int(end_text, 16)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise ValueError("range bounds must be valid hexadecimal integers") from exc

    if end < start:
        raise ValueError("range upper bound must be greater than or equal to lower bound")

    return RangePair(start=start, end=end)


def load_range_lines(lines: Iterable[str]) -> tuple[RangePair, ...]:
    """Parse an iterable of lines into :class:`RangePair` records."""

    result: list[RangePair] = []
    for index, raw in enumerate(lines, start=1):
        token = raw.strip()
        if not token or token.startswith("#"):
            continue
        try:
            result.append(parse_range_pair(token))
        except ValueError as exc:
            raise ValueError(f"Invalid range on line {index}: {exc}") from exc
    return tuple(result)


def load_range_file(path: str | Path) -> tuple[RangePair, ...]:
    """Read *path* and return the parsed :class:`RangePair` entries."""

    return load_range_lines(Path(path).read_text(encoding="utf-8").splitlines())


def summarise_ranges(ranges: Sequence[RangePair]) -> RangeSummary:
    """Compute summary statistics for *ranges*."""

    if not ranges:
        raise ValueError("at least one range is required to compute a summary")

    ordered = sorted(ranges, key=lambda item: (item.start, item.end))

    range_min = ordered[0].start
    range_max = ordered[0].end
    total_keys = ordered[0].width
    unique_widths = {ordered[0].width}
    bit_lengths = {ordered[0].bit_length}

    previous_end = ordered[0].end
    for pair in ordered[1:]:
        if pair.start <= previous_end:
            raise ValueError("ranges must be strictly increasing and non-overlapping")
        previous_end = pair.end

        range_min = min(range_min, pair.start)
        range_max = max(range_max, pair.end)
        total_keys += pair.width
        unique_widths.add(pair.width)
        bit_lengths.add(pair.bit_length)

    puzzle_bits: int | None = None
    puzzle_min: int | None = None
    puzzle_max: int | None = None
    coverage_ratio: float | None = None

    if len(bit_lengths) == 1:
        puzzle_bits = next(iter(bit_lengths))
        if puzzle_bits > 0:
            puzzle_min = 1 << (puzzle_bits - 1)
            puzzle_max = (1 << puzzle_bits) - 1
            puzzle_span = 1 << (puzzle_bits - 1)
            coverage_ratio = total_keys / puzzle_span

    return RangeSummary(
        count=len(ordered),
        range_min=range_min,
        range_max=range_max,
        total_keys=total_keys,
        unique_widths=tuple(sorted(unique_widths)),
        bit_lengths=tuple(sorted(bit_lengths)),
        puzzle_bits=puzzle_bits,
        puzzle_min=puzzle_min,
        puzzle_max=puzzle_max,
        coverage_ratio=coverage_ratio,
    )


def format_summary(summary: RangeSummary) -> str:
    """Return a human-readable representation of *summary*."""

    lines = [
        f"Total ranges: {summary.count}",
        f"Span: {summary.range_min:#x} – {summary.range_max:#x}",
        f"Total keys: {summary.total_keys:,}",
        "Unique widths: "
        + ", ".join(f"{width:#x}" for width in summary.unique_widths),
        "Bit-lengths: " + ", ".join(str(bits) for bits in summary.bit_lengths),
    ]

    if summary.puzzle_bits is not None:
        lines.append(f"Inferred puzzle bits: {summary.puzzle_bits}")
        lines.append(
            f"Puzzle domain: {summary.puzzle_min:#x} – {summary.puzzle_max:#x}"
        )
        if summary.coverage_ratio is not None:
            lines.append(
                "Coverage: "
                f"{summary.coverage_ratio:.6e} ({summary.coverage_percent:.9f}%)"
            )
    else:
        lines.append("Inferred puzzle bits: unknown")

    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for summarising puzzle range files."""

    parser = argparse.ArgumentParser(
        description="Summarise inclusive hexadecimal puzzle search ranges."
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Text file containing <start>:<end> ranges to summarise.",
    )
    args = parser.parse_args(argv)

    ranges = load_range_file(args.path)
    if not ranges:
        raise SystemExit("No ranges found in the provided file.")

    summary = summarise_ranges(ranges)
    print(format_summary(summary))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
