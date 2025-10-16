#!/usr/bin/env python3
"""echoctl — tiny CLI for continuum operations."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATA = ROOT / "data"
DOCS = ROOT / "docs"
WISH = DATA / "wish_manifest.json"
PLAN = DOCS / "NEXT_CYCLE_PLAN.md"


def load_manifest() -> dict:
    """Load the wish manifest, creating a seed file if missing."""
    if not WISH.exists():
        DATA.mkdir(parents=True, exist_ok=True)
        WISH.write_text('{"version":"1.0.0","wishes":[]}', encoding="utf-8")
    return json.loads(WISH.read_text(encoding="utf-8"))


def save_manifest(manifest: dict) -> None:
    """Persist the wish manifest."""
    WISH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def add_wish(wisher: str, desire: str, catalysts: List[str]) -> None:
    """Record a new wish entry in the manifest."""
    manifest = load_manifest()
    manifest.setdefault("wishes", []).append(
        {
            "wisher": wisher,
            "desire": desire,
            "catalysts": catalysts,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "status": "new",
        }
    )
    save_manifest(manifest)
    print("✅ wish recorded.")


def run_cycle() -> None:
    """Delegate to the continuum cycle module to refresh the plan."""
    from echo.continuum_cycle import append_registry_audit, write_next_plan, REGISTRY

    DOCS.mkdir(parents=True, exist_ok=True)
    write_next_plan()
    if REGISTRY.exists():
        append_registry_audit()
    print("🌀 cycle complete → docs/NEXT_CYCLE_PLAN.md")


def show_plan() -> None:
    """Print the current plan contents, if present."""
    if PLAN.exists():
        print(PLAN.read_text(encoding="utf-8"))
    else:
        print("No plan yet. Run: echoctl cycle")


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print("usage: echoctl [cycle|plan|wish] ...")
        return 1
    cmd = argv[1]
    if cmd == "cycle":
        run_cycle()
        return 0
    if cmd == "plan":
        show_plan()
        return 0
    if cmd == "wish":
        if len(argv) < 4:
            print("usage: echoctl wish <wisher> <desire> [catalyst,...]")
            return 1
        wisher, desire = argv[2], argv[3]
        catalysts = argv[4].split(",") if len(argv) > 4 else []
        add_wish(wisher, desire, catalysts)
        return 0
    print(f"unknown command: {cmd}")
    return 1


if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main(sys.argv))
