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
import hashlib
import json
import os
import pathlib
import re
import sys
from dataclasses import dataclass
from typing import Iterable, Sequence

from echo.glyphnet_decoder import GlyphnetKeyDecoder, GlyphnetKeyFeature


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
    length: int
    integer: int | None

    def as_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "token": self.token,
            "decoded": self.decoded,
            "is_text": self.is_text,
            "length": self.length,
            "integer": self.integer,
        }


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
    raw_bytes = decode_bytes(token)
    integer: int | None = None
    if len(raw_bytes) <= 64:
        integer = int.from_bytes(raw_bytes, byteorder="big")

    try:
        decoded_text = raw_bytes.decode("utf-8")
        # Guard against control bytes (e.g., NUL padding) that technically
        # decode but are not human-friendly. Treat them as binary payloads so
        # callers receive integer and hex previews instead of unreadable
        # strings.
        if decoded_text and decoded_text.isprintable():
            text = decoded_text
            is_text = True
        else:
            raise UnicodeDecodeError("utf-8", raw_bytes, 0, len(raw_bytes), "non-printable payload")
    except UnicodeDecodeError:
        text = raw_bytes.hex()
        is_text = False
    return DecodedSegment(
        index=index,
        token=token,
        decoded=text,
        is_text=is_text,
        length=len(raw_bytes),
        integer=integer if not is_text else None,
    )


def decode_bytes(token: str) -> bytes:
    """Decode a base64 token to raw bytes."""

    return base64.b64decode(token, validate=False)


def _secure_open(path: pathlib.Path, mode: str, perm: int):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, perm)
    return os.fdopen(fd, mode)


def write_private_vault(vault_dir: pathlib.Path, tokens: Sequence[str]) -> pathlib.Path:
    """Write decoded payloads into a private vault directory."""

    vault_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(vault_dir, 0o700)

    manifest: dict[str, object] = {"segments": []}
    for index, token in enumerate(tokens, start=1):
        raw_bytes = decode_bytes(token)
        filename = f"segment_{index:03d}.bin"
        segment_path = vault_dir / filename
        with _secure_open(segment_path, "wb", 0o600) as handle:
            handle.write(raw_bytes)
        digest = hashlib.sha256(raw_bytes).hexdigest()
        manifest["segments"].append(
            {"index": index, "file": filename, "length": len(raw_bytes), "sha256": digest}
        )

    manifest_path = vault_dir / "manifest.json"
    with _secure_open(manifest_path, "w", 0o600) as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")

    return manifest_path


def decode_all(tokens: Sequence[str]) -> list[DecodedSegment]:
    """Decode *tokens* into :class:`DecodedSegment` objects."""

    return [decode_segment(index, token) for index, token in enumerate(tokens, start=1)]


def format_segment(segment: DecodedSegment) -> str:
    kind = "text" if segment.is_text else "hex"
    preview = segment.decoded if segment.is_text else segment.decoded[:60] + ("…" if len(segment.decoded) > 60 else "")
    integer_suffix = ""
    if segment.integer is not None:
        integer_suffix = f" int={segment.integer}"
    return f"{segment.index:03d} [{kind}] len={segment.length} {preview}{integer_suffix}"


def format_feature(feature: GlyphnetKeyFeature) -> str:
    tags = ",".join(feature.tags)
    return (
        f"{feature.token} :: len={feature.length} ascii={feature.ascii_ratio:.3f} "
        f"entropy={feature.entropy:.3f} tags={tags}"
    )


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
    parser.add_argument(
        "--features",
        action="store_true",
        help="Render EchoGlyphNet metadata (entropy, ascii ratio, tags) for each token.",
    )
    parser.add_argument(
        "--integers",
        action="store_true",
        help=(
            "After decoding, print a summary table of integer values for binary "
            "segments (payloads up to 64 bytes)."
        ),
    )
    parser.add_argument(
        "--json",
        type=pathlib.Path,
        help=(
            "Optional path to write a JSON summary of decoded segments. The "
            "file will contain raw tokens, decoded payloads, and metadata."
        ),
    )
    parser.add_argument(
        "--vault-dir",
        type=pathlib.Path,
        help=(
            "Optional private directory to store decoded payloads. Segment "
            "files and a manifest.json will be written with restrictive "
            "permissions."
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

        if args.integers:
            integer_segments = [segment for segment in decoded_segments if segment.integer is not None]
            if integer_segments:
                print("\n# integer values")
                for segment in integer_segments:
                    print(f"{segment.index:03d} int={segment.integer} len={segment.length}")

        if args.features:
            decoder = GlyphnetKeyDecoder()
            features = decoder.decode_tokens(tokens)
            report = decoder.build_protocol_report(features)

            print("\n# EchoGlyphNet feature map")
            for feature in features:
                print(format_feature(feature))
            print(f"summary={report}")

        if args.json:
            payload = {
                "tokens": tokens,
                "segments": [segment.as_dict() for segment in decoded_segments],
            }
            args.json.write_text(
                json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
            )
        if args.vault_dir:
            manifest_path = write_private_vault(args.vault_dir, tokens)
            print(f"\n# private vault\nmanifest={manifest_path}")
    except BrokenPipeError:
        # Allow piping to commands like ``head`` without raising tracebacks.
        sys.exit(0)


if __name__ == "__main__":
    main()
