"""Utility for generating zero-padded hexadecimal sequences."""

from __future__ import annotations

import argparse


def generate_hex_sequence(count: int, *, width: int = 64, start: int = 1) -> list[str]:
    """Return a list of hexadecimal strings.

    Args:
        count: Number of sequential values to generate.
        width: Width of the resulting hexadecimal strings. Defaults to 64.
        start: Starting integer for the sequence. Defaults to 1.

    Returns:
        A list of lowercase hexadecimal strings, zero-padded to ``width``.
    """
    if count < 0:
        raise ValueError("count must be non-negative")
    if width < 1:
        raise ValueError("width must be positive")
    if start < 0:
        raise ValueError("start must be non-negative")

    result: list[str] = []
    for value in range(start, start + count):
        result.append(format(value, "x").zfill(width))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "count",
        type=int,
        help="Number of sequential values to output.",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=1,
        help="Starting integer for the sequence (default: 1).",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=64,
        help="Width of the hexadecimal output (default: 64).",
    )
    args = parser.parse_args()

    for item in generate_hex_sequence(args.count, width=args.width, start=args.start):
        print(item)


if __name__ == "__main__":
    main()
