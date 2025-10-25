"""Validate and summarize zero-padded hexadecimal sequences."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Iterable, Iterator, Sequence


@dataclass(frozen=True)
class HexSequenceSummary:
    """Summary information for a validated hexadecimal sequence."""

    count: int
    width: int
    step: int
    start: int
    end: int
    start_hex: str
    end_hex: str


def _tokenize_hex_lines(lines: Iterable[str]) -> Iterator[str]:
    """Yield hexadecimal tokens from the provided lines."""

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        for token in stripped.split():
            yield token


def _normalize_hex_token(token: str, *, width: int | None) -> tuple[str, int]:
    """Return a normalized hexadecimal token and its integer value."""

    if token.startswith("0x") or token.startswith("0X"):
        token = token[2:]
    normalized = token.lower()

    if width is not None and len(normalized) != width:
        msg = f"hex token '{token}' has length {len(normalized)} but expected {width}"
        raise ValueError(msg)

    if any(char not in "0123456789abcdef" for char in normalized):
        raise ValueError(f"invalid hexadecimal token: '{token}'")

    return normalized, int(normalized, 16)


def validate_hex_sequence(
    tokens: Sequence[str], *, width: int | None = None, step: int = 1
) -> HexSequenceSummary:
    """Validate that *tokens* form an arithmetic hexadecimal sequence."""

    if step <= 0:
        raise ValueError("step must be positive")

    if width is not None and width <= 0:
        raise ValueError("width must be positive when provided")

    normalized_tokens: list[str] = []
    values: list[int] = []

    inferred_width = width

    for token in tokens:
        normalized, value = _normalize_hex_token(token, width=inferred_width)
        if inferred_width is None:
            inferred_width = len(normalized)
        normalized_tokens.append(normalized)
        values.append(value)

    if not values:
        raise ValueError("no hexadecimal tokens supplied")

    expected = values[0]
    for index, value in enumerate(values[1:], start=1):
        expected += step
        if value != expected:
            msg = (
                "expected sequence step of "
                f"{step} between positions {index} and {index + 1}, "
                f"but found {value - values[index - 1]}"
            )
            raise ValueError(msg)

    summary = HexSequenceSummary(
        count=len(values),
        width=inferred_width or len(normalized_tokens[0]),
        step=step,
        start=values[0],
        end=values[-1],
        start_hex=normalized_tokens[0],
        end_hex=normalized_tokens[-1],
    )

    return summary


def _load_tokens_from_paths(paths: Sequence[str]) -> list[str]:
    """Read hexadecimal tokens from the given file paths."""

    tokens: list[str] = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as handle:
            tokens.extend(_tokenize_hex_lines(handle))
    return tokens


def _format_summary(summary: HexSequenceSummary) -> str:
    """Return a human-readable representation of *summary*."""

    lines = [
        "Hex Sequence Summary:",
        f"  Count: {summary.count}",
        f"  Width: {summary.width}",
        f"  Step: {summary.step}",
        f"  Start: {summary.start_hex} ({summary.start})",
        f"  End:   {summary.end_hex} ({summary.end})",
    ]
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files containing hexadecimal values. Reads stdin when omitted.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=None,
        help="Expected width for each hexadecimal token.",
    )
    parser.add_argument(
        "--step",
        type=int,
        default=1,
        help="Expected step between sequential values (default: 1).",
    )
    args = parser.parse_args(argv)

    if args.paths:
        tokens = _load_tokens_from_paths(args.paths)
    else:
        tokens = list(_tokenize_hex_lines(sys.stdin))

    summary = validate_hex_sequence(tokens, width=args.width, step=args.step)
    print(_format_summary(summary))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
