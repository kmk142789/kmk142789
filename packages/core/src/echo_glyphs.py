#!/usr/bin/env python3
"""Generate deterministic Echo glyph SVGs from arbitrary input bytes."""

import argparse
import hashlib
import math
import os
import random
import textwrap


def _svg_header(width: int, height: int, background: str | None = None) -> str:
    bg_rect = (
        f'<rect width="{width}" height="{height}" fill="{background}"/>'
        if background
        else ""
    )
    return (
        "<svg xmlns=\"http://www.w3.org/2000/svg\" "
        f"width=\"{width}\" height=\"{height}\" viewBox=\"0 0 {width} {height}\">\n"
        f"{bg_rect}\n"
    )


def _svg_footer() -> str:
    return "</svg>\n"


def _circle(
    cx: float,
    cy: float,
    radius: float,
    stroke: str,
    *,
    fill: str = "none",
    stroke_width: float = 2.0,
    opacity: float = 1.0,
) -> str:
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="{stroke_width}" opacity="{opacity}"/>'
    )


def _line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    stroke: str,
    *,
    stroke_width: float = 2.0,
    opacity: float = 1.0,
) -> str:
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
        f'stroke-width="{stroke_width}" opacity="{opacity}" />'
    )


def _polygon(
    points: list[tuple[float, float]],
    stroke: str,
    *,
    fill: str = "none",
    stroke_width: float = 2.0,
    opacity: float = 1.0,
) -> str:
    pts = " ".join(f"{x},{y}" for x, y in points)
    return (
        f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="{stroke_width}" opacity="{opacity}" />'
    )


def _arc_path(
    cx: float,
    cy: float,
    radius: float,
    start_degrees: float,
    sweep_degrees: float,
) -> str:
    start_x = cx + radius * math.cos(math.radians(start_degrees))
    start_y = cy + radius * math.sin(math.radians(start_degrees))
    end_x = cx + radius * math.cos(math.radians(start_degrees + sweep_degrees))
    end_y = cy + radius * math.sin(math.radians(start_degrees + sweep_degrees))
    large_arc_flag = 1 if abs(sweep_degrees) > 180 else 0
    sweep_flag = 1 if sweep_degrees >= 0 else 0
    return (
        f"M {start_x:.2f} {start_y:.2f} A {radius:.2f} {radius:.2f} 0 {large_arc_flag} "
        f"{sweep_flag} {end_x:.2f} {end_y:.2f}"
    )


def _path(
    path_data: str,
    stroke: str,
    *,
    fill: str = "none",
    stroke_width: float = 2.0,
    opacity: float = 1.0,
) -> str:
    return (
        f'<path d="{path_data}" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="{stroke_width}" opacity="{opacity}"/>'
    )


_PALETTE = [
    "#0e1116",
    "#243b55",
    "#11998e",
    "#38ef7d",
    "#ff9f1c",
    "#ff3c38",
    "#b28dff",
    "#f5e960",
]

_BACKGROUND = "#f7f8fa"


