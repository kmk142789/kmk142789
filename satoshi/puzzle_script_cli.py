"""CLI helper that prints the canonical P2PKH script for a puzzle wallet."""

from __future__ import annotations

import argparse
from typing import Iterable

from . import puzzle_dataset


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Emit the legacy P2PKH locking script recorded for a given Bitcoin "
            "puzzle wallet."
        )
    )
    parser.add_argument(
        "bits",
        type=int,
        help="Bit-length that identifies the desired puzzle wallet entry.",
    )
    parser.add_argument(
        "--separator",
        default="\\n",
        help=(
            "Token separator to use when rendering the script. Escape sequences "
            "such as \\n or \\t are honoured."
        ),
    )
    parser.add_argument(
        "--single-line",
        action="store_true",
        help="Shorthand for outputting the script as a single line.",
    )
    return parser


def _decode_separator(raw: str) -> str:
    """Interpret escape sequences embedded in *raw*."""

    return raw.encode("utf-8").decode("unicode_escape")


def _render_script(bits: int, *, separator: str) -> str:
    entry = puzzle_dataset.get_puzzle_metadata(bits)
    return entry.p2pkh_script(separator=separator)


def main(argv: Iterable[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.bits <= 0:
        parser.exit(2, "error: bits must be a positive integer\n")

    separator = " " if args.single_line else _decode_separator(args.separator)

    try:
        script = _render_script(args.bits, separator=separator)
    except ValueError as exc:  # invalid HASH160 payload
        parser.exit(1, f"error: {exc}\n")
    except KeyError as exc:  # unknown puzzle entry
        parser.exit(1, f"error: {exc}\n")

    print(script)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
