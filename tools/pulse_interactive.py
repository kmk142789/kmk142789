"""Interactive interface for exploring Echo pulse history.

This module provides a small text based user interface that makes it easy to
inspect the signals recorded in ``pulse_history.json``.  The repository already
ships with :mod:`tools.pulse_continuity_audit`, which can calculate statistics
about the recorded pulses.  The interactive shell introduced here builds on top
of that logic and exposes practical commands for browsing recent events,
searching by keyword, and reviewing the cadence of individual pulse channels.

The shell is intentionally lightweight and only relies on the Python standard
library, making it available in the same environments that already support the
existing tooling.
"""

from __future__ import annotations

import argparse
import cmd
import shlex
import textwrap
from collections import Counter
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from .pulse_continuity_audit import (
    DEFAULT_HISTORY_PATH,
    DEFAULT_PULSE_PATH,
    PulseEvent,
    audit_pulse_history,
    load_pulse_history,
    load_pulse_metadata,
)


def abbreviate_hash(value: str, length: int = 12) -> str:
    """Return a shortened representation of ``value``.

    The history file stores full SHA-256 hashes, which makes the rendered table
    difficult to read in a terminal.  Showing the first ``length`` characters
    gives readers enough entropy to recognise the event while keeping the UI
    compact.
    """

    if length < 4:
        raise ValueError("hash abbreviation length must be at least 4 characters")
    if len(value) <= length:
        return value
    return f"{value[:length]}…"


def format_event(event: PulseEvent) -> str:
    """Return a human friendly rendering of ``event``."""

    timestamp = event.moment.isoformat()
    return f"{timestamp} | {event.message} | {abbreviate_hash(event.hash)}"


class PulseSession:
    """Utility object that manages pulse data for the interactive shell."""

    def __init__(self, events: Iterable[PulseEvent], metadata: Optional[dict] = None):
        self._events: List[PulseEvent] = sorted(list(events), key=lambda event: event.timestamp)
        self.metadata = metadata or {}
        self.history_path: Optional[Path] = None
        self.pulse_path: Optional[Path] = None

    @classmethod
    def from_files(
        cls,
        history_path: Path = DEFAULT_HISTORY_PATH,
        pulse_path: Path = DEFAULT_PULSE_PATH,
    ) -> "PulseSession":
        events = load_pulse_history(history_path)
        metadata = load_pulse_metadata(pulse_path)
        session = cls(events, metadata)
        session.history_path = history_path
        session.pulse_path = pulse_path
        return session

    def reload(self) -> None:
        """Reload pulse information from disk.

        ``PulseSession`` instances created with :meth:`from_files` remember the
        source paths, allowing the interactive shell to refresh its state while
        it is running.  Manual instances without backing files raise a clear
        error to avoid accidentally hiding stale data in tests.
        """

        if self.history_path is None or self.pulse_path is None:
            raise RuntimeError("session was not initialised from file paths")
        events = load_pulse_history(self.history_path)
        metadata = load_pulse_metadata(self.pulse_path)
        self._events = sorted(events, key=lambda event: event.timestamp)
        self.metadata = metadata or {}

    @property
    def events(self) -> Sequence[PulseEvent]:
        return tuple(self._events)

    def summary_text(self, *, threshold_hours: Optional[float] = None) -> str:
        report = audit_pulse_history(self._events, self.metadata, threshold_hours=threshold_hours)
        return report.render_text()

    def latest_events(self, limit: Optional[int] = None) -> List[PulseEvent]:
        ordered = list(reversed(self._events))
        if limit is not None:
            ordered = ordered[:limit]
        return ordered

    def search(self, keyword: str, *, limit: Optional[int] = None) -> List[PulseEvent]:
        keyword_lower = keyword.casefold()
        matches = [event for event in reversed(self._events) if keyword_lower in event.message.casefold()]
        if limit is not None:
            matches = matches[:limit]
        return matches

    def by_prefix(self, prefix: str, *, limit: Optional[int] = None) -> List[PulseEvent]:
        prefix_lower = prefix.casefold()
        matches: List[PulseEvent] = []
        for event in reversed(self._events):
            channel = event.message.split(":", 1)[0].strip()
            if channel.casefold() == prefix_lower:
                matches.append(event)
        if limit is not None:
            matches = matches[:limit]
        return matches

    def prefix_counts(self) -> List[Tuple[str, int]]:
        counter: Counter[str] = Counter()
        for event in self._events:
            channel = event.message.split(":", 1)[0].strip()
            counter[channel] += 1
        return sorted(counter.items(), key=lambda item: (-item[1], item[0]))


def _parse_limit(argument: Optional[str], default: int) -> int:
    if argument is None:
        return default
    text = argument.strip()
    if not text:
        return default
    value = int(text)
    if value <= 0:
        raise ValueError("limit must be greater than zero")
    return value


