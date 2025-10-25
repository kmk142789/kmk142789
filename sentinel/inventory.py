from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from . import utils
from .signals import derive_signals


@dataclass(slots=True)
class Receipt:
    path: str
    sha256: str
    size: int
    mode: str
    metadata: dict[str, Any]


def _load_receipt(path: Path, base_dir: Path) -> Receipt:
    metadata: dict[str, Any] = {}
    if path.suffix.lower() in {".json", ".sarif"}:
        try:
            metadata = utils.read_json(path)
        except json.JSONDecodeError:
            metadata = {"error": "invalid-json"}
    elif path.suffix.lower() in {".txt", ".md"}:
        metadata = {"preview": path.read_text(encoding="utf-8", errors="ignore")[:200]}

    return Receipt(
        path=utils.relpath(path, base_dir),
        sha256=utils.sha256_file(path) if path.exists() and path.is_file() else "",
        size=path.stat().st_size if path.exists() and path.is_file() else 0,
        mode=utils.detect_mode(path),
        metadata=metadata,
    )


def collect_receipts(receipts_dir: Path) -> list[Receipt]:
    base_dir = receipts_dir.resolve()
    if not receipts_dir.exists():
        return []
    receipts: list[Receipt] = []
    for entry in sorted(receipts_dir.rglob("*")):
        if entry.is_dir():
            continue
        receipts.append(_load_receipt(entry, base_dir))
    return receipts


def build_inventory(lineage_path: Path, receipts_dir: Path, registry_path: Path | None = None) -> dict[str, Any]:
    lineage: dict[str, Any] = {}
    if lineage_path.exists():
        lineage = utils.read_json(lineage_path)

    receipts = collect_receipts(receipts_dir)
    registry = utils.load_registry(registry_path)

    payload = {
        "version": 1,
        "generated_at": utils.isoformat(),
        "lineage": lineage,
        "receipts": [asdict(receipt) for receipt in receipts],
        "registry": registry,
    }
    payload["signals"] = derive_signals(payload)
    return payload


def write_inventory(payload: dict[str, Any], out_path: Path) -> None:
    utils.write_json(out_path, payload)


def iter_receipt_paths(receipts_dir: Path) -> Iterable[Path]:
    if not receipts_dir.exists():
        return []
    return (path for path in receipts_dir.rglob("*") if path.is_file())


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a Sentinel asset inventory")
    parser.add_argument("--lineage", type=Path, required=True)
    parser.add_argument("--receipts", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=False)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    options = parse_args(argv)
    payload = build_inventory(options.lineage, options.receipts, options.registry)
    write_inventory(payload, options.out)
    print(f"Sentinel inventory written to {options.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())

