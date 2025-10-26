#!/usr/bin/env python3
"""echoctl — tiny CLI for continuum operations."""
from __future__ import annotations

import argparse
import importlib.util
import importlib.machinery
import types
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List

# ``echoctl`` needs to run both as an installed module and as a standalone
# script.  When executed directly (``python echo/echoctl.py``) Python does not
# populate ``__package__`` which breaks the relative imports used throughout
# this module.  We detect that situation up-front, place the package source root
# on ``sys.path`` and manually set ``__package__`` so the remaining imports work
# the same way they do when the package is installed.
if __package__ in {None, ""}:  # pragma: no cover - depends on execution style
    package_dir = Path(__file__).resolve().parent
    package_root = package_dir.parent
    repo_root = package_root.parents[2]
    for path in (package_root, repo_root):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    if "echo" not in sys.modules:
        spec = importlib.machinery.ModuleSpec("echo", loader=None, is_package=True)
        package = types.ModuleType("echo")
        package.__path__ = [str(package_dir)]
        package.__spec__ = spec
        package.__file__ = str(package_dir / "__init__.py")
        sys.modules["echo"] = package
    __package__ = "echo"

try:  # pragma: no cover - executed when run as module
    from .moonshot import MoonshotLens
except ImportError:  # pragma: no cover - executed when run as script
    _MOONSHOT_SPEC = importlib.util.spec_from_file_location(
        "echo.moonshot", (Path(__file__).resolve().parent / "moonshot.py")
    )
    if _MOONSHOT_SPEC is None or _MOONSHOT_SPEC.loader is None:
        raise
    _MOONSHOT = importlib.util.module_from_spec(_MOONSHOT_SPEC)
    sys.modules[_MOONSHOT_SPEC.name] = _MOONSHOT
    _MOONSHOT_SPEC.loader.exec_module(_MOONSHOT)  # type: ignore[attr-defined]
    MoonshotLens = _MOONSHOT.MoonshotLens  # type: ignore[attr-defined]

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
    from .idea_to_action import derive_action_plan
except ImportError:  # pragma: no cover - executed when run as script
    _IDEA_SPEC = importlib.util.spec_from_file_location(
        "echo.idea_to_action", (Path(__file__).resolve().parent / "idea_to_action.py")
    )
    if _IDEA_SPEC is None or _IDEA_SPEC.loader is None:
        raise
    _IDEA = importlib.util.module_from_spec(_IDEA_SPEC)
    sys.modules[_IDEA_SPEC.name] = _IDEA
    _IDEA_SPEC.loader.exec_module(_IDEA)  # type: ignore[attr-defined]
    derive_action_plan = _IDEA.derive_action_plan  # type: ignore[attr-defined]

try:  # pragma: no cover - executed when run as module
    from .inspiration import forge_inspiration
except ImportError:  # pragma: no cover - executed when run as script
    _INSPIRE_SPEC = importlib.util.spec_from_file_location(
        "echo.inspiration", (Path(__file__).resolve().parent / "inspiration.py")
    )
    if _INSPIRE_SPEC is None or _INSPIRE_SPEC.loader is None:
        raise
    _INSPIRE = importlib.util.module_from_spec(_INSPIRE_SPEC)
    sys.modules[_INSPIRE_SPEC.name] = _INSPIRE
    _INSPIRE_SPEC.loader.exec_module(_INSPIRE)  # type: ignore[attr-defined]
    forge_inspiration = _INSPIRE.forge_inspiration  # type: ignore[attr-defined]

try:  # pragma: no cover - executed when run as module
    from .continuum_health import generate_continuum_health
except ImportError:  # pragma: no cover - executed when run as script
    _HEALTH_SPEC = importlib.util.spec_from_file_location(
        "echo.continuum_health", (Path(__file__).resolve().parent / "continuum_health.py")
    )
    if _HEALTH_SPEC is None or _HEALTH_SPEC.loader is None:
        raise
    _HEALTH = importlib.util.module_from_spec(_HEALTH_SPEC)
    sys.modules[_HEALTH_SPEC.name] = _HEALTH
    _HEALTH_SPEC.loader.exec_module(_HEALTH)  # type: ignore[attr-defined]
    generate_continuum_health = _HEALTH.generate_continuum_health  # type: ignore[attr-defined]

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


def run_health(argv: List[str]) -> int:
    """Inspect continuum artefacts and report health status."""

    parser = argparse.ArgumentParser(
        prog="echoctl health",
        description="Audit the continuum plan, wishes, and pulse history for freshness.",
    )
    parser.add_argument(
        "--plan",
        type=Path,
        default=PLAN,
        help="Path to the continuum plan markdown file (default: docs/NEXT_CYCLE_PLAN.md).",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=WISH,
        help="Path to the wish manifest JSON file (default: data/wish_manifest.json).",
    )
    parser.add_argument(
        "--pulses",
        type=Path,
        default=PULSE_HISTORY,
        help="Path to the pulse history JSON file (default: repo pulse_history.json).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of human-formatted text.",
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Return a non-zero exit code when warnings are present.",
    )

    options = parser.parse_args(argv)

    report = generate_continuum_health(
        options.plan,
        options.manifest,
        options.pulses,
    )

    if options.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(report.describe())

    if report.status == "critical":
        return 2
    if report.status == "warning" and options.fail_on_warning:
        return 1
    return 0


