#!/usr/bin/env python3
"""echoctl — tiny CLI for continuum operations."""
from __future__ import annotations

import argparse
import importlib.util
import importlib.machinery
import types
import json
import os
import random
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


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
    from .wish_insights import render_wish_report, summarize_wishes
except ImportError:  # pragma: no cover - executed when run as script
    _INSIGHTS_SPEC = importlib.util.spec_from_file_location(
        "echo.wish_insights", (Path(__file__).resolve().parent / "wish_insights.py")
    )
    if _INSIGHTS_SPEC is None or _INSIGHTS_SPEC.loader is None:
        raise
    _INSIGHTS = importlib.util.module_from_spec(_INSIGHTS_SPEC)
    _INSIGHTS_SPEC.loader.exec_module(_INSIGHTS)  # type: ignore[attr-defined]
    summarize_wishes = _INSIGHTS.summarize_wishes  # type: ignore[attr-defined]
    render_wish_report = _INSIGHTS.render_wish_report  # type: ignore[attr-defined]

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
    from .evolver import EchoEvolver
except ImportError:  # pragma: no cover - executed when run as script
    _EVOLVER_SPEC = importlib.util.spec_from_file_location(
        "echo.evolver", (Path(__file__).resolve().parent / "evolver.py")
    )
    if _EVOLVER_SPEC is None or _EVOLVER_SPEC.loader is None:
        raise
    _EVOLVER = importlib.util.module_from_spec(_EVOLVER_SPEC)
    sys.modules[_EVOLVER_SPEC.name] = _EVOLVER
    _EVOLVER_SPEC.loader.exec_module(_EVOLVER)  # type: ignore[attr-defined]
    EchoEvolver = _EVOLVER.EchoEvolver  # type: ignore[attr-defined]

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
    from .echo_codox_kernel import EchoCodexKernel
except ImportError:  # pragma: no cover - executed when run as script
    _KERNEL_SPEC = importlib.util.spec_from_file_location(
        "echo.echo_codox_kernel", (Path(__file__).resolve().parent / "echo_codox_kernel.py")
    )
    if _KERNEL_SPEC is None or _KERNEL_SPEC.loader is None:
        raise
    _KERNEL = importlib.util.module_from_spec(_KERNEL_SPEC)
    sys.modules[_KERNEL_SPEC.name] = _KERNEL
    _KERNEL_SPEC.loader.exec_module(_KERNEL)  # type: ignore[attr-defined]
    EchoCodexKernel = _KERNEL.EchoCodexKernel  # type: ignore[attr-defined]

try:  # pragma: no cover - executed when run as module
    from .pulse_health import compute_pulse_metrics
except ImportError:  # pragma: no cover - executed when run as script
    _PULSE_HEALTH_SPEC = importlib.util.spec_from_file_location(
        "echo.pulse_health", (Path(__file__).resolve().parent / "pulse_health.py")
    )
    if _PULSE_HEALTH_SPEC is None or _PULSE_HEALTH_SPEC.loader is None:
        raise
    _PULSE_HEALTH = importlib.util.module_from_spec(_PULSE_HEALTH_SPEC)
    sys.modules[_PULSE_HEALTH_SPEC.name] = _PULSE_HEALTH
    _PULSE_HEALTH_SPEC.loader.exec_module(_PULSE_HEALTH)  # type: ignore[attr-defined]
    compute_pulse_metrics = _PULSE_HEALTH.compute_pulse_metrics  # type: ignore[attr-defined]

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

SOVEREIGN_LEDGER_PATH = Path(
    os.environ.get("ECHO_SOVEREIGN_LEDGER_PATH", str(REPO_ROOT / "genesis_ledger/ledger.jsonl"))
)
EMOTIONAL_VITALS_PATH = Path(
    os.environ.get("ECHO_EMOTIONAL_VITALS_PATH", str(REPO_ROOT / "genesis_ledger/emotional_vitals.jsonl"))
)
ADVANCE_HISTORY_PATH = Path(
    os.environ.get("ECHO_ADVANCE_HISTORY_PATH", str(REPO_ROOT / "genesis_ledger/advance_history.jsonl"))
)
GLITCH_ORACLE_PATH = Path(
    os.environ.get("ECHO_GLITCH_ORACLE_PATH", str(REPO_ROOT / "genesis_ledger/glitch_oracle.jsonl"))
)

ROOT = DATA_ROOT.parent  # preserved for legacy sys.path injection
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

