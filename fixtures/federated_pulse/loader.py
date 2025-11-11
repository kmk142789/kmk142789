"""Seed helpers for the Federated Pulse CRDT store."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Iterable, List

from federated_pulse.storage.migrations import apply_migrations

DEFAULT_FIXTURE = Path(__file__).with_name("lww_default.json")


def _normalize_value(value: object) -> object:
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return value


def load_state(db_path: Path, fixture: Path = DEFAULT_FIXTURE) -> List[dict[str, object]]:
    """Load fixture data into the federated pulse database."""

    apply_migrations(db_path)
    records = json.loads(fixture.read_text(encoding="utf-8"))
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM lww")
        for entry in records:
            conn.execute(
                "REPLACE INTO lww(k, v, ts, node) VALUES(?, ?, ?, ?)",
                (
                    entry["key"],
                    _normalize_value(entry["value"]),
                    int(entry["timestamp"]),
                    entry["node"],
                ),
            )
        conn.commit()
    return [dict(entry) for entry in records]


def clear_state(db_path: Path) -> None:
    if not db_path.exists():
        return
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM lww")
        conn.commit()


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Seed Federated Pulse fixtures")
    parser.add_argument("db", type=Path, help="Path to the pulse database")
    parser.add_argument(
        "--fixture",
        type=Path,
        default=DEFAULT_FIXTURE,
        help="Fixture JSON to load",
    )
    parser.add_argument("--clear", action="store_true", help="Only clear the table")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.clear:
        clear_state(args.db)
    else:
        load_state(args.db, args.fixture)


if __name__ == "__main__":
    main()