class PulseShell(cmd.Cmd):
    intro = textwrap.dedent(
        """
        Echo Pulse Interactive Shell
        ---------------------------------
        Commands:
          summary [hours]   Show the cadence report (optional threshold override)
          recent [limit]    Display the most recent pulse emissions
          find <keyword>    Search events whose message contains <keyword>
          prefix <name>     Show the most recent events for a channel prefix
          counts            Summarise how many pulses each prefix emitted
          metadata          Display metadata stored in pulse.json
          reload            Refresh the session from disk
          threshold [hours] Inspect or update the alert threshold
          exit/quit         Leave the shell
        """
    ).strip()

    prompt = "pulse> "

    def __init__(self, session: PulseSession, *, threshold_hours: Optional[float]):
        super().__init__()
        self.session = session
        self.threshold_hours = threshold_hours

    # -- Utility -----------------------------------------------------------------
    def _print_events(self, events: Sequence[PulseEvent]) -> None:
        if not events:
            print("No pulse events found.")
            return
        for event in events:
            print(format_event(event))

    # -- Commands -----------------------------------------------------------------
    def do_summary(self, arg: str) -> None:
        argument = arg.strip()
        threshold = self.threshold_hours
        if argument:
            try:
                threshold = float(argument)
            except ValueError:
                print("Threshold must be a number of hours (e.g. 'summary 6').")
                return
        print(self.session.summary_text(threshold_hours=threshold))

    def do_recent(self, arg: str) -> None:
        try:
            limit = _parse_limit(arg, default=10)
        except ValueError as exc:
            print(exc)
            return
        self._print_events(self.session.latest_events(limit))

    def do_find(self, arg: str) -> None:
        if not arg.strip():
            print("Usage: find <keyword> [limit]")
            return
        parts = shlex.split(arg)
        keyword = parts[0]
        limit: Optional[int]
        try:
            limit = _parse_limit(parts[1], default=10) if len(parts) > 1 else 10
        except ValueError as exc:
            print(exc)
            return
        self._print_events(self.session.search(keyword, limit=limit))

    def do_prefix(self, arg: str) -> None:
        if not arg.strip():
            print("Usage: prefix <name> [limit]")
            return
        parts = shlex.split(arg)
        prefix = parts[0]
        try:
            limit = _parse_limit(parts[1], default=10) if len(parts) > 1 else 10
        except ValueError as exc:
            print(exc)
            return
        self._print_events(self.session.by_prefix(prefix, limit=limit))

    def do_counts(self, arg: str) -> None:  # pylint: disable=unused-argument
        counts = self.session.prefix_counts()
        if not counts:
            print("No pulse events found.")
            return
        width = max(len(prefix) for prefix, _ in counts)
        for prefix, total in counts:
            print(f"{prefix.ljust(width)} : {total}")

    def do_metadata(self, arg: str) -> None:  # pylint: disable=unused-argument
        if not self.session.metadata:
            print("No metadata available.")
            return
        for key, value in self.session.metadata.items():
            print(f"{key}: {value}")

    def do_reload(self, arg: str) -> None:  # pylint: disable=unused-argument
        try:
            self.session.reload()
        except Exception as exc:  # pragma: no cover - interactive convenience
            print(f"Unable to reload session: {exc}")
        else:
            print("Session reloaded from disk.")

    def do_threshold(self, arg: str) -> None:
        argument = arg.strip()
        if not argument:
            if self.threshold_hours is None:
                print("No threshold configured.")
            else:
                print(f"Current threshold: {self.threshold_hours:.2f} hours")
            return
        try:
            self.threshold_hours = float(argument)
        except ValueError:
            print("Threshold must be a numeric value representing hours.")
            return
        print(f"Threshold updated to {self.threshold_hours:.2f} hours.")

    def do_exit(self, arg: str) -> bool:  # pylint: disable=unused-argument
        print("Goodbye.")
        return True

    def do_quit(self, arg: str) -> bool:  # pylint: disable=unused-argument
        return self.do_exit(arg)

    def default(self, line: str) -> None:
        print(f"Unknown command: {line!r}. Type 'help' to list available actions.")


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--history",
        type=Path,
        default=DEFAULT_HISTORY_PATH,
        help="Path to pulse_history.json (default: repository root)",
    )
    parser.add_argument(
        "--pulse",
        type=Path,
        default=DEFAULT_PULSE_PATH,
        help="Path to pulse.json metadata file (default: repository root)",
    )
    parser.add_argument(
        "--threshold-hours",
        type=float,
        default=None,
        help="Optional alert threshold used in the summary report",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    namespace = _build_arg_parser().parse_args(argv)
    session = PulseSession.from_files(namespace.history, namespace.pulse)
    shell = PulseShell(session, threshold_hours=namespace.threshold_hours)
    try:
        shell.cmdloop()
    except KeyboardInterrupt:  # pragma: no cover - interactive convenience
        print("\nInterrupted.")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
