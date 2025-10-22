"""Decode base64 fragments from the dataset, stdin, or ad-hoc CLI tokens.

The original helper focused on parsing the base64 key dump preserved in
``data/base64_keys.txt``.  Operators now regularly share additional fragments
that should be inspected without modifying the canonical dataset.  This script
normalises whitespace, fixes missing padding, decodes each segment, and reports
whether the decoded payload is printable UTF-8 text or binary data regardless
of where the fragments originate.

Run with ``python -m scripts.decode_base64_keys`` to print the decoded output
for the dataset or supply ``--token``/``--file``/stdin to analyse other
fragments.
"""

from __future__ import annotations

import argparse
import base64
import pathlib
import re
import sys
from dataclasses import dataclass
from typing import Iterable, Sequence


BASE64_PATTERN = re.compile(r"[A-Za-z0-9+/]+={0,2}")
DEFAULT_DATA_PATH = (
    pathlib.Path(__file__).resolve().parents[1] / "data" / "base64_keys.txt"
)


@dataclass
class DecodedSegment:
    index: int
    token: str
    decoded: str
    is_text: bool


def load_raw_data(path: pathlib.Path | None = None) -> str:
    """Return the trimmed contents of *path* or the default dataset."""

    target = path or DEFAULT_DATA_PATH
    return target.read_text(encoding="utf-8").strip()


def normalise_segments(raw: str) -> list[str]:
    """Extract and pad base64 tokens from *raw* text."""

    segments = BASE64_PATTERN.findall(raw)
    normalised: list[str] = []
    for token in segments:
        padding_needed = (-len(token)) % 4
        if padding_needed:
            token = f"{token}{'=' * padding_needed}"
        normalised.append(token)
    return normalised


def segments_from_tokens(tokens: Sequence[str]) -> list[str]:
    """Normalise explicit base64 *tokens* supplied via CLI arguments."""

    collected: list[str] = []
    for token in tokens:
        collected.extend(normalise_segments(token))
    return collected


def decode_segment(index: int, token: str) -> DecodedSegment:
    raw_bytes = base64.b64decode(token, validate=False)
    try:
        text = raw_bytes.decode("utf-8")
        is_text = True
    except UnicodeDecodeError:
        text = raw_bytes.hex()
        is_text = False
    return DecodedSegment(index=index, token=token, decoded=text, is_text=is_text)


def decode_all(tokens: Sequence[str]) -> list[DecodedSegment]:
    """Decode *tokens* into :class:`DecodedSegment` objects."""

    return [decode_segment(index, token) for index, token in enumerate(tokens, start=1)]


def format_segment(segment: DecodedSegment) -> str:
    kind = "text" if segment.is_text else "hex"
    preview = segment.decoded if segment.is_text else segment.decoded[:60] + ("…" if len(segment.decoded) > 60 else "")
    return f"{segment.index:03d} [{kind}] {preview}"


def _resolve_tokens(
    *, tokens: Sequence[str] | None, raw_source: str | None
) -> list[str]:
    """Return the list of base64 tokens from CLI *tokens* or a raw string."""

    if tokens:
        return segments_from_tokens(tokens)
    if raw_source is None:
        raise ValueError("raw_source must be provided when tokens are not supplied")
    return normalise_segments(raw_source)


def _read_stdin() -> str:
    """Return stripped stdin content if available, otherwise an empty string."""

    return sys.stdin.read().strip()


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Decode and classify base64 fragments from the canonical dataset, "
            "stdin, or explicit CLI tokens."
        )
    )
    parser.add_argument(
        "--token",
        action="append",
        dest="tokens",
        help=(
            "Decode the provided base64 token. Can be specified multiple "
            "times and may include whitespace separated fragments."
        ),
    )
    parser.add_argument(
        "--file",
        type=pathlib.Path,
        help=(
            "Path to a file containing base64 fragments. Defaults to the "
            "repository dataset when omitted."
        ),
    )

    args = parser.parse_args(list(argv) if argv is not None else None)

    raw_source: str | None = None
    if not args.tokens:
        if args.file:
            raw_source = load_raw_data(args.file)
        elif not sys.stdin.isatty():
            raw_source = _read_stdin()
        else:
            raw_source = load_raw_data()

    try:
        tokens = _resolve_tokens(tokens=args.tokens, raw_source=raw_source)
        decoded_segments = decode_all(tokens)
        for segment in decoded_segments:
            print(format_segment(segment))
    except BrokenPipeError:
        # Allow piping to commands like ``head`` without raising tracebacks.
        sys.exit(0)


if __name__ == "__main__":
    main()
