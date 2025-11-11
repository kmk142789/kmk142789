"""Dev orchestration helper for deterministic seeding and teardown."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fixtures.atlas.loader import clear_jobs, load_jobs
from fixtures.federated_pulse.loader import clear_state, load_state
from fixtures.pulse_weaver.loader import clear_ledger, load_ledger

DATA_DIR = REPO_ROOT / "data"
PULSE_DIR = REPO_ROOT / ".fpulse"

SCHEDULER_DB = DATA_DIR / "scheduler.db"
PULSE_WEAVER_DB = DATA_DIR / "pulse_weaver.db"
FEDERATED_PULSE_DB = PULSE_DIR / "pulse.db"


def seed(_: argparse.Namespace) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PULSE_DIR.mkdir(parents=True, exist_ok=True)
    load_jobs(SCHEDULER_DB)
    print(f"Seeded scheduler database at {SCHEDULER_DB}")
    load_ledger(PULSE_WEAVER_DB)
    print(f"Seeded Pulse Weaver ledger at {PULSE_WEAVER_DB}")
    load_state(FEDERATED_PULSE_DB)
    print(f"Seeded federated pulse store at {FEDERATED_PULSE_DB}")


def teardown(_: argparse.Namespace) -> None:
    clear_jobs(SCHEDULER_DB)
    print(f"Cleared scheduler database at {SCHEDULER_DB}")
    clear_ledger(PULSE_WEAVER_DB)
    print(f"Cleared Pulse Weaver ledger at {PULSE_WEAVER_DB}")
    clear_state(FEDERATED_PULSE_DB)
    print(f"Cleared federated pulse store at {FEDERATED_PULSE_DB}")


def replay(args: argparse.Namespace) -> None:
    teardown(args)
    seed(args)


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Dev orchestration helpers")
    subparsers = parser.add_subparsers(dest="command", required=True)

    seed_parser = subparsers.add_parser("seed", help="Seed all dev state deterministically")
    seed_parser.set_defaults(func=seed)

    teardown_parser = subparsers.add_parser("teardown", help="Clear dev state without deleting files")
    teardown_parser.set_defaults(func=teardown)

    replay_parser = subparsers.add_parser("replay", help="Teardown and seed in a single step")
    replay_parser.set_defaults(func=replay)

    args = parser.parse_args(list(argv) if argv is not None else None)
    args.func(args)


if __name__ == "__main__":
    main()
