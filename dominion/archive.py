"""CLI entry point for archiving Dominion artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from .registry import AdapterRegistry


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Archive Dominion build outputs with signatures.")
    parser.add_argument("--source", default="build", help="Source directory to archive.")
    parser.add_argument("--out", dest="out_dir", default="build/archives", help="Destination directory.")
    parser.add_argument("--name", default="dominion", help="Archive base name.")
    args = parser.parse_args(argv)

    source = Path(args.source).resolve()
    if not source.exists():
        raise SystemExit(f"Source directory not found: {source}")

    registry = AdapterRegistry()
    archive_adapter = registry.archive()
    receipt = archive_adapter.create_archive(source, Path(args.out_dir), name=args.name)
    print(f"Archive created: {receipt.archive_path} (sha256={receipt.digest})")
    print(f"Signature written to {receipt.signature_path}")


if __name__ == "__main__":
    main()
