"""Fixture loader for Pulse Weaver state."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Mapping

from pulse_weaver.adapters.sqlite import SQLiteAdapter
from pulse_weaver.storage.migrations import apply_migrations

DEFAULT_FIXTURE = Path(__file__).with_name("ledger_default.json")


def _ensure_adapter(db_path: Path) -> SQLiteAdapter:
    adapter = SQLiteAdapter(db_path)
    apply_migrations(adapter)
    return adapter


def load_ledger(db_path: Path, fixture: Path = DEFAULT_FIXTURE) -> Mapping[str, object]:
    adapter = _ensure_adapter(db_path)
    payload = json.loads(fixture.read_text(encoding="utf-8"))

    with adapter.context() as conn:
        conn.execute("DELETE FROM pulse_weaver_links")
        conn.execute("DELETE FROM pulse_weaver_events")

    events = payload.get("events", [])
    with adapter.context() as conn:
        for event in events:
            conn.execute(
                """
                INSERT INTO pulse_weaver_events (cycle, key, status, message, proof, echo, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event["cycle"],
                    event["key"],
                    event["status"],
                    event["message"],
                    event.get("proof"),
                    event.get("echo"),
                    json.dumps(event.get("metadata", {}), sort_keys=True),
                    event.get("created_at"),
                ),
            )

    links = payload.get("links", [])
    with adapter.context() as conn:
        for link in links:
            conn.execute(
                """
                INSERT INTO pulse_weaver_links (key, atlas_node, phantom_trace, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    link["key"],
                    link.get("atlas_node"),
                    link.get("phantom_trace"),
                    link.get("created_at"),
                ),
            )

    return payload


def clear_ledger(db_path: Path) -> None:
    adapter = _ensure_adapter(db_path)
    with adapter.context() as conn:
        conn.execute("DELETE FROM pulse_weaver_links")
        conn.execute("DELETE FROM pulse_weaver_events")


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Seed Pulse Weaver fixtures")
    parser.add_argument("db", type=Path, help="Path to the Pulse Weaver database")
    parser.add_argument(
        "--fixture",
        type=Path,
        default=DEFAULT_FIXTURE,
        help="Fixture JSON to load",
    )
    parser.add_argument("--clear", action="store_true", help="Only clear existing records")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.clear:
        clear_ledger(args.db)
    else:
        load_ledger(args.db, args.fixture)


if __name__ == "__main__":
    main()
