"""Utilities for running deterministic Echo memory synchronisation passes."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from echo.memory.store import JsonMemoryStore
from echo.sync.cloud import CloudSyncCoordinator, DirectorySyncTransport, SyncReport

__all__ = [
    "EchoSyncConfig",
    "EchoSyncResult",
    "run_echo_sync",
    "main",
]


_DEFAULT_TRANSPORT_DIR = Path(os.environ.get("ECHO_STATE_ROOT", ".echo-runtime/state")) / "cloud-sync"


@dataclass(frozen=True)
class EchoSyncConfig:
    """Configuration describing a single synchronisation pass."""

    node_id: str = "echo-local"
    transport_dir: Path = _DEFAULT_TRANSPORT_DIR
    memory_path: Path | None = None
    log_path: Path | None = None
    include_history: bool = False
    history_limit: int = 5
    note: str | None = None


@dataclass(frozen=True)
class EchoSyncResult:
    """Structured response produced by :func:`run_echo_sync`."""

    report: SyncReport
    history: list[dict[str, object]]

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {"report": asdict(self.report)}
        if self.history:
            payload["history"] = self.history
        return payload


def _ensure_history_limit(limit: int) -> int:
    if limit <= 0:
        raise ValueError("history_limit must be positive")
    return limit


def _record_probe(store: JsonMemoryStore, *, note: str | None) -> None:
    """Record a minimal execution session so sync operations have context."""

    with store.session(metadata={"source": "echo_sync", "note": note} if note else {"source": "echo_sync"}) as session:
        session.record_command("echo_sync.run")
        if note:
            session.set_summary(note)
        session.set_artifact(None)


def run_echo_sync(config: EchoSyncConfig) -> EchoSyncResult:
    """Execute a single synchronisation pass and return the resulting summary."""

    history_limit = _ensure_history_limit(config.history_limit)

    store = JsonMemoryStore(storage_path=config.memory_path, log_path=config.log_path)
    transport = DirectorySyncTransport(config.transport_dir)
    _record_probe(store, note=config.note)

    coordinator = CloudSyncCoordinator(config.node_id, store, transport)
    report = coordinator.sync()

    history: list[dict[str, object]] = []
    if config.include_history:
        history = [context.to_dict() for context in store.recent_executions(limit=history_limit)]

    return EchoSyncResult(report=report, history=history)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Synchronise Echo memory replicas using a directory transport.")
    parser.add_argument("--node-id", default="echo-local", help="Identifier recorded for this sync participant.")
    parser.add_argument(
        "--transport-dir",
        type=Path,
        default=_DEFAULT_TRANSPORT_DIR,
        help="Directory where CRDT payloads are exchanged between peers.",
    )
    parser.add_argument(
        "--memory-path",
        type=Path,
        help="Optional explicit path for the JsonMemoryStore payload.",
    )
    parser.add_argument(
        "--log-path",
        type=Path,
        help="Optional explicit path for the Echo execution log.",
    )
    parser.add_argument(
        "--include-history",
        action="store_true",
        help="Include recent execution contexts in the output payload.",
    )
    parser.add_argument(
        "--history-limit",
        type=int,
        default=5,
        help="Number of execution contexts to include when --include-history is supplied (default: 5).",
    )
    parser.add_argument("--note", help="Optional note recorded alongside the generated execution context.")
    parser.add_argument("--json", action="store_true", help="Emit the result as JSON.")
    return parser


def _format_summary(result: EchoSyncResult, *, include_history: bool) -> str:
    lines = [
        f"Applied contexts: {result.report.applied_contexts}",
        f"Known contexts: {result.report.known_contexts}",
        f"Sources contacted: {result.report.sources_contacted}",
    ]
    if include_history and result.history:
        lines.append("Recent contexts:")
        for entry in result.history:
            lines.append(f"  - {entry.get('timestamp', 'unknown')} :: {entry.get('summary', 'no summary')}")
    return "\n".join(lines)


def main(argv: Iterable[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        config = EchoSyncConfig(
            node_id=args.node_id,
            transport_dir=args.transport_dir,
            memory_path=args.memory_path,
            log_path=args.log_path,
            include_history=args.include_history,
            history_limit=args.history_limit,
            note=args.note,
        )
        result = run_echo_sync(config)
    except ValueError as exc:
        parser.error(str(exc))
        raise SystemExit(2)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(_format_summary(result, include_history=args.include_history))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
