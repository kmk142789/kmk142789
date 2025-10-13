"""Adapter functions exposing glyph generation helpers for packaging."""

from __future__ import annotations

from typing import Iterable

from echo_glyphs import _glyph_svg, _make_sheet, _payload_bytes, _write_text


def bytes_from_args(data: str, file_path: str | None, salt: str) -> bytes:
    """Derive the payload bytes from inline data or a file."""

    return _payload_bytes(data, file_path, salt)


def glyph_svg(byte: int, seed: int, *, size: int = 256) -> str:
    """Generate a single glyph SVG string."""

    return _glyph_svg(byte, seed, size=size)


def write_file(path: str, text: str) -> None:
    """Persist SVG text content to disk."""

    _write_text(path, text)


def make_sheet(paths: Iterable[str], *, tile: int, size: int, out: str) -> None:
    """Render a tiled sheet of glyph SVGs."""

    _make_sheet(list(paths), columns=tile, size=size, destination=out)