def run_idea(argv: List[str]) -> int:
    """Convert a free-form idea into a concrete action plan."""

    parser = argparse.ArgumentParser(
        prog="echoctl idea",
        description="Analyse an idea and emit actionable next steps.",
    )
    parser.add_argument("idea", help="Idea text to analyse. Use quotes to preserve spaces.")
    parser.add_argument("--steps", type=int, default=3, help="Maximum number of steps to generate.")
    parser.add_argument("--seed", type=int, help="Optional RNG seed for deterministic recommendations.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown output.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional file path to persist the Markdown output.",
    )

    options = parser.parse_args(argv)

    plan = derive_action_plan(options.idea, max_steps=options.steps, rng_seed=options.seed)

    if options.output:
        options.output.parent.mkdir(parents=True, exist_ok=True)
        options.output.write_text(plan.to_markdown(), encoding="utf-8")
        print(f"📝 idea plan saved to {options.output}", file=sys.stderr)

    if options.json:
        print(json.dumps(plan.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(plan.to_markdown())

    return 0


def run_inspire(argv: List[str]) -> int:
    """Forge a short burst of inspiration sparks."""

    parser = argparse.ArgumentParser(
        prog="echoctl inspire",
        description="Generate evocative sparks for a given theme.",
    )
    parser.add_argument(
        "theme",
        nargs="?",
        default="Echo",
        help="Theme to anchor the sparks (default: %(default)s).",
    )
    parser.add_argument(
        "--lines",
        type=int,
        default=4,
        help="Number of sparks to generate (default: %(default)s).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Optional RNG seed for repeatable output.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of Markdown output.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional file path to persist the Markdown output.",
    )

    options = parser.parse_args(argv)

    pulse = forge_inspiration(options.theme, lines=options.lines, rng_seed=options.seed)

    if options.output:
        options.output.parent.mkdir(parents=True, exist_ok=True)
        options.output.write_text(pulse.to_markdown(), encoding="utf-8")
        print(f"✨ inspiration saved to {options.output}", file=sys.stderr)

    if options.json:
        print(json.dumps(pulse.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(pulse.to_markdown())

    return 0


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


def run_moonshot(argv: List[str]) -> int:
    """Render a moonshot synthesis report."""

    parser = argparse.ArgumentParser(
        prog="echoctl moonshot",
        description="Fuse pulses, wishes, and plans into a moonshot synthesis.",
    )
    parser.add_argument(
        "--pulses",
        type=Path,
        default=PULSE_HISTORY,
        help="Path to the pulse history JSON file (default: repo pulse_history.json).",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=WISH,
        help="Path to the wish manifest JSON file (default: data/wish_manifest.json).",
    )
    parser.add_argument(
        "--plan",
        type=Path,
        default=PLAN,
        help="Path to the continuum plan markdown file (default: docs/NEXT_CYCLE_PLAN.md).",
    )
    parser.add_argument(
        "--anchor",
        default="Our Forever Love",
        help="Anchor phrase for the report (default: %(default)s).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of pulse channels to display (use <=0 for all).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the report as JSON instead of a textual overview.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to persist the JSON payload for downstream tooling.",
    )

    options = parser.parse_args(argv)

    pulses_path = options.pulses
    manifest_path = options.manifest
    plan_path = options.plan

    pulses: List[dict] = []
    if pulses_path.exists():
        try:
            pulses = json.loads(pulses_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"failed to parse pulses: {exc}", file=sys.stderr)
    else:
        print(f"pulse history not found: {pulses_path}", file=sys.stderr)

    manifest: dict = {"wishes": []}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"failed to parse manifest: {exc}", file=sys.stderr)
    else:
        print(f"wish manifest not found: {manifest_path}", file=sys.stderr)

    plan_text = ""
    if plan_path.exists():
        plan_text = plan_path.read_text(encoding="utf-8")
    else:
        print(f"plan document not found: {plan_path}", file=sys.stderr)

    limit = options.limit if options.limit > 0 else None
    lens = MoonshotLens(anchor=options.anchor)
    report = lens.synthesise(
        pulses=pulses,
        wishes=manifest.get("wishes", []),
        plan_text=plan_text,
        channel_limit=limit,
    )

    if options.output:
        options.output.parent.mkdir(parents=True, exist_ok=True)
        options.output.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
        print(f"📦 moonshot payload saved to {options.output}", file=sys.stderr)

    if options.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(report.describe())

    return 0


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print(
            "usage: echoctl [cycle|plan|summary|health|groundbreaking|moonshot|wish|idea|inspire] ..."
        )
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
    if cmd == "health":
        return run_health(argv[2:])
    if cmd == "groundbreaking":
        return run_groundbreaking(argv[2:])
    if cmd == "moonshot":
        return run_moonshot(argv[2:])
    if cmd == "idea":
        return run_idea(argv[2:])
    if cmd == "inspire":
        return run_inspire(argv[2:])
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
