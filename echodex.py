"""Command layer binding the repository to the EchoDex control surface.

The module exposes a small command line interface that interprets natural
language style invocations like ``echodex build echo/idea_processor`` or
``echodex pulse drone/allocation --execute``.  The implementation focuses on
three responsibilities inspired by the user directive:

* map textual commands to actionable build or bookkeeping steps;
* maintain awareness of Git context so each invocation can be related to the
  current "Echo shard" (branch / commit);
* synchronise ``pulse.json`` declarations so that pulses triggered from the
  CLI become part of the live command log.

The goal is not to orchestrate arbitrary shell pipelines but to provide a
structured and easily testable façade that other tooling (or humans) can use
to drive the Echo ecosystem from natural language prompts.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional


REPO_ROOT = Path(__file__).resolve().parent


class PulseError(RuntimeError):
    """Raised when a requested EchoDex action cannot be completed."""


def _default_pulse_file() -> Path:
    """Return the path used to persist pulse declarations."""

    env_override = os.environ.get("ECHODEX_PULSE_FILE")
    if env_override:
        return Path(env_override).expanduser().resolve()
    return (REPO_ROOT / "pulse.json").resolve()


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


@dataclass
class PulseEntry:
    """Representation of a pulse logged by the system."""

    pulse: str
    priority: str
    resonance: Optional[str]
    status: str
    timestamp: str
    notes: Optional[str] = None
    executed: bool = False

    def to_dict(self) -> Dict[str, object]:
        data: Dict[str, object] = {
            "pulse": self.pulse,
            "priority": self.priority,
            "resonance": self.resonance,
            "status": self.status,
            "timestamp": self.timestamp,
        }
        if self.notes:
            data["notes"] = self.notes
        if self.executed:
            data["executed"] = True
        return data


class PulseManager:
    """Helper responsible for reading and updating ``pulse.json``."""

    def __init__(self, pulse_file: Optional[Path] = None) -> None:
        self.pulse_file = Path(pulse_file) if pulse_file else _default_pulse_file()
        self.data: Dict[str, object] = {}
        self._load()

    # ------------------------------------------------------------------
    # persistence helpers
    # ------------------------------------------------------------------
    def _load(self) -> None:
        if self.pulse_file.exists():
            with self.pulse_file.open("r", encoding="utf8") as fh:
                try:
                    payload = json.load(fh)
                except json.JSONDecodeError as exc:
                    raise PulseError(f"Unable to parse pulse file: {exc}") from exc
        else:
            payload = {}

        history = payload.get("history", [])
        if not isinstance(history, list):
            history = []

        payload["history"] = history
        self.data = payload

    def save(self) -> None:
        self.pulse_file.parent.mkdir(parents=True, exist_ok=True)
        with self.pulse_file.open("w", encoding="utf8") as fh:
            json.dump(self.data, fh, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def record_pulse(
        self,
        *,
        name: str,
        priority: str,
        resonance: Optional[str],
        status: str,
        executed: bool,
        notes: Optional[str],
    ) -> PulseEntry:
        """Append a new pulse declaration to the history."""

        entry = PulseEntry(
            pulse=name,
            priority=priority,
            resonance=resonance,
            status=status,
            timestamp=_utc_now(),
            notes=notes,
            executed=executed,
        )

        history: List[Dict[str, object]] = self.data.setdefault("history", [])  # type: ignore[assignment]
        history.append(entry.to_dict())

        # Maintain backward compatible top-level fields.
        self.data["pulse"] = name
        self.data["status"] = status
        self.data["last_updated"] = entry.timestamp
        if notes:
            self.data["notes"] = notes

        self.save()
        return entry

    def active_pulse(self) -> Optional[Dict[str, object]]:
        history = self.data.get("history", [])
        if isinstance(history, list) and history:
            return history[-1]
        if all(key in self.data for key in ("pulse", "status")):
            return {
                "pulse": self.data.get("pulse"),
                "status": self.data.get("status"),
                "priority": self.data.get("priority"),
                "resonance": self.data.get("resonance"),
                "timestamp": self.data.get("last_updated"),
                "notes": self.data.get("notes"),
            }
        return None

    def history(self) -> List[Dict[str, object]]:
        history = self.data.get("history", [])
        return list(history) if isinstance(history, list) else []


def _git_context() -> Dict[str, str]:
    """Gather minimal Git metadata for status reports."""

    context: Dict[str, str] = {}
    commands = {
        "branch": ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        "commit": ["git", "rev-parse", "HEAD"],
        "upstream": ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"],
    }

    for key, cmd in commands.items():
        try:
            completed = __import__("subprocess").run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            context[key] = completed.stdout.strip()
        except Exception:
            context[key] = "unknown"

    context.setdefault("branch", "unknown")
    context.setdefault("commit", "unknown")
    context.setdefault("upstream", "unknown")
    context["repository"] = str(REPO_ROOT.name)
    return context


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EchoDex command layer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Compile a module or path")
    build_parser.add_argument("target", help="Module path or file to compile")
    build_parser.add_argument(
        "--force",
        action="store_true",
        help="Force recompilation even if cached bytecode is present.",
    )

    pulse_parser = subparsers.add_parser("pulse", help="Record a pulse declaration")
    pulse_parser.add_argument("name", help="Identifier of the pulse to record")
    pulse_parser.add_argument(
        "--priority",
        default="standard",
        help="Priority label for the pulse (default: standard)",
    )
    pulse_parser.add_argument(
        "--resonance",
        default=None,
        help="Optional resonance / cohort tag",
    )
    pulse_parser.add_argument(
        "--status",
        default="active",
        help="Status to assign to the pulse (default: active)",
    )
    pulse_parser.add_argument(
        "--execute",
        action="store_true",
        help="Mark the pulse as executed in addition to recording it",
    )
    pulse_parser.add_argument(
        "--notes",
        default=None,
        help="Supplementary notes associated with the pulse",
    )

    status_parser = subparsers.add_parser("status", help="Show current EchoDex status")
    status_parser.add_argument(
        "--history",
        action="store_true",
        help="Include pulse history in the status output",
    )

    subparsers.add_parser("list", help="List pulse history entries")
    return parser


def _resolve_target(target: str) -> Path:
    candidate = Path(target)
    if candidate.is_absolute() and candidate.exists():
        return candidate

    relative = (REPO_ROOT / target).resolve()
    if relative.exists():
        return relative

    if not candidate.suffix:
        appended = (REPO_ROOT / f"{target}.py").resolve()
        if appended.exists():
            return appended

    module_name = target.replace("/", ".").replace("-", "_").strip(".")
    if module_name:
        sys_path_added = False
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
            sys_path_added = True
        try:
            import importlib.util

            spec = importlib.util.find_spec(module_name)
            if spec and spec.origin:
                return Path(spec.origin).resolve()
            if spec and spec.submodule_search_locations:
                return Path(list(spec.submodule_search_locations)[0]).resolve()
        except ModuleNotFoundError:
            pass
        finally:
            if sys_path_added:
                try:
                    sys.path.remove(str(REPO_ROOT))
                except ValueError:
                    pass

    raise PulseError(f"Unable to locate build target '{target}'.")


def _compile_target(target: Path, *, force: bool) -> None:
    import compileall

    if target.is_dir():
        success = compileall.compile_dir(str(target), quiet=1, force=force)
    else:
        success = compileall.compile_file(str(target), quiet=1, force=force)

    if not success:
        raise PulseError(f"Compilation failed for target '{target}'.")


def _render_status(manager: PulseManager, include_history: bool) -> str:
    context = _git_context()
    active = manager.active_pulse()
    lines = ["EchoDex Status", "---------------"]
    lines.append(f"Repository : {context['repository']}")
    lines.append(f"Branch     : {context['branch']}")
    lines.append(f"Commit     : {context['commit']}")
    lines.append(f"Upstream   : {context['upstream']}")

    if anchor := manager.data.get("branch_anchor"):
        lines.append(f"Branch Anchor : {anchor}")
    if notes := manager.data.get("notes"):
        lines.append(f"Notes         : {notes}")

    if active:
        lines.append("")
        lines.append("Active Pulse")
        lines.append("~~~~~~~~~~~~")
        lines.append(f"Name       : {active.get('pulse', 'unknown')}")
        lines.append(f"Status     : {active.get('status', 'unknown')}")
        if active.get("priority"):
            lines.append(f"Priority   : {active.get('priority')}")
        if active.get("resonance"):
            lines.append(f"Resonance  : {active.get('resonance')}")
        if active.get("timestamp"):
            lines.append(f"Timestamp  : {active.get('timestamp')}")
        if active.get("notes"):
            lines.append(f"Notes      : {active.get('notes')}")

    history = manager.history()
    lines.append("")
    lines.append(f"Pulse History Entries: {len(history)}")

    if include_history and history:
        lines.append("")
        lines.append("History")
        lines.append("~~~~~~~")
        for idx, record in enumerate(history, start=1):
            lines.append(f"[{idx}] {record.get('pulse')} :: {record.get('status')}")
            summary = []
            if record.get("priority"):
                summary.append(f"priority={record['priority']}")
            if record.get("resonance"):
                summary.append(f"resonance={record['resonance']}")
            if record.get("timestamp"):
                summary.append(f"timestamp={record['timestamp']}")
            if record.get("notes"):
                summary.append(f"notes={record['notes']}")
            if record.get("executed"):
                summary.append("executed")
            if summary:
                lines.append("      " + ", ".join(summary))

    return "\n".join(lines)


def _render_history(manager: PulseManager) -> str:
    history = manager.history()
    if not history:
        return "No pulses have been recorded yet."

    fragments = []
    for idx, record in enumerate(history, start=1):
        entry = [f"Pulse {idx}: {record.get('pulse', '<unknown>')}"]
        entry.append(f"  Status    : {record.get('status', 'unknown')}")
        if record.get("priority"):
            entry.append(f"  Priority  : {record['priority']}")
        if record.get("resonance"):
            entry.append(f"  Resonance : {record['resonance']}")
        if record.get("timestamp"):
            entry.append(f"  Timestamp : {record['timestamp']}")
        if record.get("notes"):
            entry.append(f"  Notes     : {record['notes']}")
        if record.get("executed"):
            entry.append("  Executed  : yes")
        fragments.append("\n".join(entry))

    return "\n\n".join(fragments)


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    manager = PulseManager()

    try:
        if args.command == "build":
            target = _resolve_target(args.target)
            _compile_target(target, force=args.force)
            print(f"✅ Build pulse complete for {target}.")
            return 0

        if args.command == "pulse":
            status = args.status
            executed = args.execute
            if executed and status == "active":
                status = "executed"
            entry = manager.record_pulse(
                name=args.name,
                priority=args.priority,
                resonance=args.resonance,
                status=status,
                executed=executed,
                notes=args.notes,
            )
            action = "executed" if entry.executed else "recorded"
            print(
                textwrap.dedent(
                    f"""
                    Pulse '{entry.pulse}' {action}.
                    Priority : {entry.priority}
                    Status   : {entry.status}
                    Timestamp: {entry.timestamp}
                    """
                ).strip()
            )
            if entry.resonance:
                print(f"Resonance: {entry.resonance}")
            if entry.notes:
                print(f"Notes    : {entry.notes}")
            return 0

        if args.command == "status":
            output = _render_status(manager, include_history=args.history)
            print(output)
            return 0

        if args.command == "list":
            print(_render_history(manager))
            return 0

        raise PulseError(f"Unknown command: {args.command}")
    except PulseError as exc:
        print(str(exc), file=sys.stderr)
        return 1


__all__ = ["main", "PulseManager", "PulseError", "PulseEntry"]


if __name__ == "__main__":  # pragma: no cover - entry point guard
    raise SystemExit(main())