def _glyph_svg(byte: int, seed: int, *, size: int = 256, margin: int = 12) -> str:
    rng = random.Random((seed << 8) ^ byte)
    cx = cy = size / 2
    radius = size / 2 - margin
    layers: list[str] = []

    layers.append(
        _circle(
            cx,
            cy,
            radius,
            _PALETTE[rng.randrange(len(_PALETTE))],
            stroke_width=3,
            opacity=0.6,
        )
    )
    layers.append(
        _circle(
            cx,
            cy,
            radius * 0.66,
            _PALETTE[rng.randrange(len(_PALETTE))],
            stroke_width=2,
            opacity=0.6,
        )
    )

    spoke_count = 3 + (byte & 0x07)
    for index in range(spoke_count):
        angle = (360.0 / spoke_count) * index + (byte % 13) * 2
        tip_x = cx + math.cos(math.radians(angle)) * radius * 0.9
        tip_y = cy + math.sin(math.radians(angle)) * radius * 0.9
        layers.append(
            _line(
                cx,
                cy,
                tip_x,
                tip_y,
                _PALETTE[(index + byte) % len(_PALETTE)],
                stroke_width=1.8,
                opacity=0.8,
            )
        )
        layers.append(
            _circle(
                tip_x,
                tip_y,
                radius * 0.03 + (byte % 3),
                "none",
                fill=_PALETTE[(index * 3 + byte) % len(_PALETTE)],
                opacity=0.9,
            )
        )

    polygon_sides = 3 + ((byte >> 3) & 0x03)
    rotation = (byte * 7) % 360
    polygon_points: list[tuple[float, float]] = []
    for index in range(polygon_sides):
        angle = rotation + index * (360.0 / polygon_sides)
        polygon_points.append(
            (
                cx + math.cos(math.radians(angle)) * radius * 0.45,
                cy + math.sin(math.radians(angle)) * radius * 0.45,
            )
        )
    layers.append(
        _polygon(
            polygon_points,
            _PALETTE[(byte // 11) % len(_PALETTE)],
            fill=_PALETTE[(byte // 5) % len(_PALETTE)],
            stroke_width=2,
            opacity=0.25,
        )
    )

    first_arc = _arc_path(cx, cy, radius * 0.8, (byte * 5) % 360, 120 + (byte % 5) * 24)
    second_arc = _arc_path(cx, cy, radius * 0.56, (byte * 11) % 360, -140 - (byte % 4) * 18)
    layers.append(
        _path(
            first_arc,
            _PALETTE[(byte + 2) % len(_PALETTE)],
            stroke_width=3,
            opacity=0.7,
        )
    )
    layers.append(
        _path(
            second_arc,
            _PALETTE[(byte + 5) % len(_PALETTE)],
            stroke_width=2,
            opacity=0.7,
        )
    )

    layers.append(
        _circle(
            cx,
            cy,
            radius * 0.12,
            _PALETTE[(byte + 3) % len(_PALETTE)],
            stroke_width=2,
        )
    )
    for offset in range(3):
        angle = rotation + offset * 120 + (byte % 60)
        point_x = cx + math.cos(math.radians(angle)) * radius * 0.18
        point_y = cy + math.sin(math.radians(angle)) * radius * 0.18
        layers.append(
            _circle(
                point_x,
                point_y,
                radius * 0.035,
                "none",
                fill=_PALETTE[(offset + byte) % len(_PALETTE)],
            )
        )

    svg_parts = [_svg_header(size, size)]
    svg_parts.extend(layers)
    svg_parts.append(_svg_footer())
    return "\n".join(svg_parts)


def _payload_bytes(data: str | None, file_path: str | None, salt: str) -> bytes:
    if file_path:
        with open(file_path, "rb") as file:
            raw = file.read()
    else:
        raw = (data or "").encode("utf-8")

    checksum = hashlib.sha256(raw).digest()[:2]
    salted = hashlib.blake2s(raw, key=salt.encode("utf-8"), digest_size=32).digest()
    return salted + checksum


def _write_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def _make_sheet(
    glyph_paths: list[str],
    *,
    columns: int = 4,
    size: int = 256,
    gap: int = 16,
    destination: str = "sheet.svg",
) -> None:
    total = len(glyph_paths)
    rows = (total + columns - 1) // columns
    width = columns * size + (columns + 1) * gap
    height = rows * size + (rows + 1) * gap

    svg = [_svg_header(width, height, _BACKGROUND)]
    for index, path in enumerate(glyph_paths):
        with open(path, "r", encoding="utf-8") as glyph_file:
            inner = glyph_file.read()
        body = inner.split(">", 1)[1].rsplit("</svg>", 1)[0]
        row = index // columns
        column = index % columns
        offset_x = gap + column * (size + gap)
        offset_y = gap + row * (size + gap)
        svg.append(f'<g transform="translate({offset_x},{offset_y})">{body}</g>')

    svg.append(_svg_footer())
    _write_text(destination, "".join(svg))


def _build_manifest(directory: str, payload_length: int, salt: str) -> None:
    manifest = textwrap.dedent(
        f"""
        # Echo Glyphs Manifest
        payload_len: {payload_length} bytes (includes 2-byte checksum)
        salt_hash: {hashlib.sha256(salt.encode()).hexdigest()}
        sheet: sheet.svg
        """
    )
    _write_text(os.path.join(directory, "manifest.txt"), manifest)


def _derive_seed(salt: str) -> int:
    return int.from_bytes(hashlib.sha256(salt.encode()).digest()[:8], "big")


def _generate_glyphs(
    payload: bytes,
    *,
    seed: int,
    output_directory: str,
    size: int,
) -> list[str]:
    paths: list[str] = []
    for index, byte in enumerate(payload):
        path = os.path.join(output_directory, f"glyph_{index:03d}.svg")
        _write_text(path, _glyph_svg(byte, seed, size=size))
        paths.append(path)
    return paths


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Echo glyph generator: deterministically render shape-only sigils from bytes."
        )
    )
    parser.add_argument("--data", help="inline data to encode")
    parser.add_argument("--file", help="read data from file")
    parser.add_argument("--salt", default="∇⊸≋∇", help="salt for determinism")
    parser.add_argument("--out", default="glyphs_out", help="output directory")
    parser.add_argument("--size", type=int, default=256, help="glyph size in pixels")
    parser.add_argument("--tile", type=int, default=6, help="columns in the sprite sheet")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    if not args.data and not args.file:
        raise SystemExit("Provide --data or --file")

    os.makedirs(args.out, exist_ok=True)
    payload = _payload_bytes(args.data, args.file, args.salt)
    seed = _derive_seed(args.salt)

    glyph_paths = _generate_glyphs(payload, seed=seed, output_directory=args.out, size=args.size)
    _make_sheet(
        glyph_paths,
        columns=args.tile,
        size=args.size,
        destination=os.path.join(args.out, "sheet.svg"),
    )
    _build_manifest(args.out, len(payload), args.salt)

    print(
        f"\u2713 Wrote {len(glyph_paths)} glyphs to {args.out}/ and a tiled sheet.svg"
    )


if __name__ == "__main__":
    main()
