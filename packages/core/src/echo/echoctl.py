#!/usr/bin/env python3
"""echoctl — tiny CLI for continuum operations."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List

try:  # pragma: no cover - executed when run as module
    from .wish_insights import summarize_wishes
except ImportError:  # pragma: no cover - executed when run as script
    _INSIGHTS_SPEC = importlib.util.spec_from_file_location(
        "echo.wish_insights", (Path(__file__).resolve().parent / "wish_insights.py")
    )
    if _INSIGHTS_SPEC is None or _INSIGHTS_SPEC.loader is None:
        raise
    _INSIGHTS = importlib.util.module_from_spec(_INSIGHTS_SPEC)
    _INSIGHTS_SPEC.loader.exec_module(_INSIGHTS)  # type: ignore[attr-defined]
    summarize_wishes = _INSIGHTS.summarize_wishes  # type: ignore[attr-defined]

try:  # pragma: no cover - executed when run as module
    from ._paths import DATA_ROOT, DOCS_ROOT, REPO_ROOT
except ImportError:  # pragma: no cover - executed when run as script
    _PATHS_SPEC = importlib.util.spec_from_file_location(
        "echo._paths", (Path(__file__).resolve().parent / "_paths.py")
    )
    if _PATHS_SPEC is None or _PATHS_SPEC.loader is None:
        raise
    _PATHS = importlib.util.module_from_spec(_PATHS_SPEC)
    _PATHS_SPEC.loader.exec_module(_PATHS)  # type: ignore[attr-defined]
    DATA_ROOT = _PATHS.DATA_ROOT  # type: ignore[attr-defined]
    DOCS_ROOT = _PATHS.DOCS_ROOT  # type: ignore[attr-defined]
    REPO_ROOT = _PATHS.REPO_ROOT  # type: ignore[attr-defined]

DATA_ROOT = Path(os.environ.get("ECHO_DATA_ROOT", str(DATA_ROOT)))
DOCS_ROOT = Path(os.environ.get("ECHO_DOCS_ROOT", str(DOCS_ROOT)))
PULSE_HISTORY = Path(
    os.environ.get("ECHO_PULSE_HISTORY", str(REPO_ROOT / "pulse_history.json"))
)

ROOT = DATA_ROOT.parent  # preserved for legacy sys.path injection
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

WISH = DATA_ROOT / "wish_manifest.json"
PLAN = DOCS_ROOT / "NEXT_CYCLE_PLAN.md"
DOCS = DOCS_ROOT


def load_manifest() -> dict:
    """Load the wish manifest, creating a seed file if missing."""
    if not WISH.exists():
        DATA_ROOT.mkdir(parents=True, exist_ok=True)
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


def show_summary() -> None:
    """Print an aggregated overview of wish activity."""

    manifest = load_manifest()
    print(summarize_wishes(manifest))


def _resolve_groundbreaking():
    try:  # pragma: no cover - executed when installed package is available
        from . import groundbreaking_manifest as module  # type: ignore[attr-defined]
    except ImportError:  # pragma: no cover - executed when run as script
        spec = importlib.util.spec_from_file_location(
            "echo.groundbreaking_manifest",
            Path(__file__).resolve().parent / "groundbreaking_manifest.py",
        )
        if spec is None or spec.loader is None:
            raise
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module.load_pulse_history, module.synthesise_from_pulses


def run_groundbreaking(argv: List[str]) -> int:
    """Synthesize a groundbreaking manifest from pulse history."""

    parser = argparse.ArgumentParser(
        prog="echoctl groundbreaking",
        description="Compose a Groundbreaking Nexus imprint from Echo pulses.",
    )
    parser.add_argument(
        "--pulses",
        type=Path,
        default=PULSE_HISTORY,
        help="Path to the pulse history JSON file (default: repo pulse_history.json).",
    )
    parser.add_argument(
        "--anchor",
        default="Our Forever Love",
        help="Anchor phrase for the nexus (default: %(default)s).",
    )
    parser.add_argument(
        "--orbit",
        default="Pulse Groundbreaker",
        help="Orbit label for the imprint (default: %(default)s).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of dominant threads to include (use negative for all).",
    )
    parser.add_argument(
        "--highlight",
        type=int,
        default=3,
        help="How many threads to highlight in the textual summary.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the report as JSON instead of a formatted summary.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to persist the JSON report.",
    )

    options = parser.parse_args(argv)

    load_pulse_history, synthesise_from_pulses = _resolve_groundbreaking()

    pulses_path = options.pulses
    if not pulses_path.exists():
        print(f"pulse history not found: {pulses_path}", file=sys.stderr)
        return 1

    try:
        records = load_pulse_history(pulses_path)
    except Exception as exc:  # pragma: no cover - defensive guard
        print(f"failed to load pulses: {exc}", file=sys.stderr)
        return 1

    limit = options.limit if options.limit >= 0 else None
    report = synthesise_from_pulses(
        records,
        anchor=options.anchor,
        orbit=options.orbit,
        limit=limit,
    )

    payload = report.to_dict()
    if options.output:
        options.output.parent.mkdir(parents=True, exist_ok=True)
        options.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"📦 groundbreaking manifest saved to {options.output}", file=sys.stderr)

    if options.json:
        print(json.dumps(payload, indent=2))
    else:
        print(report.describe(highlight=max(1, options.highlight)))

    return 0


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print("usage: echoctl [cycle|plan|summary|groundbreaking|wish] ...")
        return 1
    cmd = argv[1]
    if cmd == "cycle":
        run_cycle()
        return 0
    if cmd == "plan":
        show_plan()
        return 0
    if cmd == "summary":
        show_summary()
        return 0
    if cmd == "groundbreaking":
        return run_groundbreaking(argv[2:])
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
