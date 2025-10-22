"""Decode the Base64 key dump supplied in the user prompt.

The keys are provided as one extremely long string with no whitespace between
segments.  Each Base64 segment still retains its padding, so we can recover the
individual tokens by scanning for the Base64 alphabet.  The script then decodes
each segment and reports whether the decoded payload is printable UTF-8 text or
binary data.

Run with ``python -m scripts.decode_base64_keys`` to print the decoded output.
"""

from __future__ import annotations

import base64
import pathlib
import re
import sys
from dataclasses import dataclass


BASE64_PATTERN = re.compile(r"[A-Za-z0-9+/]+={0,2}")
DATA_PATH = pathlib.Path(__file__).resolve().parents[1] / "data" / "base64_keys.txt"


@dataclass
class DecodedSegment:
    index: int
    token: str
    decoded: str
    is_text: bool


def load_raw_data() -> str:
    return DATA_PATH.read_text(encoding="utf-8").strip()


def normalise_segments(raw: str) -> list[str]:
    segments = BASE64_PATTERN.findall(raw)
    normalised: list[str] = []
    for token in segments:
        padding_needed = (-len(token)) % 4
        if padding_needed:
            token = f"{token}{'=' * padding_needed}"
        normalised.append(token)
    return normalised


def decode_segment(index: int, token: str) -> DecodedSegment:
    raw_bytes = base64.b64decode(token, validate=False)
    try:
        text = raw_bytes.decode("utf-8")
        is_text = True
    except UnicodeDecodeError:
        text = raw_bytes.hex()
        is_text = False
    return DecodedSegment(index=index, token=token, decoded=text, is_text=is_text)


def decode_all(tokens: list[str]) -> list[DecodedSegment]:
    return [decode_segment(index, token) for index, token in enumerate(tokens, start=1)]


def format_segment(segment: DecodedSegment) -> str:
    kind = "text" if segment.is_text else "hex"
    preview = segment.decoded if segment.is_text else segment.decoded[:60] + ("…" if len(segment.decoded) > 60 else "")
    return f"{segment.index:03d} [{kind}] {preview}"


def main() -> None:
    raw = load_raw_data()
    tokens = normalise_segments(raw)
    decoded_segments = decode_all(tokens)
    try:
        for segment in decoded_segments:
            print(format_segment(segment))
    except BrokenPipeError:
        # Allow piping to commands like ``head`` without raising tracebacks.
        sys.exit(0)


if __name__ == "__main__":
    main()
