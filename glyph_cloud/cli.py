#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from .glyphs import make_glyphs  # you already have a generator; import its main

def main():
    ap = argparse.ArgumentParser(
        prog="echo-glyph",
        description="Echo Glyph Cloud CLI (deterministic, no letters in art)",
    )
    ap.add_argument("--data", help="inline data")
    ap.add_argument("--file", help="path to input file")
    ap.add_argument("--salt", default="∇⊸≋∇")
    ap.add_argument("--out", default="glyphs_out")
    ap.add_argument("--size", type=int, default=256)
    ap.add_argument("--tile", type=int, default=6)
    args = ap.parse_args()

    if not args.data and not args.file:
        sys.exit("Provide --data or --file")

    os.makedirs(args.out, exist_ok=True)
    result = make_glyphs(
        data=args.data,
        file=args.file,
        salt=args.salt,
        out_dir=args.out,
        size=args.size,
        tile=args.tile,
    )
    # Write a small JSON manifest
    manifest = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "salt_sha256": hashlib.sha256(args.salt.encode()).hexdigest(),
        "out_dir": args.out,
        "count": result["count"],
        "sheet": result["sheet"],
        "checksum": result["checksum"],
    }
    with open(Path(args.out) / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    print(
        f"✓ Glyphs: {result['count']} | sheet: {result['sheet']} | checksum: {result['checksum']}"
    )


if __name__ == "__main__":
    main()