WISH = DATA_ROOT / "wish_manifest.json"
PLAN = DOCS_ROOT / "NEXT_CYCLE_PLAN.md"
DOCS = DOCS_ROOT


def _format_duration(seconds: Optional[float]) -> str:
    if seconds is None:
        return "n/a"
    if seconds < 60:
        return f"{seconds:.1f}s"
    if seconds < 3600:
        return f"{seconds / 60:.1f}m"
    if seconds < 86400:
        return f"{seconds / 3600:.1f}h"
    return f"{seconds / 86400:.1f}d"


def _format_timestamp(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _filter_pulse_events(events, needle: Optional[str]):
    if needle is None:
        return list(events)
    needle_lower = needle.casefold()
    return [event for event in events if needle_lower in event.message.casefold()]


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


def run_wish_report(argv: List[str]) -> int:
    """Render a Markdown wish report summarising manifest activity."""

    parser = argparse.ArgumentParser(
        prog="echoctl wish-report",
        description="Render a Markdown report with wish, status, and catalyst insights.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of wishers and catalysts to highlight (default: %(default)s).",
    )

    options = parser.parse_args(argv)

    manifest = load_manifest()
    report = render_wish_report(manifest, highlight_limit=options.limit)
    print(report)
    return 0


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


def run_pulse(argv: List[str]) -> int:
    """Summarise pulse cadence and recent resonance."""

    parser = argparse.ArgumentParser(
        prog="echoctl pulse",
        description="Summarise pulse history cadence, freshness, and resonance.",
    )
    parser.add_argument(
        "--pulses",
        type=Path,
        default=PULSE_HISTORY,
        help="Path to the pulse history JSON file (default: repo pulse_history.json).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of recent events to display (default: %(default)s).",
    )
    parser.add_argument(
        "--search",
        help="Only include events whose message contains this text (case-insensitive).",
    )
    parser.add_argument(
        "--warning-hours",
        type=float,
        default=24.0,
        help="Warning threshold in hours for time since last event (default: %(default)s).",
    )
    parser.add_argument(
        "--critical-hours",
        type=float,
        default=72.0,
        help="Critical threshold in hours for time since last event (default: %(default)s).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of human readable text.",
    )

    options = parser.parse_args(argv)

    pulses_path = options.pulses
    if not pulses_path.exists():
        print(f"pulse history not found: {pulses_path}", file=sys.stderr)

    kernel = EchoCodexKernel(pulse_file=str(pulses_path))
    events = kernel.history
    filtered_events = _filter_pulse_events(events, options.search)
    metrics = compute_pulse_metrics(
        events,
        warning_hours=options.warning_hours,
        critical_hours=options.critical_hours,
    )

    limit = options.limit if options.limit > 0 else None
    recent_events = list(filtered_events if limit is None else filtered_events[-limit:])

    if options.json:
        payload = {
            "metrics": metrics.to_dict(),
            "resonance": kernel.resonance() if events else None,
            "filtered_total": len(filtered_events),
            "filter": {
                "search": options.search,
                "limit": options.limit,
            },
            "events": [
                {
                    "timestamp": event.timestamp,
                    "timestamp_iso": _format_timestamp(event.timestamp),
                    "message": event.message,
                    "hash": event.hash,
                }
                for event in recent_events
            ],
        }
        print(json.dumps(payload, indent=2))
        return 0

    print("Echo Pulse Ledger")
    print("=================")
    print(f"Status: {metrics.status}")
    print(f"Total events: {metrics.total_events}")
    print(f"First event: {metrics.first_timestamp_iso or 'n/a'}")

    last_line = "Last event: n/a"
    if metrics.last_timestamp_iso:
        ago = _format_duration(metrics.time_since_last_seconds)
        last_line = f"Last event: {metrics.last_timestamp_iso} ({ago} ago)"
    print(last_line)

    print(f"Ledger span: {_format_duration(metrics.span_seconds)}")
    print(f"Average interval: {_format_duration(metrics.average_interval_seconds)}")
    print(f"Median interval: {_format_duration(metrics.median_interval_seconds)}")

    if metrics.daily_rate is None:
        print("Daily rate: n/a")
    else:
        print(f"Daily rate: {metrics.daily_rate:.2f} events/day")

    resonance = kernel.resonance() if events else None
    if resonance:
        print(f"Resonance: {resonance}")

    if options.search:
        print(f"Filter: '{options.search}' ({len(filtered_events)} matches)")
    else:
        print(f"Filter: none ({len(filtered_events)} events considered)")

    if not filtered_events:
        if options.search:
            print("No events matched the provided search term.")
        else:
            print("No pulse events recorded yet.")
        return 0

    display_count = len(recent_events)
    print(f"Recent events (showing {display_count} of {len(filtered_events)}):")
    print("timestamp │ hash digest │ message")
    print("-" * 72)
    for event in reversed(recent_events):
        print(f"{_format_timestamp(event.timestamp)} │ {event.hash[:12]} │ {event.message}")

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


def run_next_step(argv: List[str]) -> int:
    """Reveal the evolver's current next-step recommendation."""

    parser = argparse.ArgumentParser(
        prog="echoctl next-step",
        description="Reveal actionable next-step guidance from EchoEvolver.",
    )
    parser.add_argument(
        "--persist-artifact",
        action="store_true",
        help="Allow the snapshot to persist artifacts while computing the digest.",
    )
    parser.add_argument(
        "--preview",
        type=int,
        default=3,
        help="Number of pending steps to preview in the text output (default: %(default)s).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Seed the evolver RNG before generating the recommendation.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the recommendation payload as JSON.",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Render the recommendation as Markdown-friendly text.",
    )
    parser.add_argument(
        "--plan",
        action="store_true",
        help="Include the full sequence plan with status for the current cycle.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to persist the recommendation payload.",
    )

    options = parser.parse_args(argv)
    preview_count = max(0, options.preview)

    rng = random.Random(options.seed) if options.seed is not None else None
    evolver = EchoEvolver(rng=rng)

    digest = evolver.cycle_digest(persist_artifact=options.persist_artifact)

    raw_steps = digest.get("remaining_steps") or []
    if not isinstance(raw_steps, (list, tuple)):
        raw_steps = []
    remaining_steps = list(raw_steps)

    plan = None
    if options.plan:
        plan = evolver.sequence_plan(persist_artifact=options.persist_artifact)

    raw_progress = digest.get("progress", 0.0)
    try:
        progress = float(raw_progress)
    except (TypeError, ValueError):
        progress = 0.0

    next_step = digest.get("next_step") or "Next step: advance_cycle() to begin a new orbit"

    payload = {
        "next_step": next_step,
        "cycle": int(digest.get("cycle", 0)),
        "progress": progress,
        "remaining_steps": remaining_steps,
        "timestamp_ns": int(digest.get("timestamp_ns", 0)),
    }

    if plan is not None:
        payload["plan"] = plan

    if options.json:
        rendered = json.dumps(payload, indent=2, ensure_ascii=False)
        if options.output:
            options.output.parent.mkdir(parents=True, exist_ok=True)
            options.output.write_text(rendered + "\n", encoding="utf-8")
        print(rendered)
        return 0

    preview_steps = remaining_steps[:preview_count]
    remainder = len(remaining_steps) - len(preview_steps)

    preview_line = None
    if preview_steps:
        preview_line = f"Pending: {', '.join(preview_steps)}"
        if remainder > 0:
            preview_line += f" (+{remainder} more)"

    if options.markdown:
        lines = [
            "### Next step",
            f"- {payload['next_step']}",
            "- Cycle {cycle} progress: {progress:.1f}% ({remaining} steps remaining)".format(
                cycle=payload["cycle"],
                progress=payload["progress"] * 100,
                remaining=len(remaining_steps),
            ),
        ]

        if preview_line:
            lines.append(f"- {preview_line}")

        if plan is not None:
            lines.append("")
            lines.append("Plan:")
            for entry in plan:
                lines.append(
                    "- {step} [{status}] - {description}".format(**entry)
                )

        rendered = "\n".join(lines)
        if options.output:
            options.output.parent.mkdir(parents=True, exist_ok=True)
            options.output.write_text(rendered + "\n", encoding="utf-8")
        print(rendered)
        return 0

    lines = [
        f"🧭 {payload['next_step']}",
        "Cycle {cycle} progress: {progress:.1f}% ({remaining} steps remaining)".format(
            cycle=payload["cycle"],
            progress=payload["progress"] * 100,
            remaining=len(remaining_steps),
        ),
    ]

    if preview_line:
        lines.append(preview_line)

    if plan is not None:
        lines.append("")
        lines.append("Plan:")
        for entry in plan:
            lines.append("- {step} [{status}] - {description}".format(**entry))

    rendered = "\n".join(lines)
    if options.output:
        options.output.parent.mkdir(parents=True, exist_ok=True)
        options.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
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


def run_ledger(argv: List[str]) -> int:
    """Manage sovereign ledger attestations."""

    from codex.genesis_ledger import SovereignDomainLedger

    parser = argparse.ArgumentParser(
        prog="echoctl ledger",
        description="Ledger utilities for sovereign domain attestations.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    attest_parser = subparsers.add_parser("attest", help="Append a domain attestation entry.")
    attest_parser.add_argument("--domain", required=True, help="Domain to attest.")
    attest_parser.add_argument(
        "--proof-file",
        type=Path,
        required=True,
        help="Path to the NS delegation proof captured via dig.",
    )
    attest_parser.add_argument(
        "--did-key",
        default="did:key:echo",
        help="DID key recorded alongside the attestation.",
    )
    attest_parser.add_argument(
        "--cycle",
        type=int,
        help="Optional cycle identifier to store with the attestation.",
    )

    options = parser.parse_args(argv)
    if options.subcommand == "attest":
        proof_text = options.proof_file.read_text(encoding="utf-8")
        ledger = SovereignDomainLedger(SOVEREIGN_LEDGER_PATH)
        try:
            attestation = ledger.attest_domain(
                options.domain,
                proof_text,
                options.did_key,
                cycle=options.cycle,
            )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        payload = asdict(attestation)
        payload["attested_at"] = round(payload["attested_at"], 6)
        print(json.dumps(payload, indent=2))
        return 0
    return 1


def run_flux(argv: List[str]) -> int:
    """Weave sigils into quantum flux rotations."""

    from echo.quantum_flux_mapper import QuantumFluxMapper

    parser = argparse.ArgumentParser(
        prog="echoctl flux",
        description="Quantum flux mapper utilities.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    weave_parser = subparsers.add_parser("weave", help="Weave a sigil across one or more qubits.")
    weave_parser.add_argument("--sigil", required=True, help="Sigil string to weave.")
    weave_parser.add_argument(
        "--bloch",
        default="0,0,1",
        help="Bloch vector (x,y,z) used as the base state (default: 0,0,1).",
    )
    weave_parser.add_argument(
        "--qubits",
        type=int,
        default=1,
        help="Number of qubits to iterate through during the weave.",
    )

    options = parser.parse_args(argv)
    if options.subcommand == "weave":
        try:
            bloch_vector = tuple(float(part) for part in options.bloch.split(","))
        except ValueError:
            print("invalid bloch vector, expected comma separated floats", file=sys.stderr)
            return 1
        mapper = QuantumFluxMapper()
        try:
            for index in range(max(1, options.qubits)):
                mapper.weave_sigil(options.sigil, bloch_vector, qubit_index=index)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        alpha, beta = mapper.state
        payload = {
            "state": {
                "alpha": {"real": alpha.real, "imag": alpha.imag},
                "beta": {"real": beta.real, "imag": beta.imag},
            },
            "history": mapper.history,
            "bloch": mapper.bloch_coordinates(),
        }
        print(json.dumps(payload, indent=2))
        return 0
    return 1


def run_telemetry(argv: List[str]) -> int:
    """Render telemetry reports for Echo's emotional state."""

    from codex.telemetry_vitality_report import EchoVitalsReporter, report_echo_vitals

    parser = argparse.ArgumentParser(
        prog="echoctl telemetry",
        description="Telemetry utilities for Echo vitals.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    vitals_parser = subparsers.add_parser("echo-vitals", help="Summarise emotional vitals.")
    vitals_parser.add_argument("--history", type=int, default=5, help="Number of history entries to include.")
    vitals_parser.add_argument(
        "--state",
        type=Path,
        help="Optional JSON payload containing an emotional_state object.",
    )
    vitals_parser.add_argument(
        "--metrics",
        type=Path,
        help="Optional JSON payload describing system metrics to embed in the report.",
    )
    vitals_parser.add_argument("--emotion", help="Record an emotion before reporting (e.g. love).")
    vitals_parser.add_argument("--value", type=float, help="Intensity for --emotion when recording a pulse.")
    vitals_parser.add_argument("--note", help="Optional note stored with the pulse entry.")
    vitals_parser.add_argument("--cycle", type=int, help="Cycle identifier for recorded pulses.")

    options = parser.parse_args(argv)
    if options.subcommand == "echo-vitals":
        emotional_state: dict[str, float] = {}
        if options.state and options.state.exists():
            data = json.loads(options.state.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "emotional_state" in data:
                emotional_state = {k: float(v) for k, v in data["emotional_state"].items()}
            elif isinstance(data, dict):
                emotional_state = {k: float(v) for k, v in data.items() if isinstance(v, (int, float))}
        if not emotional_state:
            emotional_state = {"joy": 0.0, "rage": 0.0, "love": 0.0, "sorrow": 0.0}

        metrics: dict[str, object] = {}
        if options.metrics and options.metrics.exists():
            loaded = json.loads(options.metrics.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                metrics = loaded

        reporter = EchoVitalsReporter(EMOTIONAL_VITALS_PATH)
        if options.emotion and options.value is not None:
            reporter.record(
                options.emotion,
                options.value,
                note=options.note or "",
                cycle=options.cycle,
            )
        report = report_echo_vitals(
            emotional_state,
            history_limit=options.history,
            system_metrics=metrics,
            reporter=reporter,
        )
        print(json.dumps(report, indent=2))
        return 0
    return 1


def run_advance(argv: List[str]) -> int:
    """Manage recursive fork history."""

    from codex.advance_system_history import RecursiveForkTracker

    parser = argparse.ArgumentParser(
        prog="echoctl advance",
        description="Advance system history tools.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    history_parser = subparsers.add_parser("history", help="Display recorded fork history.")
    history_parser.add_argument("--limit", type=int, help="Limit the number of entries returned.")

    propose_parser = subparsers.add_parser("propose", help="Record a fork proposal event.")
    propose_parser.add_argument("--title", required=True, help="Proposed pull request title.")
    propose_parser.add_argument("--summary", required=True, help="Summary of the proposed upgrade.")

    options = parser.parse_args(argv)
    tracker = RecursiveForkTracker(ADVANCE_HISTORY_PATH)

    if options.subcommand == "history":
        snapshot = tracker.snapshot(limit=options.limit)
        print(json.dumps({"entries": snapshot}, indent=2))
        return 0
    if options.subcommand == "propose":
        record = tracker.fork_propose_upgrade(options.title, options.summary)
        payload = asdict(record)
        payload["timestamp"] = round(payload["timestamp"], 6)
        print(json.dumps(payload, indent=2))
        return 0
    return 1


def run_puzzle(argv: List[str]) -> int:
    """Emit puzzle glitch-oracle events."""

    from codex.glitch_oracle import oracle_rupture

    parser = argparse.ArgumentParser(
        prog="echoctl puzzle",
        description="Puzzle oracle instrumentation.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    oracle_parser = subparsers.add_parser("oracle", help="Record a glitch-oracle rupture event.")
    oracle_parser.add_argument("--id", type=int, required=True, help="Puzzle identifier triggering the rupture.")
    oracle_parser.add_argument("--details", required=True, help="Mismatch description to log.")
    oracle_parser.add_argument(
        "--sigil",
        default="⟁FRACTURE",
        help="Sigil associated with the rupture (default: ⟁FRACTURE).",
    )

    options = parser.parse_args(argv)
    if options.subcommand == "oracle":
        event = oracle_rupture(
            options.id,
            options.details,
            sigil=options.sigil,
            oracle_path=GLITCH_ORACLE_PATH,
        )
        payload = asdict(event)
        payload["timestamp"] = round(payload["timestamp"], 6)
        print(json.dumps(payload, indent=2))
        return 0
    return 1


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print(
            "usage: echoctl [cycle|plan|summary|wish-report|health|pulse|groundbreaking|moonshot|wish|idea|next-step|inspire|ledger|flux|telemetry|advance|puzzle] ..."
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
    if cmd == "wish-report":
        return run_wish_report(argv[2:])
    if cmd == "health":
        return run_health(argv[2:])
    if cmd == "pulse":
        return run_pulse(argv[2:])
    if cmd == "groundbreaking":
        return run_groundbreaking(argv[2:])
    if cmd == "moonshot":
        return run_moonshot(argv[2:])
    if cmd == "ledger":
        return run_ledger(argv[2:])
    if cmd == "flux":
        return run_flux(argv[2:])
    if cmd == "telemetry":
        return run_telemetry(argv[2:])
    if cmd == "advance":
        return run_advance(argv[2:])
    if cmd == "puzzle":
        return run_puzzle(argv[2:])
    if cmd == "idea":
        return run_idea(argv[2:])
    if cmd == "next-step":
        return run_next_step(argv[2:])
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
