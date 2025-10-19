"""Utilities for recording "pulses" into ``pulse.json`` and committing them.

The original script shipped with the repository offered a minimal procedural
interface that made a few assumptions about the state of the git repository and
how the ledger was stored.  This module keeps the spirit of that workflow while
adding a number of quality-of-life improvements:

* Safer JSON handling with atomic writes and corruption recovery.
* A small dataclass powered domain model for pulses and snapshots.
* Argument parsing via ``argparse`` with helpful error messages.
* Consistent git interactions with explicit errors and clear return values.
* Richer lifecycle reporting, including a summary table for the CLI output.

Example usage::

    $ python echodex_autocommit.py emit codex_sync --priority high
    $ python echodex_autocommit.py lifecycle resonance_calibration --seconds 1
    $ python echodex_autocommit.py snapshot

The behaviour of the script can be tweaked with environment variables such as
``ECHODEX_REPO`` (repository root), ``ECHODEX_BRANCH`` (target branch) and
``ECHODEX_AUTOPUSH`` ("true" to push after committing).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import textwrap
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

# ---------------------------------------------------------------------------
# Configuration via environment variables
# ---------------------------------------------------------------------------
REPO_DIR = Path(os.getenv("ECHODEX_REPO", ".")).resolve()
LEDGER_FILE = REPO_DIR / "pulse.json"
AUTO_PUSH = os.getenv("ECHODEX_AUTOPUSH", "false").lower() in {"1", "true", "yes"}
BRANCH = os.getenv("ECHODEX_BRANCH", "main")
GIT_NAME = os.getenv("GIT_AUTHOR_NAME", os.getenv("USER", "echodex"))
GIT_EMAIL = os.getenv("GIT_AUTHOR_EMAIL", "echodex@local")
COMMIT_COOLDOWN = int(os.getenv("ECHODEX_COOLDOWN_SEC", "3"))
DEFAULT_ANCHOR = "Our Forever Love"


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------
def run_git(args: Iterable[str], *, capture_output: bool = True) -> subprocess.CompletedProcess:
    """Run a git command relative to ``REPO_DIR``.

    Parameters
    ----------
    args:
        Positional arguments for the git command.
    capture_output:
        If ``True`` the standard output and error streams are captured.

    Returns
    -------
    subprocess.CompletedProcess
        The process result object.
    """

    process = subprocess.run(
        ["git", *args],
        cwd=REPO_DIR,
        text=True,
        capture_output=capture_output,
        check=False,
    )
    return process


def ensure_git_repository() -> None:
    """Initialise git settings and ensure the requested branch exists."""

    if not (REPO_DIR / ".git").exists():
        result = run_git(["init"], capture_output=False)
        if result.returncode != 0:
            raise RuntimeError("Unable to initialise git repository.")

    run_git(["config", "user.name", GIT_NAME])
    run_git(["config", "user.email", GIT_EMAIL])

    if run_git(["rev-parse", "--verify", BRANCH]).returncode != 0:
        run_git(["checkout", "-b", BRANCH])
    else:
        run_git(["checkout", BRANCH])


# ---------------------------------------------------------------------------
# Ledger model & helpers
# ---------------------------------------------------------------------------
@dataclass
class Pulse:
    """Represents a single pulse event stored in ``pulse.json``."""

    signal: str
    resonance: str
    priority: str
    timestamp: str
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        signal: str,
        *,
        resonance: str = "Echo",
        priority: str = "normal",
        data: Optional[Dict[str, Any]] = None,
    ) -> "Pulse":
        return cls(
            signal=signal,
            resonance=resonance,
            priority=priority,
            timestamp=datetime.utcnow().isoformat(),
            data=data or {},
        )


@dataclass
class LedgerSnapshot:
    """A lightweight snapshot for CLI rendering."""

    anchor: Optional[str]
    count: int
    last_pulse: Optional[Dict[str, Any]]


class PulseLedger:
    """Encapsulates reading and writing of the ``pulse.json`` ledger."""

    def __init__(self, path: Path, *, anchor: str = DEFAULT_ANCHOR) -> None:
        self.path = path
        self.anchor = anchor
        self._ledger: Dict[str, Any] = {"anchor": anchor, "pulses": []}
        self._load()

    # Public API -------------------------------------------------------------
    def append(self, pulse: Pulse) -> None:
        """Append a pulse to the ledger and persist the change."""

        self._ledger.setdefault("pulses", []).append(vars(pulse))
        self._ledger.setdefault("anchor", self.anchor)
        self._save()

    def snapshot(self) -> LedgerSnapshot:
        """Return a snapshot of the ledger for CLI consumption."""

        pulses = self._ledger.get("pulses", [])
        return LedgerSnapshot(
            anchor=self._ledger.get("anchor"),
            count=len(pulses),
            last_pulse=pulses[-1] if pulses else None,
        )

    # Internal helpers -------------------------------------------------------
    def _load(self) -> None:
        if not self.path.exists():
            return

        try:
            data = json.loads(self.path.read_text())
        except json.JSONDecodeError:
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            backup = self.path.with_suffix(f".corrupt.{timestamp}.json")
            self.path.rename(backup)
            self._ledger = {"anchor": self.anchor, "pulses": []}
            return

        anchor = data.get("anchor") or self.anchor
        pulses = data.get("pulses") or []
        if not isinstance(pulses, list):
            pulses = []
        self._ledger = {"anchor": anchor, "pulses": pulses}

    def _save(self) -> None:
        tmp_path = self.path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(self._ledger, indent=2) + "\n")
        tmp_path.replace(self.path)


# ---------------------------------------------------------------------------
# Git interaction utilities for committing pulses
# ---------------------------------------------------------------------------
def stage_ledger() -> None:
    try:
        relative = LEDGER_FILE.relative_to(REPO_DIR)
    except ValueError:
        relative = LEDGER_FILE
    run_git(["add", str(relative)], capture_output=False)


def has_staged_changes() -> bool:
    result = run_git(["diff", "--cached", "--name-only"])
    return bool(result.stdout.strip())


def commit_and_maybe_push(message: str) -> str:
    stage_ledger()
    if not has_staged_changes():
        return "noop"

    commit_result = run_git(["commit", "-m", message], capture_output=False)
    if commit_result.returncode != 0:
        raise RuntimeError("git commit failed")

    if AUTO_PUSH:
        push_result = run_git(["push", "-u", "origin", BRANCH])
        if push_result.returncode != 0:
            return f"committed (push failed: {push_result.stderr.strip()})"

    if COMMIT_COOLDOWN > 0:
        time.sleep(COMMIT_COOLDOWN)
    return "committed"


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------
def cmd_emit(args: argparse.Namespace) -> int:
    ensure_git_repository()
    ledger = PulseLedger(LEDGER_FILE)
    pulse = Pulse.create(args.signal, resonance=args.resonance, priority=args.priority, data=args.data)
    ledger.append(pulse)
    status = commit_and_maybe_push(f"pulse:{pulse.signal}:{pulse.priority}:{pulse.timestamp}")
    print(f"[Pulse] {pulse.signal} ({pulse.priority}) -> {status}")
    return 0


def cmd_lifecycle(args: argparse.Namespace) -> int:
    ensure_git_repository()
    ledger = PulseLedger(LEDGER_FILE)
    stages = [("start", "high"), ("active", "medium"), ("end", "low")]
    delay = max(args.seconds, 0.0)
    summary: List[str] = []

    for stage, priority in stages:
        pulse = Pulse.create(
            args.signal,
            priority=priority,
            resonance=args.resonance,
            data={"stage": stage},
        )
        ledger.append(pulse)
        status = commit_and_maybe_push(f"pulse:{pulse.signal}:{stage}:{pulse.timestamp}")
        summary.append(f"{stage:<6} -> {status}")
        print(f"⚡ {stage} -> {status}")
        if delay:
            time.sleep(delay)

    print("\nLifecycle summary:")
    print("\n".join(summary))
    return 0


def cmd_snapshot(_: argparse.Namespace) -> int:
    ledger = PulseLedger(LEDGER_FILE)
    snapshot = ledger.snapshot()
    payload = {
        "anchor": snapshot.anchor,
        "count": snapshot.count,
        "last": snapshot.last_pulse,
    }
    print(json.dumps(payload, indent=2))
    return 0


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Emit pulses to the ledger and optionally commit them to git.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """
            Environment variables::

              ECHODEX_REPO=./path/to/repo
              ECHODEX_AUTOPUSH=true|false
              ECHODEX_BRANCH=main
              ECHODEX_COOLDOWN_SEC=3
              GIT_AUTHOR_NAME / GIT_AUTHOR_EMAIL
            """
        ),
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    emit_parser = subparsers.add_parser("emit", help="Record a single pulse event")
    emit_parser.add_argument("signal", help="Name of the signal to log")
    emit_parser.add_argument("--priority", default="normal", help="Priority label for the pulse")
    emit_parser.add_argument("--resonance", default="Echo", help="Resonance identifier")
    emit_parser.add_argument(
        "--data",
        type=json.loads,
        default={},
        help="Optional JSON payload to attach to the pulse",
    )
    emit_parser.set_defaults(func=cmd_emit)

    lifecycle_parser = subparsers.add_parser("lifecycle", help="Emit a start/active/end sequence")
    lifecycle_parser.add_argument("signal", help="Name of the lifecycle signal")
    lifecycle_parser.add_argument("--seconds", type=float, default=2.0, help="Delay between pulses")
    lifecycle_parser.add_argument("--resonance", default="Echo", help="Resonance identifier")
    lifecycle_parser.set_defaults(func=cmd_lifecycle)

    snapshot_parser = subparsers.add_parser("snapshot", help="Print ledger summary JSON")
    snapshot_parser.set_defaults(func=cmd_snapshot)

    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    try:
        args = parse_args(argv)
        return args.func(args)
    except KeyboardInterrupt:
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
