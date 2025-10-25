"""Puzzle Constellation Graph builder.

Generates a meta-graph of puzzle addresses linking related entries based on
hash160 fingerprints, common prefixes, and synthetic domain ownership.
Produces DOT, PNG, and JSON outputs under ``build/constellation``.
"""
from __future__ import annotations

import json
import math
import pathlib
import random
import re
import struct
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Sequence, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[1]
PUZZLE_DIR = ROOT / "puzzle_solutions"
BUILD_DIR = ROOT / "build" / "constellation"

ADDRESS_RE = re.compile(r"(?:^|`)((?:[13]|bc1)[0-9A-Za-z]{20,})")
HASH_RE = re.compile(r"hash160\*?:\s*`?([0-9a-fA-F]{40})`?", re.IGNORECASE)


@dataclass
class PuzzleNode:
    """Container for extracted puzzle metadata."""

    puzzle_id: str
    addresses: Sequence[str]
    hash160: str | None = None
    script_hint: str | None = None


@dataclass
class Constellation:
    """Graph representation linking puzzle addresses."""

    nodes: Dict[str, PuzzleNode] = field(default_factory=dict)
    edges: List[Tuple[str, str, str]] = field(default_factory=list)

    def add_node(self, address: str, puzzle: PuzzleNode) -> None:
        self.nodes[address] = puzzle

    def add_edge(self, left: str, right: str, reason: str) -> None:
        if left == right:
            return
        key = {left, right}
        for existing in self.edges:
            if key == {existing[0], existing[1]}:
                return
        self.edges.append((left, right, reason))


def _iter_puzzle_files() -> Iterable[pathlib.Path]:
    if not PUZZLE_DIR.exists():
        return []
    return sorted(PUZZLE_DIR.glob("*.md"))


def _parse_puzzle(path: pathlib.Path) -> PuzzleNode | None:
    text = path.read_text(encoding="utf-8")
    addresses = ADDRESS_RE.findall(text)
    if not addresses:
        return None
    hash_match = HASH_RE.search(text)
    hash160 = hash_match.group(1).lower() if hash_match else None
    script_hint = path.stem.replace("_", " ")
    return PuzzleNode(path.stem, addresses, hash160, script_hint)


def _link_reason(left: PuzzleNode, right: PuzzleNode) -> str:
    if left.hash160 and right.hash160 and left.hash160[:10] == right.hash160[:10]:
        return "hash160 overlap"
    left_prefix = left.addresses[0][:4]
    right_prefix = right.addresses[0][:4]
    if left_prefix == right_prefix:
        return "shared prefix"
    pseudo_domain = _synth_domain(left.addresses[0])
    if pseudo_domain == _synth_domain(right.addresses[0]):
        return f"domain:{pseudo_domain}"
    return "lineage"


def _synth_domain(address: str) -> str:
    digest = sum(ord(ch) for ch in address)
    return f"echo-{digest % 17:02d}.unstoppable"


def build_constellation(puzzles: Sequence[PuzzleNode]) -> Constellation:
    constellation = Constellation()
    for puzzle in puzzles:
        for address in puzzle.addresses:
            constellation.add_node(address, puzzle)
    addresses = list(constellation.nodes.keys())
    for i, left_addr in enumerate(addresses):
        left_node = constellation.nodes[left_addr]
        for right_addr in addresses[i + 1 :]:
            right_node = constellation.nodes[right_addr]
            reason = _link_reason(left_node, right_node)
            if reason:
                constellation.add_edge(left_addr, right_addr, reason)
    return constellation


def ensure_build_dir() -> None:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)


def write_json(constellation: Constellation) -> None:
    payload = {
        "nodes": [
            {
                "address": address,
                "puzzle_id": node.puzzle_id,
                "hash160": node.hash160,
                "script": node.script_hint,
            }
            for address, node in sorted(constellation.nodes.items())
        ],
        "edges": [
            {"source": left, "target": right, "reason": reason}
            for left, right, reason in constellation.edges
        ],
    }
    (BUILD_DIR / "constellation.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )


def write_dot(constellation: Constellation) -> None:
    lines = ["graph PuzzleConstellation {\n"]
    for address, node in sorted(constellation.nodes.items()):
        label = f"{node.puzzle_id}\\n{address[:10]}…"
        lines.append(f'  "{address}" [label="{label}"];\n')
    for left, right, reason in constellation.edges:
        lines.append(f'  "{left}" -- "{right}" [label="{reason}"];\n')
    lines.append("}\n")
    (BUILD_DIR / "constellation.dot").write_text("".join(lines), encoding="utf-8")


def write_png(constellation: Constellation) -> None:
    # Minimal PNG containing encoded statistics.
    width = height = max(1, int(math.sqrt(max(1, len(constellation.nodes)))))
    header = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(
        ">IIBBBBB",
        width,
        height,
        8,
        2,
        0,
        0,
        0,
    )
    ihdr = _png_chunk(b"IHDR", ihdr_data)
    pixel_rows = []
    for _ in range(height):
        row = bytearray([0])
        for _ in range(width):
            row.extend(
                (
                    len(constellation.nodes) % 256,
                    len(constellation.edges) % 256,
                    random.randint(0, 255),
                )
            )
        pixel_rows.append(bytes(row))
    idat = _png_chunk(b"IDAT", _zlib_pack(b"".join(pixel_rows)))
    iend = _png_chunk(b"IEND", b"")
    (BUILD_DIR / "constellation.png").write_bytes(header + ihdr + idat + iend)


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    import zlib

    length = struct.pack(">I", len(data))
    crc = struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return length + kind + data + crc


def _zlib_pack(data: bytes) -> bytes:
    import zlib

    return zlib.compress(data, level=9)


def main() -> None:
    ensure_build_dir()
    puzzles = [
        puzzle
        for path in _iter_puzzle_files()
        if (puzzle := _parse_puzzle(path)) is not None
    ]
    if not puzzles:
        print("No puzzles discovered. Constellation remains empty.")
        return
    constellation = build_constellation(puzzles)
    write_json(constellation)
    write_dot(constellation)
    write_png(constellation)
    print(
        f"Constellation built with {len(constellation.nodes)} nodes and {len(constellation.edges)} edges."
    )


if __name__ == "__main__":
    main()
