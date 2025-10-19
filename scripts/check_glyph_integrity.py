#!/usr/bin/env python3
"""Verify glyph assets by computing SHA-256 hashes."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

GLYPH_DIR = Path(__file__).resolve().parents[1] / "docs" / "glyphs"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "packages" / "glyphs" / "inventory.json"


def hash_file(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()


def main() -> int:
    if not GLYPH_DIR.exists():
        print(f"::error ::Glyph directory missing: {GLYPH_DIR}")
        return 1

    svg_files = sorted(p for p in GLYPH_DIR.glob("*.svg") if p.is_file())
    if not svg_files:
        print("::error ::No glyph SVG files found")
        return 1

    inventory = {p.name: hash_file(p) for p in svg_files}
    OUTPUT_PATH.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    try:
        display_path = OUTPUT_PATH.relative_to(Path.cwd())
    except ValueError:
        display_path = OUTPUT_PATH
    print(f"Recorded {len(inventory)} glyph hashes to {display_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
